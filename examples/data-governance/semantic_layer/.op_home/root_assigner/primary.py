"""One LLM call per model. The body is that model's assignment JSON."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

from docorder.functions.impl.template_to_llm import complete_prompt
from docorder.functions.map_function import MapFunction
from docorder.utils.errors import FatalError

CATALOG_HEADER = "root_id|root_zh|kind|definition|not_a|aliases"
CATALOG_NAME = "final_root.csv"
CONFIDENCE = frozenset({"high", "med", "low"})


class RootAssigner(MapFunction):
    def transform_data(self, source_entity, target_entity):
        document = _inventory()(source_entity.tag, self.operator_name, source_entity.name)
        if not document["metrics"]:
            raise FatalError(f"{self.operator_name}:{source_entity.name}: yml has no metrics")
        catalog_path = self.operator.run_context.job.staging_path / CATALOG_NAME
        allowed = {row["root_id"] for row in read_catalog(catalog_path, self.operator_name)}
        allowed.add("unassigned")
        reply = complete_prompt(self, source=source_entity, target=target_entity)
        chosen = assignment_rows(reply, self.operator_name, source_entity.name)
        target_entity.staging_data = json.dumps(
            {
                "metrics": _merge_metrics(
                    document["metrics"], chosen, allowed, self.operator_name, source_entity.name
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


def read_catalog(path: Path, owner: str) -> list[dict[str, str]]:
    if not path.is_file():
        raise FatalError(f"{owner}: missing {path}")
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines or lines[0] != CATALOG_HEADER:
        raise FatalError(f"{owner}: {path} has no {CATALOG_HEADER} header")
    fields = CATALOG_HEADER.split("|")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        parts = line.split("|")
        if len(parts) != len(fields):
            raise FatalError(f"{owner}: catalog row has {len(parts)} fields: {line}")
        rows.append(dict(zip(fields, parts)))
    if not rows:
        raise FatalError(f"{owner}: {path} has no roots")
    return rows


def assignment_rows(text: str, owner: str, name: str) -> list[dict]:
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


def _merge_metrics(inventory: list[dict], chosen: list[dict], allowed: set[str], owner: str, name: str):
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
    for item in inventory:
        row = by_metric.pop(item["metric"], None)
        if row is None:
            raise FatalError(f"{owner}:{name}: response missing metric {item['metric']}")
        root_id = row.get("root_id")
        confidence = row.get("confidence")
        evidence = row.get("evidence")
        if root_id not in allowed:
            raise FatalError(f"{owner}:{name}: root_id {root_id!r} is not in the catalog")
        if confidence not in CONFIDENCE:
            raise FatalError(f"{owner}:{name}: confidence {confidence!r} is not high, med, or low")
        if not isinstance(evidence, str) or not evidence.strip():
            raise FatalError(f"{owner}:{name}: evidence is empty")
        merged.append(
            {
                "agg": item["agg"],
                "confidence": confidence,
                "evidence": evidence.strip(),
                "kind": item["kind"],
                "metric": item["metric"],
                "metric_description": item["metric_description"],
                "root_id": root_id,
            }
        )
    if by_metric:
        extra = ", ".join(sorted(by_metric))
        raise FatalError(f"{owner}:{name}: response has metrics that are not in the yml: {extra}")
    return merged


def _inventory():
    path = Path(__file__).resolve().parents[1] / "librarian" / "primary.py"
    spec = importlib.util.spec_from_file_location("semantic_librarian_inventory", path)
    if spec is None or spec.loader is None:
        raise FatalError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.inventory
