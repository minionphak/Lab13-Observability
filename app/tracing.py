from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Load .env before Langfuse initializes — SDK caches credentials at import time
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

import logging as _logging

_lf = None
_LANGFUSE_AVAILABLE = False

try:
    from langfuse import Langfuse
    from langfuse.decorators import langfuse_context, observe
    _LANGFUSE_AVAILABLE = True
except ImportError:  # pragma: no cover
    pass

if _LANGFUSE_AVAILABLE:
    try:
        _lf = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "").strip('"'),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", "").strip('"'),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").strip('"'),
        )
    except Exception as _e:  # pragma: no cover
        _logging.warning("Langfuse client init failed: %s", _e)
        _lf = None

if not _LANGFUSE_AVAILABLE:  # pragma: no cover
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

        def flush(self) -> None:
            return None

    langfuse_context = _DummyContext()


def tracing_enabled() -> bool:
    pk = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip('"')
    sk = os.getenv("LANGFUSE_SECRET_KEY", "").strip('"')
    return bool(pk and sk)


def flush() -> None:
    if _lf is not None:
        try:
            _lf.flush()
        except Exception:
            pass


def langfuse_flush() -> None:
    if _lf is not None:
        try:
            _lf.flush()
        except Exception:
            pass
    try:
        langfuse_context.flush()
    except Exception:
        pass
