"""Turn a directory of entity directories into source entities."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from docorder.core.entity import DATA_FILE, TAG_FILE, entity_name_ok
from docorder.functions.source_function import SourceFunction, SourceRecord
from docorder.utils.errors import FatalError


class DirectorySource(SourceFunction):
    """Turn a directory of entity directories into entities.

    Config key ``directory`` is that directory. A relative path is resolved
    from the operator home. ``generate`` yields one record per direct child
    that is an entity: a directory holding ``data`` and ``tag.json``. The
    entity name is the directory name. ``extract_tag`` may amend the loaded
    tag; the default keeps ``tag.json`` as it is.
    """

    def emit(self) -> Iterable[SourceRecord]:
        yield from self.generate(self.directory())

    def directory(self) -> Path:
        raw = self.environment.operator_props.get("directory")
        if not isinstance(raw, str) or not raw:
            raise FatalError("directory source config missing directory")
        path = Path(raw)
        if not path.is_absolute():
            path = self.artifact.home / path
        path = path.resolve()
        if not path.is_dir():
            raise FatalError(f"directory source path is not a directory: {path}")
        return path

    def generate(self, directory: Path) -> Iterable[SourceRecord]:
        """Yield one entity per entity directory directly under ``directory``.

        A child is an entity when it is a directory whose name is one visible
        segment and which holds both ``data`` and ``tag.json``. Files, nested
        deeper paths, and incomplete directories are skipped.
        """
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if not path.is_dir() or not entity_name_ok(path.name):
                continue
            data_path = path / DATA_FILE
            tag_path = path / TAG_FILE
            if not data_path.is_file() or not tag_path.is_file():
                continue
            if not self.include(path):
                continue
            try:
                text = data_path.read_text(encoding="utf-8")
            except (OSError, ValueError) as exc:
                raise FatalError(f"{path.name} data: {exc}") from exc
            tag = self.extract_tag(path.name, text, self._read_tag(path.name, tag_path))
            if not isinstance(tag, dict):
                raise FatalError(f"{path.name}: extract_tag must return a dict")
            yield SourceRecord(path.name, text, tag)

    def include(self, path: Path) -> bool:
        """Whether this entity directory is emitted. The default accepts every entity."""
        return True

    def extract_tag(self, name: str, content: str, tag: dict[str, Any]) -> dict[str, Any]:
        """Tag for one entity directory.

        ``name`` is the directory name. ``content`` is the ``data`` text.
        ``tag`` is the object loaded from ``tag.json``. The default returns
        that object unchanged.
        """
        return tag

    def _read_tag(self, name: str, path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise FatalError(f"{name} tag.json: {exc}") from exc
        if not isinstance(payload, dict):
            raise FatalError(f"{name} tag.json is not an object")
        return payload


class FilteredDirectorySource(DirectorySource):
    """A directory source that keeps entity directories selected by ``config["filter"]``.

    ``disabled_suffix`` drops a directory when its name ends with one of those
    suffixes. Without ``enabled_suffix``, every remaining entity is kept.
    With it, only names ending in one of those suffixes are kept. ``min_size``
    and ``max_size`` are inclusive byte bounds on the ``data`` file. A suffix
    value is one string or a list of strings.
    """

    def include(self, path: Path) -> bool:
        spec = self.filter_spec()
        name = path.name
        if self.matches_suffix(name, spec["disabled_suffix"]):
            return False
        enabled = spec["enabled_suffix"]
        if enabled is not None and not self.matches_suffix(name, enabled):
            return False
        size = (path / DATA_FILE).stat().st_size
        minimum = spec["min_size"]
        maximum = spec["max_size"]
        if minimum is not None and size < minimum:
            return False
        if maximum is not None and size > maximum:
            return False
        return True

    def filter_spec(self) -> dict[str, Any]:
        raw = self.environment.operator_props.get("filter")
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise FatalError(f"{self.operator_name}: filter must be an object")
        enabled = self.suffixes(raw, "enabled_suffix")
        disabled = self.suffixes(raw, "disabled_suffix") or ()
        minimum = self.size_bound(raw, "min_size")
        maximum = self.size_bound(raw, "max_size")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise FatalError(f"{self.operator_name}: filter min_size is greater than max_size")
        return {
            "enabled_suffix": enabled,
            "disabled_suffix": disabled,
            "min_size": minimum,
            "max_size": maximum,
        }

    def suffixes(self, raw: dict[str, Any], key: str) -> tuple[str, ...] | None:
        """Return suffixes for ``key``. Missing means the rule is not set."""
        if key not in raw or raw[key] is None:
            return None
        value = raw[key]
        if isinstance(value, str):
            items = [value]
        elif isinstance(value, list):
            items = value
        else:
            raise FatalError(f"{self.operator_name}: filter {key} must be a string or a list")
        suffixes: list[str] = []
        for item in items:
            if not isinstance(item, str) or not item:
                raise FatalError(f"{self.operator_name}: filter {key} contains an empty suffix")
            suffixes.append(item)
        return tuple(suffixes)

    def size_bound(self, raw: dict[str, Any], key: str) -> int | None:
        if key not in raw or raw[key] is None:
            return None
        value = raw[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise FatalError(f"{self.operator_name}: filter {key} must be a non-negative integer")
        return value

    @staticmethod
    def matches_suffix(name: str, suffixes: tuple[str, ...]) -> bool:
        return any(name.endswith(suffix) for suffix in suffixes)


_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


class FileHashSource(DirectorySource):
    """One entity per input directory. The body stays the input ``data`` text.

    ``paths`` is an object of tag field to path template. The resolved absolute
    path is written into the tag. The tag loaded from ``tag.json`` is kept.
    File hashes belong in the operator's ``fingerprint.record``, which the
    runner writes. This function does not hash files.

    A template uses ``{name}`` placeholders. String fields in the entity tag and
    string values in the operator props fill them. A prop overrides a tag field
    of the same name. A relative path is resolved from the operator home.
    """

    def emit(self) -> Iterable[SourceRecord]:
        path_templates = self._mapping("paths")
        for record in self.generate(self.directory()):
            values = self._values(record.tag)
            tag = dict(record.tag)
            for key, template in path_templates.items():
                tag[key] = str(self._resolve(self._render(template, values, record.name), record.name))
            yield SourceRecord(record.name, record.data, tag)

    def _mapping(self, key: str) -> dict[str, str]:
        raw = self.environment.operator_props.get(key)
        if raw is None:
            return {}
        if not isinstance(raw, dict):
            raise FatalError(f"{self.operator_name}: {key} must be an object")
        mapping: dict[str, str] = {}
        for name, template in raw.items():
            if not isinstance(name, str) or not name or not isinstance(template, str) or not template:
                raise FatalError(f"{self.operator_name}: {key} entries must be non-empty strings")
            mapping[name] = template
        return mapping

    def _values(self, tag: dict[str, Any]) -> dict[str, str]:
        values = {key: value for key, value in tag.items() if isinstance(value, str)}
        for key, value in self.environment.operator_props.items():
            if isinstance(value, str) and value:
                values[key] = value
        return values

    def _render(self, template: str, values: dict[str, str], name: str) -> str:
        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            if key not in values:
                raise FatalError(f"{self.operator_name}:{name}: placeholder {{{key}}} has no value")
            return values[key]

        return _PLACEHOLDER.sub(replace, template)

    def _resolve(self, raw: str, name: str) -> Path:
        path = Path(raw)
        if not path.is_absolute():
            path = self.artifact.home / path
        path = path.resolve()
        if not path.is_file():
            raise FatalError(f"{self.operator_name}:{name}: missing file {path}")
        return path
