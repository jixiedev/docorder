"""One JSON document per dbt model, with a metric list and a rule-derived kind."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from docorder.functions.map_function import MapFunction
from docorder.utils.errors import FatalError


class Librarian(MapFunction):
    def transform_data(self, source_entity, target_entity):
        document = inventory(source_entity.tag, self.operator_name, source_entity.name)
        target_entity.staging_data = json.dumps(document, ensure_ascii=False, indent=2) + "\n"

    def transform_props(self, source_entity, target_entity):
        tag = source_entity.tag
        target_entity.tag = {
            "db": tag.get("db"),
            "table": tag.get("table"),
            "sql": tag.get("sql"),
            "yml": tag.get("yml"),
            "model": tag.get("table"),
        }


def inventory(tag: dict, owner: str, name: str) -> dict:
    raw = tag.get("yml")
    if not isinstance(raw, str) or not raw:
        raise FatalError(f"{owner}:{name}: tag missing yml")
    path = Path(raw)
    if not path.is_file():
        raise FatalError(f"{owner}:{name}: yml is not a file: {path}")
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise FatalError(f"{owner}:{name}: invalid yml: {exc}") from exc
    models = (loaded or {}).get("models") or []
    if not models:
        raise FatalError(f"{owner}:{name}: yml has no models")
    model = models[0]
    model_name = model.get("name") or tag.get("table") or name
    description = str(model.get("description") or "").strip()
    metrics = []
    for metric in model.get("metrics") or []:
        metric_name = metric.get("name")
        metric_description = str(metric.get("description") or "").strip()
        if not metric_name or not metric_description:
            continue
        agg = str(metric.get("agg") or "")
        metric_type = str(metric.get("type") or "")
        metrics.append(
            {
                "metric": metric_name,
                "metric_description": metric_description,
                "agg": agg,
                "metric_type": metric_type,
                "kind": infer_kind(metric_name, metric_description, agg, metric_type),
            }
        )
    return {
        "model": model_name,
        "model_description": description,
        "db": tag.get("db"),
        "table": tag.get("table"),
        "sql": tag.get("sql"),
        "yml": str(path),
        "metrics": metrics,
    }


def infer_kind(metric: str, description: str, agg: str, metric_type: str) -> str:
    name = metric.lower()
    desc = description.lower()
    agg_l = agg.lower()
    mtype = metric_type.lower()
    text = f"{name} {desc}"

    if mtype == "ratio" or re.search(r"(^|_)(rate|roas|ctr|cvr|margin|ratio)(_|$)", name):
        if re.search(r"conversion_rate|fx|exchange|ex_rate|currency", text) and "checkout" not in name:
            return "rate"
        if "roas" in name or "ctr" in name or "cvr" in name or "_rate" in name or mtype == "ratio":
            return "rate"
    if re.search(r"(^|_)nps($|_)|csat|wish_score|quality_score|rating", name) or "nps" in desc:
        return "score"
    if re.search(
        r"(_days|_hours|_seconds|duration|ttd|time_to|lag_days|hours_to|sla)",
        name,
    ) or re.search(r"time to deliver|hours to first reply|fulfillment time", desc):
        if not re.search(r"gmv|revenue|spend", name):
            return "duration"
    if agg_l in {"count", "count_distinct", "sum_boolean"} or mtype == "count":
        return "count"
    if agg_l in {"sum", "average"} or mtype in {"simple", "cumulative"}:
        if re.search(r"(_rate|_roas|_ctr|_cvr|_per_)", name):
            return "rate"
        return "amount"
    if re.search(r"distinct|count|buyers|orders|impressions|clicks", name) and agg_l != "sum":
        return "count"
    return "unknown"
