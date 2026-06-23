from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import detect_meiko_recent_kasumi_context_intent, normalize_recent_agent_alias


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_kasumi_aliases_normalize_to_kasumi() -> None:
    for alias in ("Kasumi", "kasumi", "KASUMI", "카스미", "KASUMI_STOXL", "kasumi_stoxl"):
        assert_true(normalize_recent_agent_alias(alias) == "kasumi", f"{alias} normalizes")


def test_meiko_recent_context_intent_accepts_korean_and_english_aliases() -> None:
    assert_true(
        detect_meiko_recent_kasumi_context_intent("meiko-검토", "!meiko 방금 Kasumi가 찾은 지원사업 검토해줘"),
        "English alias intent",
    )
    assert_true(
        detect_meiko_recent_kasumi_context_intent("meiko-검토", "!meiko 방금 카스미가 찾은 지원사업 검토해줘"),
        "Korean alias intent",
    )
    assert_true(
        detect_meiko_recent_kasumi_context_intent("meiko-검토", "!meiko KASUMI_STOXL이 찾은 후보 판단해줘"),
        "persona alias intent",
    )


def test_fresh_web_reference_phrase_does_not_count_as_recent_context() -> None:
    assert_true(
        not detect_meiko_recent_kasumi_context_intent("meiko-검토", "!meiko 현재 신청 가능한 디자인 지원사업 검증해줘"),
        "fresh search remains web bridge eligible",
    )


def main() -> int:
    test_kasumi_aliases_normalize_to_kasumi()
    print("PASS test_kasumi_aliases_normalize_to_kasumi")
    test_meiko_recent_context_intent_accepts_korean_and_english_aliases()
    print("PASS test_meiko_recent_context_intent_accepts_korean_and_english_aliases")
    test_fresh_web_reference_phrase_does_not_count_as_recent_context()
    print("PASS test_fresh_web_reference_phrase_does_not_count_as_recent_context")
    print("All recent agent alias normalization tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
