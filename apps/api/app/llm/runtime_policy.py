import ipaddress
import os
from urllib.parse import urlparse

from app.core.config import settings
from app.llm.schemas import AIProviderConfig, ProviderId

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
EXTERNAL_API_PROVIDERS = {"openai", "gemini", "anthropic"}


def is_serverless_runtime() -> bool:
    return os.getenv("VERCEL") == "1" or bool(os.getenv("VERCEL_ENV"))


def effective_provider_config(provider_id: ProviderId) -> AIProviderConfig:
    if provider_id == "mock":
        return AIProviderConfig(provider_id="mock", mode="local")
    if provider_id == "ollama":
        return AIProviderConfig(
            provider_id="ollama",
            mode="local",
            base_url=settings.ollama_base_url,
            model=settings.llm_model or None,
        )
    if provider_id == "openai":
        return AIProviderConfig(
            provider_id="openai",
            mode="api",
            base_url=settings.llm_base_url or "https://api.openai.com/v1",
            api_key=settings.llm_api_key or None,
            model=settings.llm_model or None,
        )
    if provider_id == "openai_compatible":
        return AIProviderConfig(
            provider_id="openai_compatible",
            mode="api",
            base_url=settings.llm_base_url or None,
            api_key=settings.llm_api_key or None,
            model=settings.llm_model or None,
        )
    if provider_id == "gemini":
        return AIProviderConfig(
            provider_id="gemini",
            mode="api",
            base_url=settings.llm_base_url or None,
            api_key=settings.llm_api_key or None,
            model=settings.llm_model or None,
        )
    if provider_id == "anthropic":
        return AIProviderConfig(
            provider_id="anthropic",
            mode="api",
            base_url=settings.llm_base_url or None,
            api_key=settings.llm_api_key or None,
            model=settings.llm_model or None,
        )
    raise ValueError("Proveedor LLM no soportado.")


def assert_provider_runtime_allowed(config: AIProviderConfig) -> None:
    if config.provider_id == "mock":
        return

    if config.provider_id == "ollama":
        if is_serverless_runtime():
            raise ValueError(
                "Ollama local solo está disponible cuando el backend se ejecuta en el mismo entorno local que Ollama."
            )
        _assert_safe_base_url(config.base_url or settings.ollama_base_url, allow_local=True)
        return

    if config.provider_id in EXTERNAL_API_PROVIDERS:
        _assert_external_ai_enabled()

    if config.base_url:
        if config.provider_id == "openai_compatible" and _requires_external_ai_gate(config.base_url):
            _assert_external_ai_enabled()
        _assert_safe_base_url(config.base_url, allow_local=not is_serverless_runtime())


def _requires_external_ai_gate(base_url: str) -> bool:
    parsed = urlparse(base_url)
    if not parsed.hostname:
        return True
    return not _is_local_or_private_host(parsed.hostname)


def _assert_external_ai_enabled() -> None:
    if not settings.external_ai_providers_enabled:
        raise ValueError(
            "Los proveedores externos de IA estan bloqueados. Activa EXTERNAL_AI_PROVIDERS_ENABLED=true solo tras revisar RGPD y contratos."
        )
    if not settings.external_ai_data_processing_confirmed:
        raise ValueError(
            "Falta confirmacion RGPD para IA externa. Activa EXTERNAL_AI_DATA_PROCESSING_CONFIRMED=true cuando exista base legal y contrato de tratamiento."
        )


def _assert_safe_base_url(base_url: str, *, allow_local: bool) -> None:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Endpoint de IA no permitido.")
    if is_serverless_runtime() and parsed.scheme != "https":
        raise ValueError("En despliegues remotos solo se permiten endpoints de IA HTTPS públicos.")
    if not allow_local and _is_local_or_private_host(parsed.hostname):
        raise ValueError("El backend remoto no puede llamar a endpoints locales o privados.")


def _is_local_or_private_host(hostname: str) -> bool:
    normalized = hostname.strip("[]").lower()
    if normalized in LOCAL_HOSTS or normalized.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(normalized)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast


def safe_provider_error(exc: Exception) -> str:
    message = str(exc)
    safe_messages = (
        "Ollama local solo está disponible",
        "Endpoint de IA no permitido",
        "endpoints de IA HTTPS públicos",
        "endpoints locales o privados",
        "proveedores externos de IA estan bloqueados",
        "confirmacion RGPD para IA externa",
    )
    if any(fragment in message for fragment in safe_messages):
        return message
    return "No se pudo completar la operación con el proveedor de IA. Revisa la configuración sin exponer claves."
