"""Discord logging redaction helpers.

The actual Discord runtime can emit library logs before application reports are
printed. These filters keep token-like values, raw Discord IDs, session IDs,
and raw content out of console/log output.
"""

from __future__ import annotations

import logging
import re
from typing import Iterable


SESSION_ID_RE = re.compile(r"(?i)(session\s+id\s*[:=]\s*)([A-Za-z0-9._-]+)")
TOKEN_RE = re.compile(r"(?i)(bot\s+)?token\s*[:=]\s*\S+|bearer\s+\S+|xoxb-[A-Za-z0-9._-]+|mfa\.[A-Za-z0-9._-]+|sk-[A-Za-z0-9._-]+")
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
RAW_CONTENT_RE = re.compile(r"(?i)(content|message_content|raw_content)\s*[:=]\s*[^,\n\r]+")


def redact_discord_log_text(text: str) -> str:
    redacted = SESSION_ID_RE.sub(r"\1[REDACTED_SESSION_ID]", str(text))
    redacted = TOKEN_RE.sub("[REDACTED_SECRET]", redacted)
    redacted = LONG_ID_RE.sub("[REDACTED_DISCORD_ID]", redacted)
    redacted = RAW_CONTENT_RE.sub(r"\1=[REDACTED_CONTENT]", redacted)
    return redacted


class DiscordLogRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        record.msg = redact_discord_log_text(message)
        record.args = ()
        return True


def install_discord_logging_redaction(*, suppress_gateway_info: bool = True, logger_names: Iterable[str] | None = None) -> None:
    names = tuple(logger_names or ("discord", "discord.gateway", "discord.client", "discord.http"))
    for name in names:
        logger = logging.getLogger(name)
        if not any(isinstance(item, DiscordLogRedactionFilter) for item in logger.filters):
            logger.addFilter(DiscordLogRedactionFilter())
        if suppress_gateway_info and name == "discord.gateway" and logger.level in (logging.NOTSET, logging.DEBUG, logging.INFO):
            logger.setLevel(logging.WARNING)
