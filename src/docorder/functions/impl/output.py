"""Apply function: publish each upstream entity as a file under the job staging directory."""

from __future__ import annotations

import json
from pathlib import Path

from docorder.core.entity import Entity
from docorder.functions.apply_function import ApplyFunction
from docorder.utils.errors import FatalError


class Output(ApplyFunction):
    """Write each upstream entity body as one file under the job staging directory.

    This is an apply function. The operator that runs it is an apply operator.

    Config key ``directory`` selects another destination. A relative path is
    resolved from the operator home. When it is omitted, files go to
    ``.staging`` under the job root.

    ``rename`` chooses the file name. The default is the entity name.
    ``filename`` sets one fixed name for every entity. A subclass overrides
    ``rename`` when the name depends on the entity. The name must be one file
    name. Two entities that produce the same name fail with ``FatalError``.

    ``apply`` writes that entity's file. ``finish`` removes files this node
    published earlier and no longer produces.
    """

    _PUBLISHED_FILE = ".published-files"

    def rename(self, entity: Entity) -> str:
        """File name for one upstream entity.

        ``filename`` is a fixed name. Without it, the entity name is used.
        Subclasses override this method when the name depends on the entity.
        """
        raw = self.environment.operator_props.get("filename")
        if raw is None:
            return entity.name
        if not isinstance(raw, str) or not raw:
            raise FatalError(f"{self.operator_name}: filename must be a non-empty string")
        return raw

    def apply(self, entity: Entity) -> None:
        planned = self._plan()
        directory = self._staging_dir()
        directory.mkdir(parents=True, exist_ok=True)
        _write_result(directory / planned[entity.name], entity.read_text())

    def finish(self) -> None:
        planned = set(self._plan().values())
        directory = self._staging_dir()
        directory.mkdir(parents=True, exist_ok=True)
        for name in self._load_published() - planned:
            path = directory / name
            if path.is_file():
                path.unlink()
        self._save_published(planned)

    def _plan(self) -> dict[str, str]:
        store = self.operator.upstream_store
        if store is None:
            raise FatalError(f"{self.operator_name} needs an upstream")
        planned: dict[str, str] = {}
        owners: dict[str, str] = {}
        for name in sorted(store.entities):
            entity = store.entities[name]
            file_name = self._file_name(entity)
            if file_name in owners:
                raise FatalError(
                    f"{self.operator_name}: duplicate staging file name {file_name!r}"
                )
            owners[file_name] = name
            planned[name] = file_name
        return planned

    def _staging_dir(self) -> Path:
        raw = self.environment.operator_props.get("directory")
        if raw is None:
            return self.operator.run_context.job.staging_path
        if not isinstance(raw, str) or not raw:
            raise FatalError(f"{self.operator_name}: directory must be a non-empty string")
        path = Path(raw)
        if not path.is_absolute():
            path = self.operator.operator_home / path
        return path.resolve()

    def _file_name(self, entity: Entity) -> str:
        name = self.rename(entity)
        if not _staging_name_ok(name):
            raise FatalError(
                f"{self.operator_name}:{entity.name}: staging file name must be one file name, got {name!r}"
            )
        return name

    def _published_path(self) -> Path:
        return self.operator.output_path / self._PUBLISHED_FILE

    def _load_published(self) -> set[str]:
        path = self._published_path()
        if not path.is_file():
            return set()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return set()
        if not isinstance(payload, list) or not all(isinstance(item, str) for item in payload):
            return set()
        return set(payload)

    def _save_published(self, names: set[str]) -> None:
        path = self._published_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(sorted(names), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def _staging_name_ok(name: object) -> bool:
    """True when ``name`` is one file name under the staging directory."""
    return (
        isinstance(name, str)
        and bool(name)
        and name == name.strip()
        and "/" not in name
        and "\\" not in name
        and name not in {".", ".."}
    )


def _write_result(path: Path, text: str) -> None:
    Entity._atomic_text(path, text)
