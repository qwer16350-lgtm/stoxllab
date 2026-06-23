"""Low-level read-only search and page-fetch transport for company web reference."""

from __future__ import annotations

import html
import ipaddress
import json
import os
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from llm_client import redact_text


SUPPORTED_PROVIDERS = ("serper", "brave", "tavily")
TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)


def _provider_config(env: dict[str, Any] | None = None) -> tuple[str, str]:
    env_map = dict(os.environ if env is None else env)
    provider = str(env_map.get("HERMES_WEB_SEARCH_PROVIDER", "disabled") or "disabled").strip().lower()
    api_key = str(env_map.get("HERMES_WEB_SEARCH_API_KEY", "") or "")
    return provider, api_key


def _request(provider: str, api_key: str, query: str, limit: int) -> urllib.request.Request:
    if provider == "serper":
        return urllib.request.Request(
            "https://google.serper.dev/search",
            data=json.dumps({"q": query, "num": limit}).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-API-KEY": api_key, "User-Agent": "STOXL-Hermes-Reference/0.7"},
            method="POST",
        )
    if provider == "brave":
        url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode({"q": query, "count": limit})
        return urllib.request.Request(
            url,
            headers={"Accept": "application/json", "X-Subscription-Token": api_key, "User-Agent": "STOXL-Hermes-Reference/0.7"},
        )
    return urllib.request.Request(
        "https://api.tavily.com/search",
        data=json.dumps({"api_key": api_key, "query": query, "max_results": limit, "search_depth": "basic"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "STOXL-Hermes-Reference/0.7"},
        method="POST",
    )


def _parse_results(provider: str, body: dict[str, Any]) -> list[dict[str, str]]:
    if provider == "serper":
        raw_results = body.get("organic", [])
    elif provider == "brave":
        raw_results = (body.get("web") or {}).get("results", [])
    else:
        raw_results = body.get("results", [])
    parsed: list[dict[str, str]] = []
    for item in raw_results if isinstance(raw_results, list) else []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("link") or item.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            continue
        profile = item.get("profile") if isinstance(item.get("profile"), dict) else {}
        parsed.append(
            {
                "title": redact_text(str(item.get("title") or "제목 확인 필요"), 240),
                "url": url[:800],
                "snippet": redact_text(str(item.get("snippet") or item.get("description") or item.get("content") or ""), 600),
                "institution": redact_text(str(item.get("source") or profile.get("long_name") or ""), 160),
            }
        )
    return parsed


def _result(success: bool, reason: str, provider: str, results: list[dict[str, str]] | None = None) -> dict[str, Any]:
    selected = list(results or [])
    return {
        "search_succeeded": success,
        "failure_reason": reason,
        "provider": provider,
        "results": selected,
        "result_count": len(selected),
        "api_key_present": provider != "unknown" and reason != "api_key_missing",
        "api_key_value_logged": False,
        "read_only": True,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def run_readonly_web_search(
    queries: list[str],
    limit: int = 5,
    env: dict[str, Any] | None = None,
    opener: Any | None = None,
) -> dict[str, Any]:
    provider, api_key = _provider_config(env)
    if provider not in SUPPORTED_PROVIDERS:
        return _result(False, "provider_not_configured", "unknown")
    if not api_key:
        return _result(False, "api_key_missing", provider)
    collected: list[dict[str, str]] = []
    seen: set[str] = set()
    open_func = opener or urllib.request.urlopen
    try:
        for query in queries[:3]:
            with open_func(_request(provider, api_key, query, max(1, min(limit, 10))), timeout=15) as response:
                body = json.loads(response.read().decode("utf-8"))
            for item in _parse_results(provider, body if isinstance(body, dict) else {}):
                if item["url"] in seen:
                    continue
                seen.add(item["url"])
                collected.append(item)
                if len(collected) >= limit:
                    break
            if len(collected) >= limit:
                break
    except (TimeoutError, socket.timeout):
        return _result(False, "timeout", provider)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError, ValueError):
        return _result(False, "provider_exception", provider)
    if not collected:
        return _result(False, "no_results", provider)
    return _result(True, "", provider, collected)


def _public_url_allowed(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return not (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved)


def fetch_readonly_page_summary(url: str, opener: Any | None = None) -> dict[str, Any]:
    if not _public_url_allowed(url):
        return {"fetch_succeeded": False, "failure_reason": "blocked_by_policy", "read_only": True}
    request = urllib.request.Request(url, headers={"User-Agent": "STOXL-Hermes-Reference/0.7"})
    try:
        with (opener or urllib.request.urlopen)(request, timeout=15) as response:
            raw = response.read(200_000).decode("utf-8", errors="replace")
    except (TimeoutError, socket.timeout):
        return {"fetch_succeeded": False, "failure_reason": "timeout", "read_only": True}
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return {"fetch_succeeded": False, "failure_reason": "provider_exception", "read_only": True}
    text = html.unescape(TAG_RE.sub(" ", SCRIPT_RE.sub(" ", raw)))
    text = re.sub(r"\s+", " ", text).strip()
    return {
        "fetch_succeeded": True,
        "failure_reason": "",
        "summary": redact_text(text, 1800),
        "read_only": True,
        "external_execution": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
    }
