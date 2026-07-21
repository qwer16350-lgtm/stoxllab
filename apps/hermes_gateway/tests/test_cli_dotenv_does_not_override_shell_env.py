from __future__ import annotations

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


def fake_cli_path(repo_root: Path) -> Path:
    cli = repo_root / "apps" / "hermes_gateway" / "cli.py"
    cli.parent.mkdir(parents=True, exist_ok=True)
    cli.write_text("# fake cli path\n", encoding="utf-8")
    return cli


def test_dotenv_does_not_override_discord_bot_token_from_shell_env() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        cli = fake_cli_path(repo)
        (repo / ".env").write_text("DISCORD_BOT_TOKEN=dotenv-token\n", encoding="utf-8")
        env = {"DISCORD_BOT_TOKEN": "shell-token"}
        report = load_cli_repo_root_dotenv(cli, env)
    assert_true(report["repo_root_dotenv_loaded"] is True, "dotenv loaded")
    assert_true(env["DISCORD_BOT_TOKEN"] == "shell-token", "shell token wins")
    assert_true(report["env_override_used"] is False, "override false reported")


def test_shell_alias_wins_over_dotenv_primary_key() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        cli = fake_cli_path(repo)
        (repo / ".env").write_text("DISCORD_BOT_TOKEN=dotenv-token\n", encoding="utf-8")
        env = {"HERMES_DISCORD_BOT_TOKEN": "shell-alias-token"}
        load_cli_repo_root_dotenv(cli, env)
    assert_true(env["DISCORD_BOT_TOKEN"] == "shell-alias-token", "shell alias wins over dotenv primary")
    assert_true(env["HERMES_DISCORD_BOT_TOKEN"] == "shell-alias-token", "shell alias preserved")


def main() -> int:
    test_dotenv_does_not_override_discord_bot_token_from_shell_env()
    print("PASS test_dotenv_does_not_override_discord_bot_token_from_shell_env")
    test_shell_alias_wins_over_dotenv_primary_key()
    print("PASS test_shell_alias_wins_over_dotenv_primary_key")
    print("All CLI dotenv override tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
