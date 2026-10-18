"""How many entities one operator run added, modified, or deleted."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Protocol


class _Census(Protocol):
    def census(self) -> Mapping[str, str]: ...

_HEADERS = ("operator", "added", "modified", "rewritten", "deleted")
_ALIGN_RIGHT = (False, True, True, True, True)


class EpochEntityDiff:
    """Change across one operator run.

    Construct this before the operator prepares its outputs, and call
    ``finish`` after ``execute`` returns. The source is whatever ``census``
    reports: epoch entities for a transform, or published result files for
    output. Added names are new, deleted names are gone, and modified names
    kept the same name but changed their content hash. Rewritten names were
    written again and kept that hash. An entity hash is the body plus the user
    tag, so a rewrite that only replaces the upstream snapshot is rewritten,
    not modified. Pass the names this run wrote to ``finish``.
    """

    added: frozenset[str]
    modified: frozenset[str]
    rewritten: frozenset[str]
    deleted: frozenset[str]

    def __init__(self, source: _Census) -> None:
        self._source = source
        self._before = self._snapshot()
        self._finished = False
        self.added = frozenset()
        self.modified = frozenset()
        self.rewritten = frozenset()
        self.deleted = frozenset()

    def finish(self, written: Iterable[str] = ()) -> None:
        """Compare the epoch directory with the snapshot taken at construction.

        ``written`` is the names this run wrote. A name in both snapshots whose
        hash did not change is rewritten only when it is in that list.
        """
        after = self._snapshot()
        before_names = set(self._before)
        after_names = set(after)
        written_names = set(written)
        self.added = frozenset(after_names - before_names)
        self.deleted = frozenset(before_names - after_names)
        stayed = before_names & after_names
        self.modified = frozenset(
            name for name in stayed if self._before[name] != after[name]
        )
        self.rewritten = frozenset(
            name
            for name in stayed & written_names
            if self._before[name] == after[name]
        )
        self._finished = True

    def counts(self) -> tuple[int, int, int, int]:
        """Added, modified, rewritten, and deleted counts. Requires ``finish``."""
        if not self._finished:
            raise RuntimeError("finish the epoch diff before reporting it")
        return len(self.added), len(self.modified), len(self.rewritten), len(self.deleted)

    def _snapshot(self) -> dict[str, str]:
        return dict(self._source.census())


def format_diff_table(epoch: str, rows: Sequence[tuple[str, EpochEntityDiff]]) -> str:
    """Box table of added, modified, rewritten, and deleted counts, one operator per row.

    The operator column is left-aligned. Count columns are right-aligned.
    """
    body = [
        (name, *(str(count) for count in diff.counts()))
        for name, diff in rows
    ]
    return f"epoch {epoch}\n{_box_table(body)}"


def _box_table(body: Sequence[tuple[str, ...]]) -> str:
    widths = []
    for index, header in enumerate(_HEADERS):
        width = len(header)
        for row in body:
            width = max(width, len(row[index]))
        widths.append(width)

    def rule(left: str, mid: str, right: str) -> str:
        cells = ["─" * (width + 2) for width in widths]
        return left + mid.join(cells) + right

    def row(values: tuple[str, ...]) -> str:
        cells: list[str] = []
        for value, width, align_right in zip(values, widths, _ALIGN_RIGHT, strict=True):
            text = value.rjust(width) if align_right else value.ljust(width)
            cells.append(f" {text} ")
        return "│" + "│".join(cells) + "│"

    lines = [
        rule("┌", "┬", "┐"),
        row(_HEADERS),
        rule("├", "┼", "┤"),
        *(row(item) for item in body),
        rule("└", "┴", "┘"),
    ]
    return "\n".join(lines)
