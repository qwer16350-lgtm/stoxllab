from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CLI = REPO_ROOT / "apps" / "hermes_gateway" / "cli.py"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_minimal_png(path: Path, width: int, height: int) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x02\x00\x00\x00"
    )


def test_decompression_bomb_warning_is_not_printed_to_console() -> None:
    with tempfile.TemporaryDirectory() as nas_root:
        root = Path(nas_root)
        write_minimal_png(root / "huge.png", 10_000, 10_000)
        env = os.environ.copy()
        env.update({"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_MAX_IMAGE_PIXELS": "80000000"})
        result = subprocess.run(
            [sys.executable, str(CLI), "--rag-scan-nas", "--dry-run", "--json"],
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )
    assert_true(result.returncode == 0, result.stderr)
    assert_true("DecompressionBombWarning" not in result.stdout, "warning not in stdout")
    assert_true("DecompressionBombWarning" not in result.stderr, "warning not in stderr")
    assert_true("huge.png" not in result.stderr, "raw file name not leaked through warning")
    payload = json.loads(result.stdout)
    assert_true(payload["decompression_bomb_warning_suppressed"] is True, "suppression reported")
    assert_true(payload["skip_summary"]["[image_pixel_too_large]"] == 1, "bounded skip reason")
    assert_true(payload["raw_nas_absolute_path_logged"] is False, "raw path not logged")
    assert_true(payload["vision_api_called"] is False, "no vision")
    assert_true(payload["ocr_called"] is False, "no OCR")
    assert_true(payload["llm_called"] is False, "no LLM")
    assert_true(payload["embedding_called"] is False, "no embedding")
    assert_true(payload["external_execution"] is False, "no external")


def main() -> int:
    test_decompression_bomb_warning_is_not_printed_to_console()
    print("PASS test_decompression_bomb_warning_is_not_printed_to_console")
    print("All RAG NAS decompression bomb guard tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
