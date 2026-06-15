from __future__ import annotations

import functools
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

import logging as _logging

_lf = None

try:
    from langfuse import Langfuse

    _lf = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "").strip('"'),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", "").strip('"'),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").strip('"'),
    )
except Exception as _e:
    _logging.warning("Langfuse init failed: %s", _e)
    _lf = None


def observe(*deco_args: Any, **deco_kwargs: Any):
    """Decorator that wraps a function in a Langfuse generation span (v3 API)."""

    def decorator(func):
        if _lf is None:
            return func

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            with _lf.start_as_current_span(name=func.__name__):
                return func(*args, **kwargs)

        return wrapper

    if len(deco_args) == 1 and callable(deco_args[0]):
        return decorator(deco_args[0])
    return decorator


class _LangfuseContext:
    """Thin shim mapping the v2 langfuse_context API onto the v3 client."""

    def update_current_trace(self, **kwargs: Any) -> None:
        if _lf is None:
            return
        try:
            v3: dict[str, Any] = {}
            for key in ("user_id", "session_id", "name", "tags", "metadata"):
                if key in kwargs:
                    v3[key] = kwargs[key]
            if v3:
                _lf.update_current_trace(**v3)
        except Exception as exc:
            _logging.debug("update_current_trace: %s", exc)

    def update_current_observation(self, **kwargs: Any) -> None:
        if _lf is None:
            return
        try:
            meta: dict[str, Any] = dict(kwargs.get("metadata") or {})
            if "usage_details" in kwargs:
                ud = kwargs["usage_details"]
                meta["tokens_in"] = ud.get("input", 0)
                meta["tokens_out"] = ud.get("output", 0)
            if meta:
                _lf.update_current_span(metadata=meta)
        except Exception as exc:
            _logging.debug("update_current_observation: %s", exc)

    def flush(self) -> None:
        if _lf is not None:
            try:
                _lf.flush()
            except Exception:
                pass


langfuse_context = _LangfuseContext()


def tracing_enabled() -> bool:
    pk = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip('"')
    sk = os.getenv("LANGFUSE_SECRET_KEY", "").strip('"')
    return bool(pk and sk and _lf is not None)


def flush() -> None:
    if _lf is not None:
        try:
            _lf.flush()
        except Exception:
            pass


def langfuse_flush() -> None:
    flush()
    langfuse_context.flush()
