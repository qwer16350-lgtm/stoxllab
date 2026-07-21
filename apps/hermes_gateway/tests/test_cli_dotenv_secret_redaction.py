from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from runtime_dotenv import load_cli_repo_root_dotenv


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_dotenv_loader_report_does_not_expose_secret_values() -> None:
    fake_secret = "fake-secret-value-for-redaction-test"
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        cli = repo / "apps" / "hermes_gateway" / "cli.py"
        cli.parent.mkdir(parents=True, exist_ok=True)
        cli.write_text("# fake cli path\n", encoding="utf-8")
        (repo / ".env").write_text(
            "\n".join(
                [
                    f"DISCORD_BOT_TOKEN={fake_secret}",
                    "DISCORD_GUILD_ID=123456789012345678",
                    "OPENROUTER_API_KEY=fake-openrouter-secret",
                ]
            ),
            encoding="utf-8",
        )
        report = load_cli_repo_root_dotenv(cli, {})
    encoded = json.dumps(report, ensure_ascii=False)
    assert_true(fake_secret not in encoded, "discord token not in report")
    assert_true("fake-openrouter-secret" not in encoded, "api key not in report")
    assert_true("123456789012345678" not in encoded, "raw Discord ID not in report")
    assert_true(report["discord_token_present"] is True, "presence boolean only")
    assert_true(report["discord_token_value_logged"] is False, "token value not logged")
    assert_true(report["secret_values_logged"] is False, "secret flag false")
    assert_true(report["repo_root_dotenv_content_logged"] is False, "dotenv content not logged")


def main() -> int:
    test_dotenv_loader_report_does_not_expose_secret_values()
    print("PASS test_dotenv_loader_report_does_not_expose_secret_values")
    print("All CLI dotenv secret redaction tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
