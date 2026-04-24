from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GeoblockedError(RuntimeError):
    """Raised when Polymarket blocks the current network location."""


@dataclass(slots=True)
class SourcePayload:
    source: str
    markets: list[dict[str, Any]]
    metadata: dict[str, Any]


class JsonHttpClient:
    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def get_json(self, url: str) -> Any:
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; PolymarketBusinessResearch/0.1)",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 403:
                raise GeoblockedError(f"Received HTTP 403 from {url}") from exc
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} for {url}: {body[:300]}") from exc
        except URLError as exc:
            raise RuntimeError(f"Network error for {url}: {exc}") from exc


class PolymarketClient:
    GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
    GEOBLOCK_URL = "https://polymarket.com/api/geoblock"

    def __init__(self, http_client: JsonHttpClient | None = None) -> None:
        self.http = http_client or JsonHttpClient()

    def geoblock_status(self) -> dict[str, Any]:
        try:
            payload = self.http.get_json(self.GEOBLOCK_URL)
            if isinstance(payload, dict):
                return payload
        except Exception as exc:
            return {"blocked": None, "error": str(exc)}
        return {"blocked": None}

    def fetch_markets(self, *, closed: bool, limit: int = 40, max_pages: int = 3) -> SourcePayload:
        geoblock = self.geoblock_status()
        if geoblock.get("blocked") is True:
            country = geoblock.get("country", "unknown")
            region = geoblock.get("region", "unknown")
            raise GeoblockedError(
                f"Polymarket marked this environment as geoblocked (country={country}, region={region})."
            )

        collected: list[dict[str, Any]] = []
        after_cursor: str | None = None
        pages = 0

        while len(collected) < limit and pages < max_pages:
            page_limit = min(100, limit - len(collected))
            params = {
                "limit": page_limit,
                "closed": str(closed).lower(),
                "include_tag": "true",
                "related_tags": "true",
                "ascending": "false",
                "order": "volume24hr",
            }
            if after_cursor:
                params["after_cursor"] = after_cursor
            url = f"{self.GAMMA_BASE_URL}/markets/keyset?{urlencode(params)}"
            payload = self.http.get_json(url)
            if not isinstance(payload, dict):
                raise RuntimeError("Unexpected response shape from Polymarket market endpoint.")
            page_markets = payload.get("markets") or []
            if not isinstance(page_markets, list):
                raise RuntimeError("Polymarket payload did not include a market list.")
            collected.extend(page_markets)
            after_cursor = payload.get("next_cursor")
            pages += 1
            if not page_markets or not after_cursor:
                break

        return SourcePayload(
            source="live",
            markets=collected[:limit],
            metadata={
                "geoblock": geoblock,
                "closed": closed,
                "pages_loaded": pages,
                "limit_requested": limit,
            },
        )


class FixtureClient:
    def load(self, path: Path) -> SourcePayload:
        payload = json.loads(path.read_text(encoding="utf-8"))
        markets = payload.get("markets") or []
        metadata = payload.get("metadata") or {}
        return SourcePayload(source="fixture", markets=markets, metadata=metadata)
