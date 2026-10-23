"""A function that acts on one upstream entity and returns nothing."""

from abc import ABC, abstractmethod

from docorder.core.entity import Entity
from docorder.functions.function import Function


class ApplyFunction(Function, ABC):
    """Type marker for an apply operator.

    ``apply`` runs once per upstream entity. ``finish`` runs once after that,
    including when the upstream epoch has no entities. Neither method may
    return a value: an apply operator writes no entity and has no downstream.
    """

    @abstractmethod
    def apply(self, entity: Entity) -> None:
        """Act on one upstream entity. Return nothing."""

    def finish(self) -> None:
        """Run once after every entity has been applied. Return nothing."""
        return None
