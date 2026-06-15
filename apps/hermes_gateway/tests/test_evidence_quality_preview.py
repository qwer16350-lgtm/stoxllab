from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from evidence_quality_preview import build_evidence_quality_preview, render_evidence_quality_preview_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_quality_checks() -> None:
    report = build_evidence_quality_preview()
    assert_true(report["citation_sufficiency_checked"] is True, "Citation checked")
    assert_true(report["duplicate_evidence_checked"] is True, "Duplicate checked")
    assert_true(report["stale_doc_suspicion_checked"] is True, "Stale checked")
    assert_true(report["relative_paths_only"] is True, "Relative only")
    assert_true(report["full_content_included"] is False, "No full content")


def test_disabled_targets() -> None:
    report = build_evidence_quality_preview()
    assert_true(report["ready_for_llm_prompt"] is False, "LLM false")
    assert_true(report["ready_for_embedding"] is False, "Embedding false")
    assert_true(report["ready_for_external_sources"] is False, "External false")
    assert_true(report["ready_for_discord_send"] is False, "Discord false")


def test_finding_shape_and_sensitive_values() -> None:
    report = build_evidence_quality_preview()
    finding = report["quality_findings"][0]
    assert_true(finding["citation_sufficient"] is True, "Citation sufficient")
    assert_true(finding["duplicate_suspected"] is False, "No duplicate")
    assert_true(finding["stale_doc_suspected"] is False, "No stale")
    text = json.dumps(report, ensure_ascii=False)
    assert_true("sk-" not in text.lower() and not LONG_NUMBER_RE.search(text), "No sensitive values")


def test_markdown() -> None:
    assert_true("Evidence Quality" in render_evidence_quality_preview_markdown(build_evidence_quality_preview()), "Markdown renders")


def main() -> int:
    for test in [test_quality_checks, test_disabled_targets, test_finding_shape_and_sensitive_values, test_markdown]:
        test()
        print(f"PASS {test.__name__}")
    print("All evidence quality preview tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
