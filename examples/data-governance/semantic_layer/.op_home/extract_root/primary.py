"""Split the assignment document into one entity per root, skipping unassigned."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from docorder.functions.fanout_function import FanoutFunction
from docorder.utils.errors import FatalError

CATALOG_NAME = "final_root.csv"


class ExtractRoot(FanoutFunction):
    def output_names(self, source_entity):
        payload = _document(source_entity.read_text(), self.operator_name, source_entity.name)
        names: set[str] = set()
        for model in payload["models"]:
            for metric in model["metrics"]:
                root_id = metric.get("root_id")
                if isinstance(root_id, str) and root_id and root_id != "unassigned":
                    names.add(root_id)
        return sorted(names)

    def transform_data(self, source_entity, target_entity):
        payload = _document(source_entity.read_text(), self.operator_name, source_entity.name)
        root_id = target_entity.name
        catalog = _read_catalog()(
            self.operator.run_context.job.staging_path / CATALOG_NAME,
            self.operator_name,
        )
        row = next((item for item in catalog if item["root_id"] == root_id), None)
        if row is None:
            raise FatalError(f"{self.operator_name}:{root_id}: root is not in {CATALOG_NAME}")
        metrics = []
        for model in payload["models"]:
            for metric in model["metrics"]:
                if metric.get("root_id") != root_id:
                    continue
                metrics.append(
                    {
                        "agg": metric.get("agg"),
                        "confidence": metric.get("confidence"),
                        "evidence": metric.get("evidence"),
                        "kind": metric.get("kind"),
                        "metric": metric.get("metric"),
                        "metric_description": metric.get("metric_description"),
                        "model": model.get("model"),
                        "model_description": model.get("model_description"),
                    }
                )
        metrics.sort(key=lambda item: (str(item["model"]), str(item["metric"])))
        target_entity.staging_data = json.dumps(
            {
                "aliases": row["aliases"],
                "definition": row["definition"],
                "kind": row["kind"],
                "metrics": metrics,
                "not_a": row["not_a"],
                "root_id": root_id,
                "root_zh": row["root_zh"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"

    def transform_props(self, source_entity, target_entity):
        del source_entity
        target_entity.tag = {"root_id": target_entity.name}


def _document(text: str, owner: str, name: str) -> dict:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FatalError(f"{owner}:{name}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        raise FatalError(f"{owner}:{name}: assignment JSON needs a models list")
    return payload


def _read_catalog():
    path = Path(__file__).resolve().parents[1] / "root_assigner" / "primary.py"
    spec = importlib.util.spec_from_file_location("semantic_root_assigner_catalog", path)
    if spec is None or spec.loader is None:
        raise FatalError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.read_catalog
