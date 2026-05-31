from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import reset_rate_limits
from app.core.security import create_access_token, hash_password
from app.db.models import AuditLog, Project, ProjectStatus, Report, ReportType, User, UserRole


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


def test_security_headers_are_applied(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_sensitive_rate_limit_blocks_repeated_login(client: TestClient) -> None:
    original_limit = settings.rate_limit_sensitive_per_window
    original_window = settings.rate_limit_window_seconds
    settings.rate_limit_sensitive_per_window = 2
    settings.rate_limit_window_seconds = 60
    reset_rate_limits()
    try:
        for _ in range(2):
            response = client.post("/api/auth/login", json={"email": "none@example.com", "password": "bad"})
            assert response.status_code == 401
        blocked = client.post("/api/auth/login", json={"email": "none@example.com", "password": "bad"})
        assert blocked.status_code == 429
    finally:
        settings.rate_limit_sensitive_per_window = original_limit
        settings.rate_limit_window_seconds = original_window
        reset_rate_limits()


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


def test_report_download_blocks_internal_paths(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    user = db_session.scalar(select(User).where(User.email == "teacher@example.com"))
    assert user is not None
    project = Project(
        owner_id=user.id,
        title="Tema seguro",
        area="Biología",
        educational_level="ESO",
        legal_framework="Normativa aportada",
        status=ProjectStatus.reports_generated,
    )
    db_session.add(project)
    db_session.flush()
    report = Report(
        project_id=project.id,
        report_type=ReportType.scientific_update,
        title="Informe inseguro",
        content_markdown="## Fuentes\n\nRuta interna C:\\Users\\test\\storage\\uploads\\tema.docx",
    )
    db_session.add(report)
    db_session.commit()

    response = client.get(f"/api/reports/{report.id}/download", headers=auth_headers)

    assert response.status_code == 422
    assert "puerta de calidad" in response.json()["detail"]


def test_legacy_report_download_repairs_missing_footer_without_inventing_sources(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    user = db_session.scalar(select(User).where(User.email == "teacher@example.com"))
    assert user is not None
    project = Project(
        owner_id=user.id,
        title="Tema legacy",
        area="Biologia",
        educational_level="ESO",
        legal_framework="Normativa aportada",
        status=ProjectStatus.reports_generated,
    )
    db_session.add(project)
    db_session.flush()
    report = Report(
        project_id=project.id,
        report_type=ReportType.scientific_update,
        title="Informe antiguo",
        content_markdown=(
            "## Informe antiguo\n\n"
            "Contenido generado antes de la puerta de calidad actual. "
            "Incluye observaciones docentes amplias, pero no conserva metadatos corporativos ni "
            "citas trazables porque pertenece a una version anterior del MVP."
        ),
    )
    db_session.add(report)
    db_session.commit()

    response = client.get(f"/api/reports/{report.id}/download", headers=auth_headers)

    assert response.status_code == 200
    text = response.content.decode("utf-8")
    assert "Fuentes y limitaciones" in text
    assert "No se han inventado fuentes" in text
    assert "asistencia de IA" in text
    db_session.refresh(report)
    assert "Centro de Formaci" in report.content_markdown
