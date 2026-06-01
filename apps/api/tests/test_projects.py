from fastapi.testclient import TestClient


def create_project(client: TestClient, auth_headers: dict[str, str]) -> int:
    response = client.post(
        "/api/projects",
        headers=auth_headers,
        json={
            "title": "Tema de prueba",
            "area": "Educación Primaria",
            "educational_level": "Oposiciones docentes",
            "legal_framework": "Normativa aportada por el profesor",
            "bibliography_notes": "Bibliografía base",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_project(client: TestClient, auth_headers: dict[str, str]) -> None:
    project_id = create_project(client, auth_headers)
    assert project_id > 0


def test_legal_framework_catalog_is_public(client: TestClient) -> None:
    response = client.get("/api/legal-frameworks")

    assert response.status_code == 200
    option_ids = {option["id"] for option in response.json()}
    assert {"auto", "extremadura_infantil", "extremadura_primaria", "estatal_oposiciones"}.issubset(option_ids)


def test_create_project_infers_legal_framework_when_empty(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/projects",
        headers=auth_headers,
        json={
            "title": "Tema sin normativa manual",
            "area": "Educacion Primaria",
            "educational_level": "Oposiciones Educacion Primaria Extremadura",
            "legal_framework": "",
            "bibliography_notes": "",
            "instructions": "Preparacion para tribunal en Caceres.",
        },
    )

    assert response.status_code == 201
    legal_framework = response.json()["legal_framework"]
    assert "inferido" in legal_framework.lower()
    assert "157/2022" in legal_framework
    assert "Extremadura" in legal_framework


def test_register_ignores_requested_admin_role(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "attacker@example.com",
            "password": "change-me-secure",
            "full_name": "Usuario sin privilegios",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "teacher"


def test_demo_login_seeds_projects(client: TestClient) -> None:
    response = client.post("/api/auth/demo")
    assert response.status_code == 200
    token = response.json()["access_token"]

    projects = client.get("/api/projects", headers={"Authorization": f"Bearer {token}"})
    assert projects.status_code == 200
    assert len(projects.json()) >= 3


def test_create_suggestion_and_review(client: TestClient, auth_headers: dict[str, str]) -> None:
    project_id = create_project(client, auth_headers)
    response = client.post(
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
    assert response.status_code == 201
    suggestion_id = response.json()["id"]

    review = client.patch(
        f"/api/suggestions/{suggestion_id}",
        headers=auth_headers,
        json={"status": "approved", "teacher_notes": "Correcto"},
    )
    assert review.status_code == 200
    assert review.json()["status"] == "approved"
