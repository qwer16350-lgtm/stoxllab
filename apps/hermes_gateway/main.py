"""Local entrypoint for the fresh STOXL Hermes Gateway skeleton."""

from __future__ import annotations

import sys
from pathlib import Path

from config import load_config
from registry_loader import load_registry, registry_summary
from safety import safety_summary


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cfg = load_config(Path(__file__).resolve())
    print("STOXL Fresh Hermes Gateway")
    print("Mode: local dry-run only; no Discord, LLM, .env, or external execution.")
    print(f"Repo root: {cfg.repo_root}")
    print(f".env.example present: {cfg.env_example_exists}")
    try:
        registry = load_registry(cfg)
        print(f"Registry summary: {registry_summary(registry)}")
    except Exception as exc:
        print(f"Registry unavailable: {exc}")
    print(f"Safety rules: {safety_summary()}")
    print("")
    print("Usage:")
    print('  python apps\\hermes_gateway\\cli.py --text "인스타 업로드 문구 초안 만들어줘" --channel "marin-초안" --author-role "Decision Maker"')
    print("  python apps\\hermes_gateway\\cli.py --event apps\\hermes_gateway\\examples\\local_message_event.json --json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
