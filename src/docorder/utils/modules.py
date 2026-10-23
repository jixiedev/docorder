"""Load a symbol from an operator home or an importable module."""

from __future__ import annotations

import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Any

from docorder.utils.errors import JobValidationError, OperatorValidationError


class ModuleLoader:
    """Load the function class named by an operator home's ``class`` field.

    The value is ``module:Class``. The colon is split once.

    ``primary:Class`` loads ``primary.py`` from that operator home. The file
    is executed with ``importlib`` under the module name
    ``docorder_home_<home directory name>``, then cached on this class by
    the home's resolved path. A second load of the same home returns the
    cached module and does not execute the file again. A home with no
    ``primary.py`` raises ``JobValidationError``.

    Any other module name is imported with ``importlib.import_module``, so
    it must already be importable, for example
    ``docorder.functions.impl.command:Command``. The symbol is taken with
    ``getattr``. A missing symbol is ``JobValidationError``.

    ``load_function_class`` is what operator assembly calls. It turns a
    load failure into ``OperatorValidationError``, then requires the symbol
    to be a concrete subclass of the base for the operator's ``type``. An
    abstract class is rejected with the names of the methods it still has
    to implement. The check runs before any stage, so a bad class on a
    later node fails the job before earlier nodes write.
    """

    _modules: dict[Path, Any] = {}

    @classmethod
    def load_primary(cls, home: Path) -> Any:
        """Return the module object for ``home / primary.py``, loading it once."""
        key = home.resolve()
        cached = cls._modules.get(key)
        if cached is not None:
            return cached
        path = home / "primary.py"
        if not path.is_file():
            raise JobValidationError(f"{home} has no primary.py")
        spec = importlib.util.spec_from_file_location(f"docorder_home_{home.name}", path)
        if spec is None or spec.loader is None:
            raise JobValidationError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls._modules[key] = module
        return module

    @classmethod
    def load_symbol(cls, home: Path, target: str) -> Any:
        """Return the attribute named by ``target`` (``module:Name``).

        ``primary`` reads the home. Every other module name is imported
        from the normal module path. ``target`` must contain one colon.
        """
        module_name, symbol_name = target.split(":", 1)
        if module_name == "primary":
            module = cls.load_primary(home)
        else:
            module = importlib.import_module(module_name)
        try:
            return getattr(module, symbol_name)
        except AttributeError as exc:
            raise JobValidationError(f"{home.name}: {target} was not found") from exc

    @classmethod
    def load_function_class(
        cls,
        home: Path,
        operator_name: str,
        spec: object,
        base: type,
    ) -> type:
        """Load ``spec`` and require a concrete subclass of ``base``.

        ``operator_name`` is only used in the error text. A bad spec, a
        missing symbol, the wrong base, or leftover abstract methods all
        raise ``OperatorValidationError``.
        """
        if not isinstance(spec, str) or ":" not in spec:
            raise OperatorValidationError(
                f"{operator_name}: class must be 'primary:Class' or 'module:Class'"
            )
        try:
            symbol = cls.load_symbol(home, spec)
        except JobValidationError as exc:
            raise OperatorValidationError(str(exc)) from exc
        if not isinstance(symbol, type) or not issubclass(symbol, base):
            raise OperatorValidationError(
                f"{operator_name}: {spec} must be a subclass of {base.__name__}"
            )
        if inspect.isabstract(symbol):
            missing = ", ".join(sorted(symbol.__abstractmethods__))
            raise OperatorValidationError(f"{operator_name}: {spec} must implement {missing}")
        return symbol
