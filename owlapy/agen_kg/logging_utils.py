"""Logging helpers for the agen_kg package.

The agen_kg components expose an ``enable_logging`` flag. When set, progress
messages are emitted through per-module loggers under ``owlapy.agen_kg`` and a
console handler is attached so the opt-in keeps producing visible output even
if the host application has not configured logging. Host applications that
configure logging themselves can ignore the flag and control verbosity via the
``owlapy`` logger hierarchy instead.
"""

import logging

_console_handler = None


def enable_console_logging(level: int = logging.INFO) -> None:
    """Attach a console handler to the ``owlapy.agen_kg`` logger (idempotent)."""
    global _console_handler
    pkg_logger = logging.getLogger("owlapy.agen_kg")
    pkg_logger.setLevel(level)
    if _console_handler is None:
        _console_handler = logging.StreamHandler()
        _console_handler.setFormatter(logging.Formatter("%(name)s: %(levelname)s :: %(message)s"))
        pkg_logger.addHandler(_console_handler)
