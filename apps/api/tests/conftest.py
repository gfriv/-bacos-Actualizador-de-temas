from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.rate_limit import reset_rate_limits
from app.db.base import Base
from app.db.models import UserRole
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture()
def db_session(tmp_path) -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    original_upload_dir = settings.upload_dir
    original_generated_dir = settings.generated_dir
    original_llm_provider = settings.llm_provider
    original_llm_base_url = settings.llm_base_url
    original_llm_api_key = settings.llm_api_key
    original_llm_model = settings.llm_model
    original_analysis_llm_enabled = settings.analysis_llm_enabled
    original_external_ai_providers_enabled = settings.external_ai_providers_enabled
    original_external_ai_data_processing_confirmed = settings.external_ai_data_processing_confirmed
    original_web_search_provider = settings.web_search_provider
    original_external_web_search_enabled = settings.external_web_search_enabled
    original_official_source_fetch_enabled = settings.official_source_fetch_enabled
    original_web_search_max_results = settings.web_search_max_results
    original_web_search_timeout_seconds = settings.web_search_timeout_seconds
    original_demo_access_enabled = settings.demo_access_enabled
    original_rate_limit_enabled = settings.rate_limit_enabled
    original_rate_limit_window_seconds = settings.rate_limit_window_seconds
    original_rate_limit_sensitive_per_window = settings.rate_limit_sensitive_per_window
    settings.upload_dir = str(tmp_path / "uploads")
    settings.generated_dir = str(tmp_path / "generated")
    settings.llm_provider = "mock"
    settings.llm_base_url = ""
    settings.llm_api_key = ""
    settings.llm_model = ""
    settings.analysis_llm_enabled = False
    settings.external_ai_providers_enabled = False
    settings.external_ai_data_processing_confirmed = False
    settings.web_search_provider = "disabled"
    settings.external_web_search_enabled = False
    settings.official_source_fetch_enabled = False
    settings.web_search_max_results = 3
    settings.web_search_timeout_seconds = 1.0
    settings.demo_access_enabled = True
    settings.rate_limit_enabled = True
    settings.rate_limit_window_seconds = 60
    settings.rate_limit_sensitive_per_window = 1000

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        reset_rate_limits()
        session.close()
        Base.metadata.drop_all(bind=engine)
        settings.upload_dir = original_upload_dir
        settings.generated_dir = original_generated_dir
        settings.llm_provider = original_llm_provider
        settings.llm_base_url = original_llm_base_url
        settings.llm_api_key = original_llm_api_key
        settings.llm_model = original_llm_model
        settings.analysis_llm_enabled = original_analysis_llm_enabled
        settings.external_ai_providers_enabled = original_external_ai_providers_enabled
        settings.external_ai_data_processing_confirmed = original_external_ai_data_processing_confirmed
        settings.web_search_provider = original_web_search_provider
        settings.external_web_search_enabled = original_external_web_search_enabled
        settings.official_source_fetch_enabled = original_official_source_fetch_enabled
        settings.web_search_max_results = original_web_search_max_results
        settings.web_search_timeout_seconds = original_web_search_timeout_seconds
        settings.demo_access_enabled = original_demo_access_enabled
        settings.rate_limit_enabled = original_rate_limit_enabled
        settings.rate_limit_window_seconds = original_rate_limit_window_seconds
        settings.rate_limit_sensitive_per_window = original_rate_limit_sensitive_per_window


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    payload = {
        "email": "teacher@example.com",
        "password": "change-me",
        "full_name": "Docente Ábacos",
        "role": UserRole.teacher.value,
    }
    client.post("/api/auth/register", json=payload)
    response = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
