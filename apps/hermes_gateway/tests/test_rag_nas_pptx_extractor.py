from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_rag_nas_index import build_nas_index, scan_nas_files


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


SLIDE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>
</p:sld>
"""


def write_pptx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as deck:
        deck.writestr("ppt/slides/slide1.xml", SLIDE_XML.format(text="Brand proposal"))
        deck.writestr("ppt/slides/slide2.xml", SLIDE_XML.format(text="STOXL launch notes"))


def test_pptx_supported_and_slide_text_indexed() -> None:
    with tempfile.TemporaryDirectory() as nas_root, tempfile.TemporaryDirectory() as index_dir:
        root = Path(nas_root)
        write_pptx(root / "deck.pptx")
        scan = scan_nas_files(dry_run=True, env={"HERMES_RAG_NAS_ROOT": nas_root})
        index = build_nas_index(allow_write=True, env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_INDEX_DIR": index_dir})
        payload = json.loads((Path(index_dir) / "nas_rag_index.json").read_text(encoding="utf-8"))
    assert_true(".pptx" in scan["supported_extensions"], "pptx supported")
    assert_true(scan["files_supported"] == 1, "pptx counted supported")
    assert_true(index["index_file_written"] is True, "index written")
    record = payload["records"][0]
    assert_true(record["extension"] == ".pptx", "pptx record")
    assert_true("[PPTX] deck.pptx" in record["content_preview"], "pptx marker")
    assert_true("Slide 1: Brand proposal" in record["content_preview"], "slide 1 text")
    assert_true("Slide 2: STOXL launch notes" in record["content_preview"], "slide 2 text")
    assert_true(index["ocr_called"] is False, "no OCR")
    assert_true(index["vision_api_called"] is False, "no vision")
    assert_true(index["llm_called"] is False, "no LLM")
    assert_true(index["external_execution"] is False, "no external")


def main() -> int:
    test_pptx_supported_and_slide_text_indexed()
    print("PASS test_pptx_supported_and_slide_text_indexed")
    print("All RAG NAS PPTX extractor tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
