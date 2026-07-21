from __future__ import annotations

import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_bot_fleet import load_agent_bot_token_presence
from company_agent_runtime import _runtime_env, build_company_agent_runtime_start_report
from runtime_dotenv import load_cli_repo_root_dotenv


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def fake_cli_path(repo_root: Path) -> Path:
    cli = repo_root / "apps" / "hermes_gateway" / "cli.py"
    cli.parent.mkdir(parents=True, exist_ok=True)
    cli.write_text("# fake cli path for repo-root resolution\n", encoding="utf-8")
    return cli


def test_loads_repo_root_dotenv_from_cli_location_not_cwd() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        cli = fake_cli_path(repo)
        (repo / ".env").write_text(
            "\n".join(
                [
                    "DISCORD_BOT_TOKEN=dotenv-main-token",
                    "HERMES_DISCORD_LUCY_BOT_TOKEN=dotenv-lucy-token",
                ]
            ),
            encoding="utf-8",
        )
        env: dict[str, str] = {}
        report = load_cli_repo_root_dotenv(cli, env)
    runtime = _runtime_env(env)
    start_report = build_company_agent_runtime_start_report(True, env, discord_dependency_available=False)
    presence = load_agent_bot_token_presence(env)
    assert_true(report["repo_root_dotenv_present"] is True, "repo .env present")
    assert_true(report["repo_root_dotenv_loaded"] is True, "repo .env loaded")
    assert_true(report["discord_token_present"] is True, "token presence only")
    assert_true(runtime["discord_token_present"] is True, "company runtime sees token")
    assert_true(start_report["discord_token_present"] is True, "start report presence only")
    assert_true(start_report["token_value_logged"] is False, "start report does not log token")
    assert_true(presence["lucy"] is True, "agent bot token loaded after dotenv")
    assert_true(report["repo_root_dotenv_path_logged"] is False, "dotenv path not logged")
    assert_true(report["repo_root_dotenv_content_logged"] is False, "dotenv content not logged")
    assert_true(report["discord_token_value_logged"] is False, "token value not logged")


def test_missing_dotenv_keeps_safe_existing_behavior() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env: dict[str, str] = {}
        report = load_cli_repo_root_dotenv(fake_cli_path(Path(tmp)), env)
    assert_true(report["repo_root_dotenv_present"] is False, "missing .env allowed")
    assert_true(report["repo_root_dotenv_loaded"] is False, "missing .env not loaded")
    assert_true(report["discord_token_present"] is False, "token still missing")


def main() -> int:
    test_loads_repo_root_dotenv_from_cli_location_not_cwd()
    print("PASS test_loads_repo_root_dotenv_from_cli_location_not_cwd")
    test_missing_dotenv_keeps_safe_existing_behavior()
    print("PASS test_missing_dotenv_keeps_safe_existing_behavior")
    print("All CLI repo-root dotenv loading tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
