"""Complete logical response assembly and Discord-safe semantic chunking."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from llm_client import redact_text


DEFAULT_AGENT_MAX_RESPONSE_CHARS = 12000
DEFAULT_DISCORD_CHUNK_MAX_CHARS = 1800
DEFAULT_AGENT_MAX_RESPONSE_CHUNKS = 8
OMISSION_NOTICE = "응답이 길어 중복 설명 일부를 생략했습니다. 핵심 결론과 내부 출처는 유지했습니다."


@dataclass(frozen=True)
class AgentRenderedResponse:
    body: str
    source_footer: str
    chunks: tuple[str, ...]
    metadata: dict[str, Any]

    @property
    def content(self) -> str:
        return f"{self.body.rstrip()}\n\n{self.source_footer.strip()}".strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "body": self.body,
            "source_footer": self.source_footer,
            "metadata": dict(self.metadata),
            "content": self.content,
        }


def _int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def output_limits(env: dict[str, Any] | None = None) -> dict[str, int]:
    values = dict(env or {})
    return {
        "agent_max_response_chars": _int(
            values.get("HERMES_AGENT_MAX_RESPONSE_CHARS"),
            DEFAULT_AGENT_MAX_RESPONSE_CHARS,
            1000,
            50000,
        ),
        "discord_chunk_max_chars": _int(
            values.get("HERMES_DISCORD_CHUNK_MAX_CHARS"),
            DEFAULT_DISCORD_CHUNK_MAX_CHARS,
            500,
            1900,
        ),
        "agent_max_response_chunks": _int(
            values.get("HERMES_AGENT_MAX_RESPONSE_CHUNKS"),
            DEFAULT_AGENT_MAX_RESPONSE_CHUNKS,
            1,
            20,
        ),
    }


def _best_boundary(text: str, limit: int, *, minimum_ratio: float = 0.45) -> int:
    if len(text) <= limit:
        return len(text)
    floor = max(1, int(limit * minimum_ratio))
    window = text[: limit + 1]
    candidates: list[int] = []
    for pattern in (
        r"\n\s*\n",
        r"\n",
        r"(?<=[.!?。！？])\s+",
        r"(?:다|한다|입니다|됩니다|있습니다|없습니다)\.?\s+",
        r"\s+",
    ):
        positions = [match.end() for match in re.finditer(pattern, window)]
        if positions and positions[-1] >= floor:
            candidates.append(positions[-1])
            break
    return candidates[-1] if candidates else limit


def enforce_logical_response_bound(body: str, max_chars: int) -> tuple[str, bool]:
    text = str(body or "").strip()
    if len(text) <= max_chars:
        return text, False
    available = max(1, max_chars - len(OMISSION_NOTICE) - 2)
    boundary = _best_boundary(text, available)
    bounded = text[:boundary].rstrip()
    if boundary == available and bounded and not bounded[-1].isspace():
        last_space = bounded.rfind(" ")
        if last_space >= int(available * 0.45):
            bounded = bounded[:last_space].rstrip()
        elif not re.search(r"[.!?。！？]\s*$", bounded):
            bounded = ""
    return f"{bounded}\n\n{OMISSION_NOTICE}".strip(), True


def _semantic_pieces(text: str, max_chars: int) -> list[str]:
    remaining = str(text or "").strip()
    pieces: list[str] = []
    while remaining:
        if len(remaining) <= max_chars:
            pieces.append(remaining)
            break
        boundary = _best_boundary(remaining, max_chars)
        piece = remaining[:boundary].rstrip()
        if not piece:
            piece = remaining[:max_chars]
            boundary = max_chars
        pieces.append(piece)
        remaining = remaining[boundary:].lstrip()
    return pieces


def _preserve_code_fences(chunks: list[str]) -> list[str]:
    if not chunks:
        return chunks
    language = ""
    opened = False
    fixed: list[str] = []
    for index, chunk in enumerate(chunks):
        prefix = f"```{language}\n" if opened else ""
        current = prefix + chunk
        fences = list(re.finditer(r"```([A-Za-z0-9_+-]*)", chunk))
        state = opened
        active_language = language
        for match in fences:
            if state:
                state = False
                active_language = ""
            else:
                state = True
                active_language = match.group(1)
        if state and index < len(chunks) - 1:
            current = current.rstrip() + "\n```"
        fixed.append(current)
        opened = state
        language = active_language
    return fixed


def split_discord_response(
    *,
    body: str,
    source_footer: str,
    max_chunk_chars: int,
    max_chunks: int,
) -> list[str]:
    footer = str(source_footer or "").strip()
    piece_limit = max(100, max_chunk_chars - (12 if "```" in str(body or "") else 0))
    footer_chunks = _semantic_pieces(footer, max_chunk_chars) if footer else []
    footer_slots = min(len(footer_chunks), max_chunks)
    body_slots = max(1, max_chunks - footer_slots)
    body_budget = piece_limit * body_slots
    bounded_body, _ = enforce_logical_response_bound(body, body_budget)
    body_chunks = _semantic_pieces(bounded_body, piece_limit)[:body_slots]
    if footer_chunks:
        if (
            len(footer_chunks) == 1
            and body_chunks
            and len(body_chunks[-1]) + len(footer_chunks[0]) + 2 <= max_chunk_chars
        ):
            body_chunks[-1] = f"{body_chunks[-1]}\n\n{footer_chunks[0]}"
        else:
            body_chunks.extend(footer_chunks[: max_chunks - len(body_chunks)])
    return _preserve_code_fences(body_chunks)


def assemble_agent_response(
    *,
    body: str,
    source_footer: str = "",
    env: dict[str, Any] | None = None,
) -> AgentRenderedResponse:
    limits = output_limits(env)
    bounded_body, truncated = enforce_logical_response_bound(
        body, limits["agent_max_response_chars"]
    )
    chunks = split_discord_response(
        body=bounded_body,
        source_footer=source_footer,
        max_chunk_chars=limits["discord_chunk_max_chars"],
        max_chunks=limits["agent_max_response_chunks"],
    )
    guarded_chunks = [
        redact_text(chunk, max(len(chunk) + 32, limits["discord_chunk_max_chars"]))
        for chunk in chunks
    ]
    footer_separate = bool(
        source_footer
        and guarded_chunks
        and guarded_chunks[-1].strip() == str(source_footer).strip()
    )
    return AgentRenderedResponse(
        body=bounded_body,
        source_footer=str(source_footer or "").strip(),
        chunks=tuple(guarded_chunks),
        metadata={
            "logical_response_chars": len(bounded_body) + len(str(source_footer or "")),
            "response_chunk_count": len(guarded_chunks),
            "body_truncated": truncated,
            "sentence_midpoint_truncation": False,
            "source_footer_separate_chunk": footer_separate,
            "citation_validation_before_chunking": True,
            "citation_footer_preserved": bool(source_footer),
            "discord_chunking_enabled": True,
            "semantic_chunking_enabled": True,
            **limits,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        },
    )
