"""Send the upstream prompt to the LLM. The runner fingerprints the files it writes."""

from __future__ import annotations

from pathlib import Path

from docorder.core.entity import Entity
from docorder.functions.map_function import MapFunction
from docorder.utils.errors import DocorderError, FatalError
from docorder.utils.llm_tool import LLMTool


class GenerateModel(MapFunction):
    def transform_data(self, source_entity: Entity, target_entity: Entity) -> None:
        self._staging().mkdir(parents=True, exist_ok=True)
        tool = LLMTool.resolve(self.environment.operator_props, self.artifact)
        tool.complete(source_entity.read_text(), self._workspace())
        self._model_files(source_entity.name)

    def transform_props(self, source_entity: Entity, target_entity: Entity) -> None:
        sql, yml = self._model_files(source_entity.name)
        tag = source_entity.carried_tag()
        target_entity.tag = {
            "database": tag.get("database"),
            "table": tag.get("table"),
            "documentation": tag.get("documentation"),
            "sql": str(sql),
            "yml": str(yml),
        }

    def _workspace(self) -> Path:
        raw = self.environment.operator_props.get("workspace")
        if not isinstance(raw, str) or not raw:
            raise FatalError(f"{self.operator_name}: workspace must be a non-empty string")
        path = Path(raw)
        if not path.is_dir():
            raise FatalError(f"{self.operator_name}: workspace is not a directory: {path}")
        return path

    def _staging(self) -> Path:
        raw = self.environment.operator_props.get("staging")
        if not isinstance(raw, str) or not raw:
            raise FatalError(f"{self.operator_name}: staging must be a non-empty string")
        return Path(raw)

    def _model_files(self, name: str) -> tuple[Path, Path]:
        staging = self._staging()
        sql = (staging / f"{name}.sql").resolve()
        yml = (staging / f"{name}.yml").resolve()
        missing = [str(path) for path in (sql, yml) if not path.is_file()]
        if missing:
            listed = ", ".join(missing)
            raise DocorderError(f"{self.operator_name}:{name}: model files were not written: {listed}")
        return sql, yml
