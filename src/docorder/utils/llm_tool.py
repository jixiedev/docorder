"""Command-line LLM tools. A preset is a JSON file in the operator home."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docorder.core.artifact import Artifact
from docorder.utils.errors import DocorderError, FatalError


@dataclass(frozen=True)
class LLMTool:
    """One command-line tool that turns a prompt into text on stdout.

    ``name`` is only used in error messages. ``run`` is the argv, and each
    argument may contain the literal ``{workspace}``, replaced with the
    workspace path before the process starts. ``prompt`` is ``stdin`` or
    ``arg``. ``stdin`` writes the prompt to the process standard input.
    ``arg`` appends the prompt as the final argument and passes no input.

    ``resolve`` picks the definition in this order:

    1. ``config["tool"]``, which is the function's ``tool`` parameter.
    2. The ``DOCORDER_LLM`` environment variable, when ``tool`` is missing
       or empty.

    A string looks first for ``tools/<name>.json`` inside the operator home,
    then for that string as a filesystem path. A mapping is an inline tool
    object and does not touch the home. Anything else, or a name that
    matches neither place, raises ``FatalError``.

    The JSON object needs a non-empty ``run`` list of strings. ``prompt``
    defaults to ``stdin``. ``name`` defaults to the preset name, the file
    stem, or ``custom`` for an inline object. A missing executable is
    ``FatalError``. A non-zero exit is ``DocorderError``, so the operator
    retry policy still applies. Standard output is the completion.
    """

    name: str
    run: tuple[str, ...]
    prompt: str

    @classmethod
    def resolve(cls, config: dict[str, Any], artifact: Artifact) -> LLMTool:
        """Select a tool from config, ``DOCORDER_LLM``, or ``tools/<name>.json``."""
        spec = config.get("tool")
        if spec is None or spec == "":
            spec = os.environ.get("DOCORDER_LLM", "").strip() or None
        if not spec:
            raise FatalError(
                "llm config missing tool. Set tool to a home preset, a JSON file path, or a tool object."
            )
        if isinstance(spec, str):
            relative = f"tools/{spec}.json"
            if artifact.exists(relative):
                return cls.from_text(artifact.read_text(relative), relative, default_name=spec)
            path = Path(spec).expanduser()
            if path.is_file():
                return cls.from_text(path.read_text(encoding="utf-8"), str(path), default_name=path.stem)
            raise FatalError(
                f"unknown llm tool {spec!r}. Looked for {relative} in {artifact.home}, then {path}."
            )
        if isinstance(spec, dict):
            return cls.from_mapping(spec, default_name="custom")
        raise FatalError("llm tool must be a preset name, a JSON file path, or an object")

    def complete(self, prompt: str, workspace: Path) -> str:
        """Run the tool on ``prompt`` and return its standard output.

        ``{workspace}`` in ``run`` is replaced with ``workspace``. The
        process working directory is that same path.
        """
        argv = [arg.replace("{workspace}", str(workspace)) for arg in self.run]
        if self.prompt == "arg":
            argv.append(prompt)
            prompt_input = None
        else:
            prompt_input = prompt
        completed = self.run_process(argv, prompt=prompt_input, cwd=workspace)
        return completed.stdout

    @classmethod
    def from_text(cls, text: str, label: str, *, default_name: str) -> LLMTool:
        """Parse a tool JSON document. ``label`` names the file in errors."""
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise FatalError(f"llm tool file is not JSON: {label}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise FatalError(f"llm tool file must contain an object: {label}")
        return cls.from_mapping(loaded, default_name=default_name)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any], *, default_name: str) -> LLMTool:
        """Build a tool from ``run``, optional ``prompt``, and optional ``name``."""
        run = raw.get("run")
        if not isinstance(run, list) or not run or not all(isinstance(item, str) for item in run):
            raise FatalError(f"llm tool {default_name} needs a non-empty run argv")
        prompt = str(raw.get("prompt", "stdin"))
        if prompt not in {"stdin", "arg"}:
            raise FatalError(f"llm tool {default_name} prompt must be stdin or arg")
        return cls(
            name=str(raw.get("name") or default_name),
            run=tuple(run),
            prompt=prompt,
        )

    def run_process(
        self,
        argv: list[str],
        *,
        prompt: str | None,
        cwd: Path | None,
    ) -> subprocess.CompletedProcess[str]:
        """Run ``argv``. ``prompt`` is the standard input, or ``None`` when unused.

        A missing executable is ``FatalError``. A non-zero status is
        ``DocorderError`` and includes the tail of stderr, or stdout when
        stderr is empty.
        """
        try:
            completed = subprocess.run(
                argv,
                input=prompt,
                check=False,
                capture_output=True,
                text=True,
                cwd=cwd,
            )
        except FileNotFoundError as exc:
            raise FatalError(f"{self.name} executable is not on PATH: {argv[0]}") from exc
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise DocorderError(f"{self.name} exited {completed.returncode}: {detail[-4000:]}")
        return completed
