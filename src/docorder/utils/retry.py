"""Retry policy declared by an operator home and applied by the runner."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from docorder.utils.errors import FatalError

log = logging.getLogger(__name__)
T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    """How many times one entity call may run, and how long to wait between tries.

    ``max_attempts`` includes the first call. The default ``1`` means a
    failure is final. ``backoff_seconds`` is the base delay. After attempt
    ``n`` fails, the wait before the next try is ``backoff_seconds * n``
    seconds. A base of ``0`` retries at once.

    An operator home declares this as the ``retry`` object in ``props.json``.
    A job node may replace that whole policy when the node is added.
    ``from_mapping`` reads ``max_attempts`` and ``backoff_seconds``. A
    missing mapping, or a missing key, uses the defaults above. An attempt
    count below 1 raises ``ValueError`` while the home is loaded.

    ``FatalError`` is never retried. Every other exception is, until
    ``max_attempts`` is exhausted. The last exception propagates unchanged.
    """

    max_attempts: int = 1
    backoff_seconds: float = 0

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> RetryPolicy:
        """Build a policy from a ``retry`` object. ``None`` uses the defaults."""
        raw = raw or {}
        attempts = int(raw.get("max_attempts", 1))
        if attempts < 1:
            raise ValueError("retry.max_attempts must be >= 1")
        return cls(
            max_attempts=attempts,
            backoff_seconds=float(raw.get("backoff_seconds", 0)),
        )


def call_with_retry(action: Callable[[], T], policy: RetryPolicy, *, label: str) -> T:
    """Run ``action`` under ``policy``. ``label`` is the log line for a failed try.

    ``FatalError`` stops the loop immediately. Any other exception is logged
    and, when attempts remain, followed by ``backoff_seconds * attempt``
    seconds of sleep. ``attempt`` starts at 1.
    """
    last: Exception | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return action()
        except FatalError:
            raise
        except Exception as exc:
            last = exc
            if attempt >= policy.max_attempts:
                raise
            delay = policy.backoff_seconds * attempt
            log.warning("%s attempt %s/%s failed: %s", label, attempt, policy.max_attempts, exc)
            if delay > 0:
                time.sleep(delay)
    assert last is not None
    raise last
