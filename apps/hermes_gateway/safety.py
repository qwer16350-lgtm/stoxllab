"""Static safety rules for the fresh local Hermes Gateway skeleton."""

from __future__ import annotations

SECRET_MARKERS = (
    "api key",
    "apikey",
    "token",
    "secret",
    "password",
    "비밀번호",
    "토큰",
)

SAFETY_RULES = {
    "no_external_execution": True,
    "human_only_execution": True,
    "no_secret_output": True,
    "no_rag_source_copy": True,
    "no_unknown_agent_dispatch": True,
    "no_junior_direct_approval": True,
    "no_reze_direct_order": True,
    "no_discord_api_call": True,
}


def contains_secret_request(text: str) -> bool:
    lower = (text or "").lower()
    return any(marker in lower for marker in SECRET_MARKERS)


def safety_summary() -> dict[str, bool]:
    return dict(SAFETY_RULES)
