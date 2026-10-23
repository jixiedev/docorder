"""One LLM call per model: assign each metric to a member under its root."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

from docorder.functions.impl.template_to_llm import complete_prompt
from docorder.functions.map_function import MapFunction
from docorder.utils.errors import FatalError

ASSIGN_NAME = "root_assign.json"
MEMBER_NAME = "root_member.csv"
MEMBER_HEADER = (
    "root_id|member_id|member_zh|definition|is_default|scope_filter|time_basis|attribution|aliases"
)
CONFIDENCE = frozenset({"high", "med", "low"})


class AssignMember(MapFunction):
    def transform_data(self, source_entity, target_entity):
        tag = source_entity.tag
        staging = self.operator.run_context.job.staging_path
        assign_path = staging / ASSIGN_NAME
        member_path = staging / MEMBER_NAME
        document = _inventory()(tag, self.operator_name, source_entity.name)
        if not document["metrics"]:
            raise FatalError(f"{self.operator_name}:{source_entity.name}: yml has no metrics")
        assigned = _model_roots(assign_path, document["model"], self.operator_name, source_entity.name)
        members_by_root = _members_by_root(member_path, self.operator_name)
        reply = complete_prompt(self, source=source_entity, target=target_entity)
        chosen = _member_rows(reply, self.operator_name, source_entity.name)
        target_entity.staging_data = json.dumps(
            {
                "metrics": _merge_members(
                    document,
                    assigned,
                    chosen,
                    members_by_root,
                    self.operator_name,
                    source_entity.name,
                ),
                "model": document["model"],
                "model_description": document["model_description"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"

    def transform_props(self, source_entity, target_entity):
        tag = source_entity.tag
        target_entity.tag = {
            "db": tag.get("db"),
            "model": tag.get("table"),
            "table": tag.get("table"),
            "yml": tag.get("yml"),
        }


def _model_roots(path: Path, model: str, owner: str, name: str) -> dict:
    if not path.is_file():
        raise FatalError(f"{owner}:{name}: missing {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FatalError(f"{owner}:{name}: invalid {path.name}: {exc}") from exc
    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        raise FatalError(f"{owner}:{name}: {path.name} needs a models list")
    for item in models:
        if isinstance(item, dict) and item.get("model") == model:
            metrics = item.get("metrics")
            if not isinstance(metrics, list):
                raise FatalError(f"{owner}:{name}: model {model} has no metrics list")
            return item
    raise FatalError(f"{owner}:{name}: model {model} is not in {path.name}")


def _members_by_root(path: Path, owner: str) -> dict[str, list[dict[str, str]]]:
    rows = read_member_csv(path, owner)
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["root_id"], []).append(row)
    return grouped


def read_member_csv(path: Path, owner: str) -> list[dict[str, str]]:
    if not path.is_file():
        raise FatalError(f"{owner}: missing {path}")
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines or lines[0] != MEMBER_HEADER:
        raise FatalError(f"{owner}: {path} has no {MEMBER_HEADER} header")
    fields = MEMBER_HEADER.split("|")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        parts = line.split("|")
        if len(parts) != len(fields):
            raise FatalError(f"{owner}: member row has {len(parts)} fields: {line}")
        rows.append(dict(zip(fields, parts)))
    return rows


def _member_rows(text: str, owner: str, name: str) -> list[dict]:
    fenced = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    body = fenced.group(1) if fenced else text
    start = body.find("{")
    end = body.rfind("}")
    if start < 0 or end <= start:
        raise FatalError(f"{owner}:{name}: response has no JSON object")
    try:
        payload = json.loads(body[start : end + 1])
    except json.JSONDecodeError as exc:
        raise FatalError(f"{owner}:{name}: response JSON is invalid: {exc}") from exc
    metrics = payload.get("metrics") if isinstance(payload, dict) else None
    if not isinstance(metrics, list):
        raise FatalError(f"{owner}:{name}: response JSON needs a metrics list")
    return metrics


def _merge_members(
    document: dict,
    assigned: dict,
    chosen: list[dict],
    members_by_root: dict[str, list[dict[str, str]]],
    owner: str,
    name: str,
) -> list[dict]:
    root_by_metric = {row["metric"]: row for row in assigned["metrics"]}
    by_metric: dict[str, dict] = {}
    for row in chosen:
        if not isinstance(row, dict):
            raise FatalError(f"{owner}:{name}: metric row is not an object")
        metric = row.get("metric")
        if not isinstance(metric, str) or not metric:
            raise FatalError(f"{owner}:{name}: metric name is missing")
        if metric in by_metric:
            raise FatalError(f"{owner}:{name}: duplicate metric {metric}")
        by_metric[metric] = row

    merged = []
    for item in document["metrics"]:
        metric = item["metric"]
        root_row = root_by_metric.get(metric)
        if root_row is None:
            raise FatalError(f"{owner}:{name}: root_assign missing metric {metric}")
        row = by_metric.pop(metric, None)
        if row is None:
            raise FatalError(f"{owner}:{name}: response missing metric {metric}")
        root_id = root_row.get("root_id")
        if not isinstance(root_id, str) or not root_id:
            raise FatalError(f"{owner}:{name}: root_id missing for {metric}")
        member_id = row.get("member_id")
        confidence = row.get("confidence")
        evidence = row.get("evidence")
        related = row.get("related_ratio")
        if root_id == "unassigned":
            if member_id != "unassigned":
                raise FatalError(f"{owner}:{name}: unassigned root needs member_id unassigned")
            ratio = _ratio(related, owner, name, metric)
        else:
            allowed = {m["member_id"] for m in members_by_root.get(root_id, [])}
            if member_id not in allowed:
                raise FatalError(
                    f"{owner}:{name}: member_id {member_id!r} is not listed for root {root_id}"
                )
            ratio = _ratio(related, owner, name, metric)
        if confidence not in CONFIDENCE:
            raise FatalError(f"{owner}:{name}: confidence {confidence!r} is not high, med, or low")
        if not isinstance(evidence, str) or not evidence.strip():
            raise FatalError(f"{owner}:{name}: evidence is empty for {metric}")
        merged.append(
            {
                "agg": item["agg"],
                "confidence": confidence,
                "evidence": evidence.strip(),
                "kind": item["kind"],
                "member_id": member_id,
                "metric": metric,
                "metric_description": item["metric_description"],
                "related_ratio": ratio,
                "root_id": root_id,
            }
        )
    if by_metric:
        extra = ", ".join(sorted(by_metric))
        raise FatalError(f"{owner}:{name}: response has metrics that are not in the yml: {extra}")
    return merged


def _ratio(value, owner: str, name: str, metric: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FatalError(f"{owner}:{name}: related_ratio for {metric} must be a number")
    number = float(value)
    if number < 0 or number > 1:
        raise FatalError(f"{owner}:{name}: related_ratio for {metric} must be between 0 and 1")
    return number


def _inventory():
    path = Path(__file__).resolve().parents[1] / "librarian" / "primary.py"
    spec = importlib.util.spec_from_file_location("semantic_librarian_inventory", path)
    if spec is None or spec.loader is None:
        raise FatalError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.inventory
