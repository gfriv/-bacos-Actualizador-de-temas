import base64
import json

from fastapi.testclient import TestClient

from tests.test_documents_and_consolidation import make_docx_bytes
from tests.test_projects import create_project


def test_queue_research_analysis_creates_analysis_run(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    calls: list[tuple[str, str, tuple[object, ...]]] = []

    def fake_enqueue(queue_name: str, function_path: str, *args: object) -> object:
        calls.append((queue_name, function_path, args))
        return object()

    monkeypatch.setattr("app.api.routes.enqueue_rq_job", fake_enqueue)
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

    response = client.post(f"/api/projects/{project_id}/analysis/research/queue", headers=auth_headers)

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "queued"
    assert calls
    assert calls[0][0] == "research"
    assert calls[0][1] == "workers.tasks.research_worker"

    status_response = client.get(f"/api/analysis-runs/{payload['id']}", headers=auth_headers)
    assert status_response.status_code == 200
    assert status_response.json()["id"] == payload["id"]


def test_queue_research_rejects_byok_config_to_avoid_key_persistence(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    project_id = create_project(client, auth_headers)
    encoded = base64.urlsafe_b64encode(
        json.dumps(
            {
                "provider_id": "openai",
                "mode": "api",
                "api_key": "sk-test-secret-should-not-persist",
                "model": "gpt-4o-mini",
            }
        ).encode("utf-8")
    ).decode("ascii")

    response = client.post(
        f"/api/projects/{project_id}/analysis/research/queue",
        headers={**auth_headers, "X-Abacos-AI-Config": encoded},
    )

    assert response.status_code == 400
    assert "BYOK" in response.json()["detail"]
    assert "sk-test-secret" not in response.text
