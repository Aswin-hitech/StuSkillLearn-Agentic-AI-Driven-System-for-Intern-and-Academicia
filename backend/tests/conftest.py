"""Keep tests isolated from the developer's live/demo database and providers."""
from __future__ import annotations

import atexit
import os
from pathlib import Path
import tempfile
import uuid


TEST_DATABASE = Path(tempfile.gettempdir()) / f"stuskilllink-test-{uuid.uuid4().hex}.db"
TEST_LANGGRAPH_DATABASE = Path(tempfile.gettempdir()) / f"stuskilllink-langgraph-test-{uuid.uuid4().hex}.sqlite"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE.as_posix()}"
os.environ["LANGGRAPH_CHECKPOINT_PATH"] = str(TEST_LANGGRAPH_DATABASE)
os.environ["LANGGRAPH_STRICT_MSGPACK"] = "true"
os.environ["NVIDIA_NIM_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["JWT_SECRET_KEY"] = "stuskilllink-isolated-test-secret-with-32-plus-characters"


@atexit.register
def remove_test_database() -> None:
    try:
        from app.db import engine
        engine.dispose()
    except ImportError:
        pass
    TEST_DATABASE.unlink(missing_ok=True)
    TEST_LANGGRAPH_DATABASE.unlink(missing_ok=True)
