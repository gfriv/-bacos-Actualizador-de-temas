from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.llm.schemas import AIProviderConfig

SESSION_TTL_MINUTES = 120
_SESSIONS: dict[str, tuple[AIProviderConfig, datetime]] = {}


def create_ai_session(config: AIProviderConfig) -> tuple[str, datetime]:
    cleanup_expired_ai_sessions()
    session_id = uuid4().hex
    expires_at = datetime.now(UTC) + timedelta(minutes=SESSION_TTL_MINUTES)
    _SESSIONS[session_id] = (config, expires_at)
    return session_id, expires_at


def get_ai_session(session_id: str) -> AIProviderConfig | None:
    cleanup_expired_ai_sessions()
    stored = _SESSIONS.get(session_id)
    if stored is None:
        return None
    return stored[0]


def cleanup_expired_ai_sessions() -> None:
    now = datetime.now(UTC)
    expired = [session_id for session_id, (_, expires_at) in _SESSIONS.items() if expires_at <= now]
    for session_id in expired:
        _SESSIONS.pop(session_id, None)
