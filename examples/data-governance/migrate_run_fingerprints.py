"""Rewrite local ``runs/`` entity trees to match the unified ``fingerprint`` scheme.

Does not invoke LLMs or re-run jobs. Updates ``data`` / ``tag.json``, then
refreshes ``upstream`` hashes in topological order.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from docorder.core.entity import content_digest  # noqa: E402
from docorder.core.external_hash import (  # noqa: E402
    DEPEND,
    FINGERPRINT_KEY,
    RECORD,
    file_hashes,
    placeholder_values,
    spec,
)

SEMANTIC_ROOT = Path(__file__).resolve().parent / "semantic_layer"
RUNS = SEMANTIC_ROOT / "runs"
INPUT = SEMANTIC_ROOT / ".input"
EPOCH = "demo"
DEFAULT_MODEL_HOME = "/Users/jixie/wbox/data-governance/semantic_layer/models/hive"

OPERATOR_ORDER = (
    "source",
    "source_assign",
    "source_member",
    "librarian",
    "optimizer_root",
    "root_assigner",
    "assign_member",
    "taxonomist_root",
    "reduce_assigner",
    "combine_assign_member",
    "merge_root",
    "extract_root",
    "taxonomist_member",
    "combine_root_member",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _input_body(name: str) -> str:
    body = (INPUT / name / "data").read_text(encoding="utf-8")
    if body and not body.endswith("\n"):
        body += "\n"
    return body


def _write_entity(entity_dir: Path, data: str, tag: dict[str, Any]) -> None:
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / "data").write_text(data, encoding="utf-8")
    (entity_dir / "tag.json").write_text(
        json.dumps(tag, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _hash_section(
    templates: tuple[str, ...],
    entity_name: str,
    staging: Path,
    job_root: Path,
    props: dict[str, Any],
    tag: dict[str, Any] | None,
    owner: str,
) -> dict[str, str]:
    if not templates:
        return {}
    values = placeholder_values(entity_name, str(staging), props, tag)
    return file_hashes(templates, values, job_root, owner)


def _model_home() -> str:
    import os

    return os.environ.get("SEMANTIC_LAYER_MODELS", DEFAULT_MODEL_HOME)


def _staging(job_root: Path) -> Path:
    return job_root / ".staging"


def migrate_source(entity_dir: Path, name: str, job_root: Path, props: dict[str, Any]) -> None:
    tag = _read_json(entity_dir / "tag.json")
    body = _input_body(name)
    record = _hash_section(
        spec(props, "source").record,
        name,
        _staging(job_root),
        job_root,
        props,
        tag,
        f"source:{name}",
    )
    tag[FINGERPRINT_KEY] = {RECORD: record}
    tag.pop("external-hash", None)
    _write_entity(entity_dir, body, tag)


def migrate_source_assign(entity_dir: Path, name: str, job_root: Path, props: dict[str, Any]) -> None:
    tag = _read_json(entity_dir / "tag.json")
    body = _input_body(name)
    tag.pop("catalog", None)
    record = _hash_section(
        spec(props, "source_assign").record,
        name,
        _staging(job_root),
        job_root,
        props,
        tag,
        f"source_assign:{name}",
    )
    tag[FINGERPRINT_KEY] = {RECORD: record}
    _write_entity(entity_dir, body, tag)


def migrate_source_member(entity_dir: Path, name: str, job_root: Path, props: dict[str, Any]) -> None:
    tag = _read_json(entity_dir / "tag.json")
    body = _input_body(name)
    tag.pop("root_assign", None)
    tag.pop("root_member", None)
    record = _hash_section(
        spec(props, "source_member").record,
        name,
        _staging(job_root),
        job_root,
        props,
        tag,
        f"source_member:{name}",
    )
    tag[FINGERPRINT_KEY] = {RECORD: record}
    _write_entity(entity_dir, body, tag)


def migrate_optimizer(entity_dir: Path, name: str, job_root: Path, props: dict[str, Any]) -> None:
    tag = _read_json(entity_dir / "tag.json")
    fp = spec(props, "optimizer_root")
    record = _hash_section(
        fp.record,
        name,
        _staging(job_root),
        job_root,
        props,
        tag,
        f"optimizer_root:{name}",
    )
    depend = _hash_section(
        fp.depend,
        name,
        _staging(job_root),
        job_root,
        props,
        None,
        f"optimizer_root:{name}",
    )
    tag[FINGERPRINT_KEY] = {}
    if record:
        tag[FINGERPRINT_KEY][RECORD] = record
    if depend:
        tag[FINGERPRINT_KEY][DEPEND] = depend
    _write_entity(entity_dir, "\n", tag)


def migrate_root_assigner(entity_dir: Path, name: str, job_root: Path, props: dict[str, Any]) -> None:
    tag = _read_json(entity_dir / "tag.json")
    tag.pop("catalog", None)
    depend = _hash_section(
        spec(props, "root_assigner").depend,
        name,
        _staging(job_root),
        job_root,
        props,
        None,
        f"root_assigner:{name}",
    )
    if depend:
        tag[FINGERPRINT_KEY] = {DEPEND: depend}
    else:
        tag.pop(FINGERPRINT_KEY, None)
    data = (entity_dir / "data").read_text(encoding="utf-8")
    _write_entity(entity_dir, data, tag)


def migrate_assign_member(entity_dir: Path, name: str, job_root: Path, props: dict[str, Any]) -> None:
    tag = _read_json(entity_dir / "tag.json")
    tag.pop("root_assign", None)
    tag.pop("root_member", None)
    depend = _hash_section(
        spec(props, "assign_member").depend,
        name,
        _staging(job_root),
        job_root,
        props,
        None,
        f"assign_member:{name}",
    )
    if depend:
        tag[FINGERPRINT_KEY] = {DEPEND: depend}
    else:
        tag.pop(FINGERPRINT_KEY, None)
    data = (entity_dir / "data").read_text(encoding="utf-8")
    _write_entity(entity_dir, data, tag)


def migrate_merge_root(entity_dir: Path, name: str, job_root: Path, props: dict[str, Any]) -> None:
    tag = _read_json(entity_dir / "tag.json")
    depend = _hash_section(
        spec(props, "merge_root").depend,
        name,
        _staging(job_root),
        job_root,
        props,
        None,
        f"merge_root:{name}",
    )
    if depend:
        existing = tag.get(FINGERPRINT_KEY)
        if isinstance(existing, dict):
            existing = dict(existing)
            existing[DEPEND] = depend
            tag[FINGERPRINT_KEY] = existing
        else:
            tag[FINGERPRINT_KEY] = {DEPEND: depend}
    data = (entity_dir / "data").read_text(encoding="utf-8")
    _write_entity(entity_dir, data, tag)


def migrate_extract_root(entity_dir: Path, name: str, job_root: Path, props: dict[str, Any]) -> None:
    tag = _read_json(entity_dir / "tag.json")
    depend = _hash_section(
        spec(props, "extract_root").depend,
        name,
        _staging(job_root),
        job_root,
        props,
        None,
        f"extract_root:{name}",
    )
    if depend:
        tag[FINGERPRINT_KEY] = {DEPEND: depend}
    data = (entity_dir / "data").read_text(encoding="utf-8")
    _write_entity(entity_dir, data, tag)


def migrate_reduce_assigner(entity_dir: Path) -> None:
    tag = _read_json(entity_dir / "tag.json")
    tag.pop("catalog", None)
    data = (entity_dir / "data").read_text(encoding="utf-8")
    _write_entity(entity_dir, data, tag)


def _load_props(home_name: str) -> dict[str, Any]:
    path = SEMANTIC_ROOT / ".op_home" / home_name / "props.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if k not in ("type", "class")}


def _job_props_for_source_assign(job_root: Path) -> dict[str, Any]:
    props = _load_props("source")
    catalog = str(_staging(job_root) / "final_root.csv")
    props = dict(props)
    props["catalog"] = catalog
    props[FINGERPRINT_KEY] = {
        RECORD: {
            "{model_home}/{db}/{table}.sql": "",
            "{model_home}/{db}/{table}.yml": "",
            "{catalog}": "",
        }
    }
    props["model_home"] = _model_home()
    return props


def _job_props_for_source_member(job_root: Path) -> dict[str, Any]:
    props = _load_props("source_member")
    staging = _staging(job_root)
    props = dict(props)
    props["model_home"] = _model_home()
    props["root_assign"] = str(staging / "root_assign.json")
    props["root_member"] = str(staging / "root_member.csv")
    return props


def _job_props_for_source(job_root: Path) -> dict[str, Any]:
    props = _load_props("source")
    props = dict(props)
    props["model_home"] = _model_home()
    return props


def refresh_upstream(entity_dir: Path, name: str, job_root: Path) -> None:
    tag = _read_json(entity_dir / "tag.json")
    raw = tag.get("upstream")
    if raw is None:
        return
    records = [raw] if isinstance(raw, dict) else raw
    updated: list[dict[str, str]] = []
    for record in records:
        op = record["operator"]
        upstream_name = record["name"]
        upstream_dir = job_root / op / EPOCH / upstream_name
        upstream_tag = _read_json(upstream_dir / "tag.json")
        upstream_data = (upstream_dir / "data").read_text(encoding="utf-8")
        digest = content_digest(upstream_data, upstream_tag)
        updated.append(
            {
                "operator": op,
                "name": upstream_name,
                "epoch": record["epoch"],
                "hash": digest,
            }
        )
    tag["upstream"] = updated[0] if len(updated) == 1 else updated
    data = (entity_dir / "data").read_text(encoding="utf-8")
    _write_entity(entity_dir, data, tag)


def migrate_semantic_runs(job_root: Path) -> None:
    source_props = _job_props_for_source(job_root)
    source_assign_props = _job_props_for_source_assign(job_root)
    source_member_props = _job_props_for_source_member(job_root)
    optimizer_props = _load_props("optimizer_root")
    root_assigner_props = _load_props("root_assigner")
    assign_member_props = _load_props("assign_member")
    merge_props = _load_props("merge_root")
    extract_props = _load_props("extract_root")

    for op in ("source", "source_assign", "source_member"):
        epoch_dir = job_root / op / EPOCH
        if not epoch_dir.is_dir():
            continue
        for entity_dir in sorted(epoch_dir.iterdir()):
            if not entity_dir.is_dir():
                continue
            name = entity_dir.name
            if op == "source":
                migrate_source(entity_dir, name, job_root, source_props)
            elif op == "source_assign":
                migrate_source_assign(entity_dir, name, job_root, source_assign_props)
            else:
                migrate_source_member(entity_dir, name, job_root, source_member_props)

    for name in ("optimizer_root",):
        epoch_dir = job_root / name / EPOCH
        if epoch_dir.is_dir():
            for entity_dir in sorted(epoch_dir.iterdir()):
                if entity_dir.is_dir():
                    migrate_optimizer(entity_dir, entity_dir.name, job_root, optimizer_props)

    for name, migrator, props in (
        ("root_assigner", migrate_root_assigner, root_assigner_props),
        ("assign_member", migrate_assign_member, assign_member_props),
    ):
        epoch_dir = job_root / name / EPOCH
        if epoch_dir.is_dir():
            for entity_dir in sorted(epoch_dir.iterdir()):
                if entity_dir.is_dir():
                    migrator(entity_dir, entity_dir.name, job_root, props)

    merge_epoch = job_root / "merge_root" / EPOCH
    if merge_epoch.is_dir():
        for entity_dir in sorted(merge_epoch.iterdir()):
            if entity_dir.is_dir():
                migrate_merge_root(entity_dir, entity_dir.name, job_root, merge_props)

    reduce_epoch = job_root / "reduce_assigner" / EPOCH
    if reduce_epoch.is_dir():
        for entity_dir in sorted(reduce_epoch.iterdir()):
            if entity_dir.is_dir():
                migrate_reduce_assigner(entity_dir)

    extract_epoch = job_root / "extract_root" / EPOCH
    if extract_epoch.is_dir():
        for entity_dir in sorted(extract_epoch.iterdir()):
            if entity_dir.is_dir():
                migrate_extract_root(entity_dir, entity_dir.name, job_root, extract_props)

    for op in OPERATOR_ORDER:
        epoch_dir = job_root / op / EPOCH
        if not epoch_dir.is_dir():
            continue
        for entity_dir in sorted(epoch_dir.iterdir()):
            if entity_dir.is_dir():
                refresh_upstream(entity_dir, entity_dir.name, job_root)


def main() -> None:
    if not RUNS.is_dir():
        print(f"no runs directory at {RUNS}", file=sys.stderr)
        sys.exit(1)
    migrate_semantic_runs(RUNS)
    print(f"migrated {RUNS}")


if __name__ == "__main__":
    main()
