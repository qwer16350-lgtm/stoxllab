from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_rag_discord_output_does_not_expose_absolute_paths() -> None:
    with tempfile.TemporaryDirectory() as index_dir:
        raw_abs = str(Path(index_dir) / "NAS" / "secret" / "brand.md")
        payload = {
            "records": [
                {
                    "source_label": "Safe Brand Doc",
                    "relative_path": "safe/brand.md",
                    "absolute_path": raw_abs,
                    "file_name": "brand.md",
                    "asset_type": "document_metadata",
                    "media_type": "document",
                    "content_preview": "brand safe source",
                }
            ]
        }
        Path(index_dir, "nas_rag_index.json").write_text(json.dumps(payload), encoding="utf-8")
        result = build_company_agent_message_result("operation-brief", "!rag-search brand", env={"HERMES_RAG_INDEX_DIR": index_dir})
    content = result["response"]["content"]
    assert_true("safe/brand.md" in content, "safe relative path shown")
    assert_true(raw_abs not in content, "raw absolute path hidden")
    assert_true(str(index_dir) not in content, "raw index path hidden")
    assert_true(result["raw_nas_absolute_path_logged"] is False, "raw NAS path flag")
    assert_true(result["raw_index_absolute_path_logged"] is False, "raw index path flag")
    assert_true(result["secret_values_logged"] is False, "secret flag")


def main() -> int:
    test_rag_discord_output_does_not_expose_absolute_paths()
    print("PASS test_rag_discord_output_does_not_expose_absolute_paths")
    print("All RAG Discord path redaction tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
