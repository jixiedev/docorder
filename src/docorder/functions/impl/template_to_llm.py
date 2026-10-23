"""Render a Jinja prompt that names files, then call the LLM.

``TemplateToLLM`` is the reduce: one call for the whole upstream list.
``EntityTemplateToLLM`` is the map: one call per upstream entity.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import jinja2

from docorder.core.entity import Entity
from docorder.core.environment import Environment
from docorder.functions.map_function import MapFunction
from docorder.functions.reduce_function import ReduceFunction
from docorder.utils.errors import FatalError
from docorder.utils.llm_tool import LLMTool


class TemplateToLLM(ReduceFunction):
    """Render a Jinja template over every upstream entity, then call the LLM.

    ``template`` is a path relative to the operator home. A trailing newline
    in that file is kept. The template sees ``sources``, a list of objects
    with ``name``, ``path``, and ``tag``, in the order the reduce receives
    them. ``path`` is that entity's ``data`` file. ``staging(name)`` is the
    path of one file in the job ``.staging`` directory. ``name`` is one file
    name, and the file must already exist. The template does not receive
    file contents. ``operator`` and ``job`` are the same view a map template
    reads.

    ``header``, when set, keeps the reply from that line onward and drops one
    surrounding fence. Without it, the body is the reply.

    ``tag_template`` is an optional Jinja string. It renders a JSON object,
    and that object is the entity tag. Without it, the tag is empty.

    ``min_sources`` and ``max_sources`` bound the upstream list. Omit either
    bound to leave that side open.

    ``workspace`` and ``tool`` mean the same as they do for ``PromptToLLM``.
    """

    def transform_data(self, sources: list[Entity], target: Entity) -> None:
        body, _tag = self._outcome(sources, target)
        target.staging_data = body

    def transform_props(self, sources: list[Entity], target: Entity) -> None:
        _body, tag = self._outcome(sources, target)
        target.tag = tag

    def _outcome(self, sources: list[Entity], target: Entity) -> tuple[str, dict[str, Any]]:
        cached = getattr(self, "_cache", None)
        key = (tuple(source.name for source in sources), target.name)
        if cached is None or cached[0] != key:
            cached = (key, self._run(sources, target))
            self._cache = cached
        return cached[1]

    def _run(self, sources: list[Entity], target: Entity) -> tuple[str, dict[str, Any]]:
        values = prompt_values(self, sources=sources, target=target)
        prompt = render_template(self, _template_text(self), values, target.name)
        tool = LLMTool.resolve(self.environment.operator_props, self.artifact)
        reply = tool.complete(prompt, workspace(self))
        header = self.environment.operator_props.get("header")
        body = reply
        return body, render_tag(self, values, target.name)


def prompt_values(
    function,
    *,
    source: Entity | None = None,
    sources: list[Entity] | None = None,
    target: Entity | None = None,
) -> dict[str, Any]:
    values = Environment(function.operator, target).template_env
    if sources is not None:
        values["sources"] = [_source_view(item) for item in sources]
    if source is not None:
        values["source"] = _source_view(source)
    values["staging"] = lambda name: staging_file(function, name)
    return values


def render_template(function, template: str, values: dict[str, Any], name: str) -> str:
    jinja_env = jinja2.Environment(
        undefined=jinja2.StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    try:
        return jinja_env.from_string(template).render(**values)
    except jinja2.TemplateError as exc:
        raise FatalError(f"{function.operator_name}:{name}: template failed: {exc}") from exc


def render_tag(function, values: dict[str, Any], name: str) -> dict[str, Any]:
    template = function.environment.operator_props.get("tag_template")
    if template is None:
        return {}
    if not isinstance(template, str) or not template:
        raise FatalError(f"{function.operator_name}: tag_template must be a non-empty string")
    rendered = render_template(function, template, values, name)
    try:
        payload = json.loads(rendered)
    except json.JSONDecodeError as exc:
        raise FatalError(f"{function.operator_name}:{name}: tag_template is not JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise FatalError(f"{function.operator_name}:{name}: tag_template must render a JSON object")
    return payload


def workspace(function) -> Path:
    raw = function.environment.operator_props.get("workspace")
    if not isinstance(raw, str) or not raw:
        raise FatalError(f"{function.operator_name}: workspace must be a non-empty string")
    path = Path(raw)
    if not path.is_dir():
        raise FatalError(f"{function.operator_name}: workspace is not a directory: {path}")
    return path


def staging_file(function, name: str) -> str:
    if (
        not isinstance(name, str)
        or not name
        or name != name.strip()
        or "/" in name
        or "\\" in name
        or name in {".", ".."}
    ):
        raise FatalError(f"{function.operator_name}: staging file name must be one file name, got {name!r}")
    path = function.operator.run_context.job.staging_path / name
    if not path.is_file():
        raise FatalError(f"{function.operator_name}: missing {path}")
    return str(path)


def complete_prompt(
    function,
    *,
    source: Entity | None = None,
    sources: list[Entity] | None = None,
    target: Entity | None = None,
) -> str:
    """Render this operator's template and return the LLM reply."""
    name = source.name if source is not None else target.name if target is not None else function.operator_name
    values = prompt_values(function, source=source, sources=sources, target=target)
    prompt = render_template(function, _template_text(function), values, name)
    tool = LLMTool.resolve(function.environment.operator_props, function.artifact)
    return tool.complete(prompt, workspace(function))


def _source_view(source: Entity) -> dict[str, Any]:
    return {"name": source.name, "path": str(source.data_path), "tag": source.tag}


def _template_text(function) -> str:
    relative = function.environment.operator_props.get("template")
    if not isinstance(relative, str) or not relative:
        raise FatalError(f"{function.operator_name}: template must be a non-empty string")
    return function.artifact.read_text(relative)


class EntityTemplateToLLM(MapFunction):
    """Render a Jinja template for one upstream entity, then call the LLM.

    The template sees ``source`` with ``name``, ``path``, and ``tag``.
    ``path`` is that entity's ``data`` file. ``staging(name)`` is the path of
    one file in the job ``.staging`` directory. The template does not receive
    file contents. ``header``, ``tag_template``, ``workspace``, and ``tool``
    mean the same as they do for ``TemplateToLLM``.
    """

    def transform_data(self, source_entity: Entity, target_entity: Entity) -> None:
        body, _tag = self._outcome(source_entity, target_entity)
        target_entity.staging_data = body

    def transform_props(self, source_entity: Entity, target_entity: Entity) -> None:
        _body, tag = self._outcome(source_entity, target_entity)
        target_entity.tag = tag

    def _outcome(self, source_entity: Entity, target_entity: Entity) -> tuple[str, dict[str, Any]]:
        cached = getattr(self, "_cache", None)
        key = (source_entity.name, target_entity.name)
        if cached is None or cached[0] != key:
            cached = (key, self._run(source_entity, target_entity))
            self._cache = cached
        return cached[1]

    def _run(self, source_entity: Entity, target_entity: Entity) -> tuple[str, dict[str, Any]]:
        values = prompt_values(self, source=source_entity, target=target_entity)
        prompt = render_template(self, _template_text(self), values, source_entity.name)
        tool = LLMTool.resolve(self.environment.operator_props, self.artifact)
        reply = tool.complete(prompt, workspace(self))
        header = self.environment.operator_props.get("header")
        body = reply
        return body, render_tag(self, values, source_entity.name)


def _header(function, raw: Any) -> str:
    if not isinstance(raw, str) or not raw:
        raise FatalError(f"{function.operator_name}: header must be a non-empty string")
    return raw

