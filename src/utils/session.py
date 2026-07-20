"""Session ID utility — single source of truth shared by SaveManager and dumper.

Usage:
    from src.utils.session import init_session_id, get_session_id

    init_session_id()          # startup: generate fresh ID
    init_session_id(old_id)    # restore: switch to archived ID
    sid = get_session_id()     # read current ID
"""

from datetime import datetime

_session_id: str | None = None


def init_session_id(session_id: str | None = None) -> str:
    """Initialize (or re-initialize) the session ID.

    Called once at startup, and during /restore to sync to an archived session.
    """
    global _session_id
    if session_id is not None:
        _session_id = session_id
    else:
        _session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    return _session_id


def get_session_id() -> str:
    """Return the current session ID. Raises RuntimeError if not initialized."""
    if _session_id is None:
        raise RuntimeError("Session ID not initialized — call init_session_id() first")
    return _session_id
