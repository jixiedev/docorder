"""File fingerprints declared on an operator and stored on its entity tag.

``props.json`` ``fingerprint`` has two objects. ``record`` lists files this
operator writes or a source points at. ``depend`` lists files it reads that no
upstream entity carries. Keys are path templates. Values in the config are
ignored. The entity tag stores the same keys with the sha256 of each file.

``depend`` is compared before a map, reduce, or fanout runs, and updated after
a successful write. ``record`` is written after the entity is filled and is not
a reason to redo that entity.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docorder.utils.errors import FatalError

FINGERPRINT_KEY = "fingerprint"
RECORD = "record"
DEPEND = "depend"
_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass(frozen=True)
class FingerprintSpec:
    """Templates declared for one operator. Empty tuples mean that side is absent."""

    record: tuple[str, ...]
    depend: tuple[str, ...]


def spec(props: dict[str, Any], owner: str) -> FingerprintSpec:
    """Read ``fingerprint`` from operator props. Absent means both sides are empty."""
    raw = props.get(FINGERPRINT_KEY)
    if raw is None:
        return FingerprintSpec((), ())
    if not isinstance(raw, dict):
        raise FatalError(f"{owner}: fingerprint must be an object")
    return FingerprintSpec(
        _templates(raw.get(RECORD), owner, RECORD),
        _templates(raw.get(DEPEND), owner, DEPEND),
    )


def placeholder_values(
    entity_name: str,
    staging: str,
    props: dict[str, Any],
    tag: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Values that fill a template.

    ``name`` is the entity and wins over props and tag. String props override
    string tag fields. ``staging`` defaults to the job staging directory.
    """
    values = {"name": entity_name, "staging": staging}
    if tag:
        for key, value in tag.items():
            if isinstance(value, str) and value:
                values[key] = value
    for key, value in props.items():
        if key == "name" or not isinstance(value, str) or not value:
            continue
        values[key] = value
    values["name"] = entity_name
    return values


def file_hashes(
    declared: tuple[str, ...],
    values: dict[str, str],
    root: Path,
    owner: str,
) -> dict[str, str]:
    """Sha256 of each rendered file. The dict key is the template, not the path."""
    hashes: dict[str, str] = {}
    for template in declared:
        path = render_path(template, values, root, owner)
        if not path.is_file():
            raise FatalError(f"{owner}: missing external file {path}")
        hashes[template] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def render_path(template: str, values: dict[str, str], root: Path, owner: str) -> Path:
    """Render ``template`` and resolve a relative result against ``root``."""

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise FatalError(f"{owner}: placeholder {{{key}}} has no value")
        return values[key]

    rendered = _PLACEHOLDER.sub(replace, template)
    path = Path(rendered)
    if not path.is_absolute():
        path = root / path
    return path


def matches(stored: Any, current: dict[str, str]) -> bool:
    """True when ``stored`` is the template-to-hash object ``current`` describes."""
    if not current:
        return True
    if not isinstance(stored, dict) or set(stored) != set(current):
        return False
    return all(stored.get(template) == digest for template, digest in current.items())


def _templates(raw: Any, owner: str, section: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, dict):
        raise FatalError(f"{owner}: fingerprint.{section} must be an object")
    found: list[str] = []
    for key in raw:
        if not isinstance(key, str) or not key:
            raise FatalError(f"{owner}: fingerprint.{section} keys must be non-empty templates")
        found.append(key)
    return tuple(found)
