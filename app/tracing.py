from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Load .env before Langfuse initializes — SDK caches credentials at import time
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

try:
    from langfuse import Langfuse
    from langfuse.decorators import langfuse_context, observe

    # Explicit initialization so credentials are never stale regardless of import order
    _lf = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "").strip('"'),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", "").strip('"'),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").strip('"'),
    )
except Exception:  # pragma: no cover
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

    langfuse_context = _DummyContext()


def tracing_enabled() -> bool:
    pk = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip('"')
    sk = os.getenv("LANGFUSE_SECRET_KEY", "").strip('"')
    return bool(pk and sk)


def flush() -> None:
    try:
        _lf.flush()
    except Exception:
        pass
