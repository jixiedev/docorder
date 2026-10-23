"""Errors the runner treats differently during retry."""


class DocorderError(Exception):
    """Failure of a stage, operator, or job definition.

    Every error this package raises on purpose is a ``DocorderError``.
    ``call_with_retry`` retries it, except ``FatalError``. An ordinary
    ``Exception`` raised by function code is retried the same way.
    """


class JobValidationError(DocorderError):
    """The job graph or an operator home's static contract is inconsistent.

    Raised while the job is being built, before any epoch runs. Typical
    causes are a missing ``props.json``, a ``class`` string with no ``:``,
    an unknown ``type``, a missing or cyclic upstream, or two nodes writing
    the same output path. The same job fails the same way on the next run.
    """


class OperatorValidationError(DocorderError):
    """One operator cannot run with the class and config it was given.

    Assembly raises it before any stage writes: the function class cannot
    be imported, is not a subclass of the base for its ``type``, or still
    has abstract methods. A stage also raises it when that operator cannot
    proceed, for example parallelism below 1, a missing upstream, or a
    lineage that names the same output twice. That stage stops.
    """


class FatalError(DocorderError):
    """Do not retry. The input is missing or the function contract is broken.

    ``call_with_retry`` re-raises this on the first attempt. Use it when
    another attempt would fail for the same reason: a required config key
    is absent, a path is not the kind of file the function needs, or data
    emitted by a function has the wrong type. A failure that might pass
    later, such as a command that exits non-zero, stays a ``DocorderError``
    so the operator's retry policy still applies.
    """
