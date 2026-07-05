"""Shared in-memory progress tracker for real-time frontend updates."""
import threading
import uuid

_store: dict[str, dict] = {}
_lock = threading.Lock()


def create_session() -> str:
    """Start a new progress session, return its ID."""
    sid = uuid.uuid4().hex[:12]
    with _lock:
        _store[sid] = {"steps": [], "done": False}
    return sid


def push(sid: str, step: str) -> None:
    with _lock:
        if sid in _store:
            _store[sid]["steps"].append(step)


def mark_done(sid: str) -> None:
    with _lock:
        if sid in _store:
            _store[sid]["done"] = True


def get_progress(sid: str) -> dict | None:
    with _lock:
        return _store.get(sid)


def cleanup(sid: str) -> None:
    with _lock:
        _store.pop(sid, None)
