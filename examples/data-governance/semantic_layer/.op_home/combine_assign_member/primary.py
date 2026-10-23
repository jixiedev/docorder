"""Merge per-model member assignments into one JSON document."""

from __future__ import annotations

import json

from docorder.functions.reduce_function import ReduceFunction
from docorder.utils.errors import FatalError


class CombineAssignMember(ReduceFunction):
    def transform_data(self, sources, target):
        if not sources:
            raise FatalError(f"{self.operator_name}: no model assignments")
        models = []
        for source in sorted(sources, key=lambda item: item.name):
            try:
                payload = json.loads(source.read_text())
            except json.JSONDecodeError as exc:
                raise FatalError(f"{self.operator_name}:{source.name}: invalid JSON: {exc}") from exc
            if not isinstance(payload, dict) or "model" not in payload or "metrics" not in payload:
                raise FatalError(
                    f"{self.operator_name}:{source.name}: JSON is missing model or metrics"
                )
            models.append(payload)
        target.staging_data = json.dumps(
            {"models": models},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"

    def transform_props(self, sources, target):
        target.tag = {"models": len(sources)}
