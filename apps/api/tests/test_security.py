from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.db.models import AuditLog, Project, ProjectStatus, User, UserRole


def test_tampered_bearer_token_cannot_create_project(client: TestClient) -> None:
    response = client.post(
        "/api/projects",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
        json={
            "title": "Tema privado",
            "area": "Biología",
            "educational_level": "ESO",
            "legal_framework": "Normativa aportada",
        },
    )

    assert response.status_code == 401


def test_reviewer_role_cannot_create_project(client: TestClient, db_session: Session) -> None:
    reviewer = User(
        email="reviewer@example.com",
        password_hash=hash_password("change-me-secure"),
        full_name="Revisor Ábacos",
        role=UserRole.reviewer,
    )
    db_session.add(reviewer)
    db_session.commit()

    token = create_access_token(str(reviewer.id))
    response = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Tema privado",
            "area": "Biología",
            "educational_level": "ESO",
            "legal_framework": "Normativa aportada",
        },
    )

    assert response.status_code == 403


def test_teacher_cannot_access_another_teacher_project(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    other = User(
        email="other@example.com",
        password_hash=hash_password("change-me-secure"),
        full_name="Otro Docente",
        role=UserRole.teacher,
    )
    db_session.add(other)
    db_session.flush()
    project = Project(
        owner_id=other.id,
        title="Proyecto ajeno",
        area="Lengua",
        educational_level="Primaria",
        legal_framework="Normativa aportada",
        status=ProjectStatus.draft,
    )
    db_session.add(project)
    db_session.commit()

    response = client.get(f"/api/projects/{project.id}", headers=auth_headers)

    assert response.status_code == 403


def test_api_key_is_not_stored_in_audit_log(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    secret = "sk-test-secret-should-not-be-audited"

    response = client.post(
        "/api/ai/providers/validate",
        headers=auth_headers,
        json={
            "config": {
                "provider_id": "mock",
                "mode": "local",
                "api_key": secret,
            }
        },
    )

    assert response.status_code == 200
    serialized_logs = "\n".join(str(item.metadata_json) for item in db_session.scalars(select(AuditLog)))
    assert secret not in serialized_logs
