from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def audit(db: Session, action: str, user_id: int | None = None, project_id: int | None = None, **metadata: Any) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            project_id=project_id,
            action=action,
            metadata_json=metadata or None,
        )
    )
