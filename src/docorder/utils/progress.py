"""Stderr progress bar for one operator stage."""

from __future__ import annotations

import sys

from tqdm import tqdm


def progress_bar(name: str, total: int | None, initial: int = 0):
    """A bar for one stage. ``total`` is None when the count is not known yet.

    ``initial`` is how much of the stage is already done. A resumed run starts
    there instead of flashing zero for a frame before the skipped count is
    added.
    """
    return tqdm(
        total=total,
        initial=initial,
        desc=name,
        unit="entity",
        dynamic_ncols=True,
        file=sys.stderr,
        leave=True,
    )
