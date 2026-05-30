from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient

from app.core.config import settings
from tests.test_projects import create_project


def make_docx_bytes() -> bytes:
    buffer = BytesIO()
    document = Document()
    document.add_heading("1. Introducción", level=1)
    document.add_paragraph("Texto original sobre competencias, criterios y evaluación.")
    document.add_heading("2. Desarrollo", level=1)
    document.add_paragraph("Contenido científico pendiente de revisión.")
    document.save(buffer)
    buffer.seek(0)
    return buffer.read()


def test_upload_document_extracts_docx(client: TestClient, auth_headers: dict[str, str]) -> None:
    project_id = create_project(client, auth_headers)
    response = client.post(
        f"/api/projects/{project_id}/documents",
        headers=auth_headers,
        files={
            "file": (
                "tema.docx",
                make_docx_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 201
    assert "Texto original" in response.json()["extracted_text"]
    assert "file_path" not in response.json()

    sections = client.get(f"/api/projects/{project_id}/sections", headers=auth_headers)
    assert sections.status_code == 200
    assert len(sections.json()) >= 1


def test_upload_invalid_docx_returns_422_without_internal_path(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    project_id = create_project(client, auth_headers)
    response = client.post(
        f"/api/projects/{project_id}/documents",
        headers=auth_headers,
        files={
            "file": (
                "tema.docx",
                b"esto no es un docx valido",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 422
    assert "DOCX/PDF" in response.json()["detail"]
    assert "storage" not in response.json()["detail"].lower()


def test_database_storage_backend_serves_uploaded_document(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    original_storage_backend = settings.storage_backend
    settings.storage_backend = "database"
    try:
        project_id = create_project(client, auth_headers)
        document = client.post(
            f"/api/projects/{project_id}/documents",
            headers=auth_headers,
            files={
                "file": (
                    "tema.docx",
                    make_docx_bytes(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        assert document.status_code == 201

        download = client.get(f"/api/documents/{document.json()['id']}/download", headers=auth_headers)
        assert download.status_code == 200
        assert download.content.startswith(b"PK")
    finally:
        settings.storage_backend = original_storage_backend


def test_research_analysis_creates_reports_and_suggestions(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    project_id = create_project(client, auth_headers)
    client.post(
        f"/api/projects/{project_id}/documents",
        headers=auth_headers,
        files={
            "file": (
                "tema.docx",
                make_docx_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    response = client.post(f"/api/projects/{project_id}/analysis/research", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["reports"]) == 6
    assert len(response.json()["suggestions"]) == 2

    reports = client.get(f"/api/projects/{project_id}/reports", headers=auth_headers)
    suggestions = client.get(f"/api/projects/{project_id}/suggestions", headers=auth_headers)
    assert len(reports.json()) == 6
    assert len(suggestions.json()) == 2
    source_report = next(report for report in reports.json() if report["report_type"] == "source_validation")
    report_download = client.get(f"/api/reports/{source_report['id']}/download", headers=auth_headers)
    assert report_download.status_code == 200
    assert b"Centro de Formaci" in report_download.content


def test_consolidation_rejects_pending_only(client: TestClient, auth_headers: dict[str, str]) -> None:
    project_id = create_project(client, auth_headers)
    client.post(
        f"/api/projects/{project_id}/documents",
        headers=auth_headers,
        files={
            "file": (
                "tema.docx",
                make_docx_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    client.post(
        f"/api/projects/{project_id}/suggestions",
        headers=auth_headers,
        json={
            "suggestion_type": "scientific_update",
            "original_fragment": "Texto original",
            "proposed_change": "Texto actualizado",
            "justification": "Justificación docente",
            "source_reference": "MockProvider",
            "confidence_level": "medium",
        },
    )
    response = client.post(f"/api/projects/{project_id}/consolidate", headers=auth_headers)
    assert response.status_code == 400
    assert "No hay sugerencias aprobadas" in response.json()["detail"]


def test_consolidation_uses_approved_suggestions_and_generates_resource(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    project_id = create_project(client, auth_headers)
    client.post(
        f"/api/projects/{project_id}/documents",
        headers=auth_headers,
        files={
            "file": (
                "tema.docx",
                make_docx_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    suggestion = client.post(
        f"/api/projects/{project_id}/suggestions",
        headers=auth_headers,
        json={
            "suggestion_type": "scientific_update",
            "original_fragment": "Texto original",
            "proposed_change": "Texto actualizado",
            "justification": "Justificación docente",
            "source_reference": "MockProvider",
            "confidence_level": "medium",
        },
    ).json()
    client.patch(
        f"/api/suggestions/{suggestion['id']}",
        headers=auth_headers,
        json={"status": "approved"},
    )

    consolidated = client.post(f"/api/projects/{project_id}/consolidate", headers=auth_headers)
    assert consolidated.status_code == 200
    assert "docx_path" not in consolidated.json()
    consolidated_download = client.get(
        f"/api/projects/{project_id}/consolidated/download",
        headers=auth_headers,
    )
    assert consolidated_download.status_code == 200
    assert consolidated_download.content.startswith(b"PK")
    assert "Documento consolidado" in consolidated.json()["content_markdown"]
    assert "Centro de Formación y Estudios Ábacos" in consolidated.json()["content_markdown"]
    assert "asistencia de IA" in consolidated.json()["content_markdown"]

    resource = client.post(
        f"/api/projects/{project_id}/resources",
        headers=auth_headers,
        json={"resource_type": "esquema_desarrollado"},
    )
    assert resource.status_code == 200
    assert "file_path" not in resource.json()
    resource_download = client.get(f"/api/resources/{resource.json()['id']}/download", headers=auth_headers)
    assert resource_download.status_code == 200
    assert b"Recurso" in resource_download.content
    assert "Recurso didáctico simulado" in resource.json()["content_markdown"]
    assert "Centro de Formación y Estudios Ábacos" in resource.json()["content_markdown"]
    assert "asistencia de IA" in resource.json()["content_markdown"]


def test_resource_generation_requires_consolidated_document(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    project_id = create_project(client, auth_headers)
    response = client.post(
        f"/api/projects/{project_id}/resources",
        headers=auth_headers,
        json={"resource_type": "esquema_desarrollado"},
    )
    assert response.status_code == 400
    assert "documento consolidado" in response.json()["detail"]
