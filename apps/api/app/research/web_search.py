from __future__ import annotations

from abc import ABC, abstractmethod
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.research.schemas import SearchResult


class WebSearchProvider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, max_results: int | None = None) -> list[SearchResult]:
        raise NotImplementedError


class DisabledSearchProvider(WebSearchProvider):
    name = "disabled"

    async def search(self, query: str, max_results: int | None = None) -> list[SearchResult]:
        return []


class DuckDuckGoSearchProvider(WebSearchProvider):
    """No-key development provider using DuckDuckGo HTML results.

    This is useful for local pilots, but production should use a contractual API provider.
    """

    name = "duckduckgo"

    async def search(self, query: str, max_results: int | None = None) -> list[SearchResult]:
        limit = max_results or settings.web_search_max_results
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
            )
        }
        async with httpx.AsyncClient(timeout=settings.web_search_timeout_seconds, headers=headers) as client:
            response = await client.get("https://html.duckduckgo.com/html/", params={"q": query})
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[SearchResult] = []
        for node in soup.select(".result"):
            link = node.select_one(".result__a")
            if link is None:
                continue
            title = link.get_text(" ", strip=True)
            href = self._clean_duckduckgo_url(link.get("href", ""))
            snippet = node.select_one(".result__snippet")
            if not title or not href:
                continue
            results.append(
                SearchResult(
                    title=title,
                    url=href,
                    snippet=snippet.get_text(" ", strip=True) if snippet else "",
                    source="DuckDuckGo",
                )
            )
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def _clean_duckduckgo_url(url: str) -> str:
        parsed = urlparse(url)
        if "duckduckgo.com" in parsed.netloc and parsed.query:
            target = parse_qs(parsed.query).get("uddg", [""])[0]
            if target:
                return unquote(target)
        return url


class TavilySearchProvider(WebSearchProvider):
    name = "tavily"

    async def search(self, query: str, max_results: int | None = None) -> list[SearchResult]:
        if not settings.tavily_api_key:
            raise RuntimeError("TAVILY_API_KEY es obligatorio cuando WEB_SEARCH_PROVIDER=tavily.")
        payload = {
            "query": query,
            "search_depth": "basic",
            "max_results": max_results or settings.web_search_max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        headers = {"Authorization": f"Bearer {settings.tavily_api_key}"}
        async with httpx.AsyncClient(timeout=settings.web_search_timeout_seconds, headers=headers) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
        data = response.json()
        return [
            SearchResult(
                title=item.get("title") or item.get("url") or "Resultado",
                url=item.get("url") or "",
                snippet=item.get("content") or "",
                source="Tavily",
            )
            for item in data.get("results", [])
            if item.get("url")
        ]


class BraveSearchProvider(WebSearchProvider):
    name = "brave"

    async def search(self, query: str, max_results: int | None = None) -> list[SearchResult]:
        if not settings.brave_search_api_key:
            raise RuntimeError("BRAVE_SEARCH_API_KEY es obligatorio cuando WEB_SEARCH_PROVIDER=brave.")
        headers = {"X-Subscription-Token": settings.brave_search_api_key}
        params = {"q": query, "count": max_results or settings.web_search_max_results}
        async with httpx.AsyncClient(timeout=settings.web_search_timeout_seconds, headers=headers) as client:
            response = await client.get("https://api.search.brave.com/res/v1/web/search", params=params)
            response.raise_for_status()
        data = response.json()
        return [
            SearchResult(
                title=item.get("title") or item.get("url") or "Resultado",
                url=item.get("url") or "",
                snippet=item.get("description") or "",
                source="Brave",
            )
            for item in data.get("web", {}).get("results", [])
            if item.get("url")
        ]


def get_web_search_provider(provider_name: str | None = None) -> WebSearchProvider:
    selected = (provider_name or settings.web_search_provider).lower()
    if selected in {"disabled", "none", "off"}:
        return DisabledSearchProvider()
    if not settings.external_web_search_enabled:
        return DisabledSearchProvider()
    if selected == "duckduckgo":
        return DuckDuckGoSearchProvider()
    if selected == "tavily":
        return TavilySearchProvider()
    if selected == "brave":
        return BraveSearchProvider()
    raise ValueError(f"Proveedor de búsqueda web no soportado: {selected}")
