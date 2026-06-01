from fastapi.testclient import TestClient


def test_ai_provider_catalog_is_public(client: TestClient) -> None:
    response = client.get("/api/ai/providers")

    assert response.status_code == 200
    provider_ids = {provider["id"] for provider in response.json()}
    assert {"mock", "openai", "gemini", "anthropic", "openai_compatible", "ollama"}.issubset(provider_ids)


def test_provider_validation_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/ai/providers/validate",
        json={"config": {"provider_id": "mock", "mode": "local"}},
    )

    assert response.status_code == 401


def test_authenticated_mock_provider_validation(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/ai/providers/validate",
        headers=auth_headers,
        json={"config": {"provider_id": "mock", "mode": "local"}},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["provider_id"] == "mock"


def test_model_listing_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/ai/providers/models",
        json={"config": {"provider_id": "mock", "mode": "local"}},
    )

    assert response.status_code == 401


def test_generate_text_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/ai/generate-text",
        json={
            "config": {"provider_id": "mock", "mode": "local"},
            "input": {"prompt": "Genera un resumen"},
        },
    )

    assert response.status_code == 401


def test_authenticated_mock_generation(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/ai/generate-text",
        headers=auth_headers,
        json={
            "config": {"provider_id": "mock", "mode": "local"},
            "input": {"prompt": "Genera un resumen"},
        },
    )

    assert response.status_code == 200
    assert response.json()["provider_id"] == "mock"
    assert "MockProvider" in response.json()["text"]


def test_ai_session_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/ai/sessions",
        json={"config": {"provider_id": "mock", "mode": "local"}},
    )

    assert response.status_code == 401


def test_ai_session_returns_ephemeral_id_without_leaking_key(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    secret = "sk-test-secret-should-not-leak"

    response = client.post(
        "/api/ai/sessions",
        headers=auth_headers,
        json={"config": {"provider_id": "mock", "mode": "local", "api_key": secret}},
    )

    assert response.status_code == 200
    assert response.json()["ai_session_id"]
    assert response.json()["expires_at"]
    assert secret not in response.text


def test_ollama_pull_requires_explicit_confirmation(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/ai/ollama/pull",
        headers=auth_headers,
        json={"model": "qwen2.5:7b-instruct", "confirm": False},
    )

    assert response.status_code == 400
    assert "Confirma" in response.json()["detail"]


def test_ollama_pull_is_disabled_by_default(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/ai/ollama/pull",
        headers=auth_headers,
        json={"model": "qwen2.5:7b-instruct", "confirm": True},
    )

    assert response.status_code == 403
    assert "OLLAMA_PULL_ENABLED" in response.json()["detail"]


def test_remote_runtime_blocks_ollama_without_calling_localhost(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    monkeypatch.setenv("VERCEL", "1")

    response = client.post(
        "/api/ai/providers/validate",
        headers=auth_headers,
        json={
            "config": {
                "provider_id": "ollama",
                "mode": "local",
                "base_url": "http://localhost:11434",
                "model": "qwen2.5:7b-instruct",
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "Ollama local solo" in response.json()["message"]


def test_remote_runtime_blocks_private_openai_compatible_endpoint_and_redacts_key(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    monkeypatch.setenv("VERCEL", "1")
    secret = "sk-test-secret-should-not-leak"

    response = client.post(
        "/api/ai/providers/models",
        headers=auth_headers,
        json={
            "config": {
                "provider_id": "openai_compatible",
                "mode": "api",
                "base_url": "http://127.0.0.1:11434/v1",
                "api_key": secret,
                "model": "local-model",
            }
        },
    )

    assert response.status_code == 400
    assert "HTTPS públicos" in response.json()["detail"]
    assert secret not in response.text


def test_external_ai_provider_is_blocked_until_rgpd_gate_is_enabled(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    secret = "sk-test-secret-should-not-leak"

    response = client.post(
        "/api/ai/providers/models",
        headers=auth_headers,
        json={
            "config": {
                "provider_id": "openai",
                "mode": "api",
                "api_key": secret,
                "model": "gpt-4o-mini",
            }
        },
    )

    assert response.status_code == 400
    assert "proveedores externos de IA" in response.json()["detail"]
    assert secret not in response.text


def test_external_ai_session_accepts_explicit_teacher_confirmation_without_leaking_key(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    secret = "sk-test-secret-should-not-leak"

    response = client.post(
        "/api/ai/sessions",
        headers=auth_headers,
        json={
            "config": {
                "provider_id": "openai",
                "mode": "api",
                "api_key": secret,
                "model": "gpt-4o-mini",
                "external_data_processing_confirmed": True,
                "web_search_enabled": True,
                "web_search_provider": "duckduckgo",
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["ai_session_id"]
    assert secret not in response.text
