#!/usr/bin/env python
"""Build a read-only STOXL agent registry from config, prompts, and dry-run specs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


AGENTS = ["lucy", "marin", "meiko", "kasumi", "reze"]
PROMPTS = {agent: f"prompts/agents/{agent}.md" for agent in AGENTS}
CONFIG_FILES = [
    "config/stoxl/agents.yaml",
    "config/stoxl/departments.yaml",
    "config/stoxl/permissions.yaml",
    "config/stoxl/forbidden_actions.yaml",
    "config/stoxl/approval_rules.yaml",
    "config/stoxl/discord_channels.yaml",
    "config/stoxl/routing_rules.yaml",
    "config/stoxl/workflow_rules.yaml",
    "config/stoxl/report_formats.yaml",
    "config/stoxl/rag_access.yaml",
    "config/stoxl/notification_rules.yaml",
    "config/stoxl/status_tags.yaml",
    "config/stoxl/config_lists.yaml",
]
DRYRUN_FILES = [
    "discord/server_structure.dryrun.json",
    "discord/role_structure.dryrun.json",
    "discord/channel_permissions.dryrun.json",
    "discord/routing_workflow.dryrun.json",
    "discord/approval_gate.dryrun.json",
    "discord/handoff_rules.dryrun.json",
]
ENV_FILE = ".env.example"


class RegistryLoader:
    def __init__(self, root: Path):
        self.root = root
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.yaml_data: dict[str, Any] = {}
        self.json_data: dict[str, Any] = {}
        self.prompts: dict[str, str] = {}
        self.env: dict[str, str] = {}
        self.source_files = [ENV_FILE, *CONFIG_FILES, *PROMPTS.values(), *DRYRUN_FILES]

    def path(self, rel: str) -> Path:
        return self.root / rel

    def read_text(self, rel: str) -> str:
        return self.path(rel).read_text(encoding="utf-8")

    def load(self) -> bool:
        try:
            import yaml  # type: ignore
        except Exception:
            self.errors.append("PyYAML is required: pip install pyyaml")
            return False

        for rel in self.source_files:
            if not self.path(rel).exists():
                self.errors.append(f"Missing required source file: {rel}")

        if self.errors:
            return False

        for rel in CONFIG_FILES:
            try:
                self.yaml_data[rel] = yaml.safe_load(self.read_text(rel))
            except Exception as exc:
                self.errors.append(f"Failed to parse YAML {rel}: {exc}")

        for rel in DRYRUN_FILES:
            try:
                self.json_data[rel] = json.loads(self.read_text(rel))
            except Exception as exc:
                self.errors.append(f"Failed to parse JSON {rel}: {exc}")

        for agent, rel in PROMPTS.items():
            self.prompts[agent] = self.read_text(rel)

        self.env = self.parse_env(self.read_text(ENV_FILE))
        return not self.errors

    def parse_env(self, text: str) -> dict[str, str]:
        env: dict[str, str] = {}
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
        return env

    def build(self, agent_filter: str | None = None) -> dict[str, Any]:
        if agent_filter and agent_filter not in AGENTS:
            self.errors.append(f"Unknown agent_id: {agent_filter}")
            return {}

        agents_doc = self.yaml_data["config/stoxl/agents.yaml"]
        departments_doc = self.yaml_data["config/stoxl/departments.yaml"]
        rag_doc = self.yaml_data["config/stoxl/rag_access.yaml"]
        report_doc = self.yaml_data["config/stoxl/report_formats.yaml"]
        server_doc = self.json_data["discord/server_structure.dryrun.json"]
        routing_doc = self.json_data["discord/routing_workflow.dryrun.json"]
        approval_doc = self.json_data["discord/approval_gate.dryrun.json"]
        handoff_doc = self.json_data["discord/handoff_rules.dryrun.json"]

        selected_agents = [agent_filter] if agent_filter else AGENTS

        registry = {
            "meta": {
                "registry_type": "stoxl_agent_registry",
                "version": "phase9_dryrun",
                "root": str(self.root),
                "source_files": self.source_files,
            },
            "decision_makers": self.build_decision_makers(),
            "departments": self.build_departments(departments_doc),
            "agents": self.build_agents(agents_doc, rag_doc, report_doc, routing_doc, selected_agents),
            "channels": self.build_channels(server_doc),
            "routing": self.build_routing(routing_doc),
            "approval_gates": self.build_approval_gates(approval_doc),
            "handoff_rules": self.build_handoff_rules(handoff_doc),
            "rag_access": self.build_rag_access(rag_doc),
            "status_tags": self.build_status_tags(),
            "warnings": self.warnings,
        }
        return registry

    def build_decision_makers(self) -> list[dict[str, Any]]:
        return [
            {
                "display_name": "김태호_STOXL",
                "role": "decision_maker",
                "can_approve": True,
                "can_execute_external_actions": False,
                "env_user_id_key": "OWNER_KIM_DISCORD_ID",
            },
            {
                "display_name": "이주호_STOXL",
                "role": "decision_maker",
                "can_approve": True,
                "can_execute_external_actions": False,
                "env_user_id_key": "OWNER_LEE_DISCORD_ID",
            },
        ]

    def build_departments(self, departments_doc: dict[str, Any]) -> dict[str, Any]:
        departments = {}
        for department_id, data in departments_doc.get("departments", {}).items():
            departments[department_id] = {
                "department_id": data.get("department_id", department_id),
                "display_name": data.get("display_name"),
                "purpose": data.get("purpose"),
                "members": data.get("members", []),
                "decision_flow": data.get("decision_flow", []),
                "default_channels": data.get("default_channels", []),
            }
        return departments

    def build_agents(
        self,
        agents_doc: dict[str, Any],
        rag_doc: dict[str, Any],
        report_doc: dict[str, Any],
        routing_doc: dict[str, Any],
        selected_agents: list[str],
    ) -> dict[str, Any]:
        rag_access = rag_doc.get("agent_access", {})
        agents_by_id = {a.get("agent_id"): a for a in agents_doc.get("agents", [])}
        routing_roles = self.routing_roles_by_agent(routing_doc)
        forbidden_shortcuts = self.forbidden_shortcuts_by_agent(routing_doc)
        result = {}
        for agent_id in selected_agents:
            agent = agents_by_id.get(agent_id)
            if not agent:
                self.errors.append(f"Missing agent in agents.yaml: {agent_id}")
                continue
            prompt_path = PROMPTS[agent_id]
            result[agent_id] = {
                "agent_id": agent_id,
                "display_name": agent.get("display_name"),
                "department_id": agent.get("department_id"),
                "seniority": agent.get("seniority"),
                "reports_to": agent.get("reports_to", []),
                "reviews": agent.get("reviews", []),
                "primary_role": agent.get("primary_role"),
                "responsibilities": agent.get("responsibilities", []),
                "allowed_work": agent.get("allowed_work", []),
                "forbidden_work": agent.get("forbidden_work", []),
                "permission_levels": agent.get("permission_levels", {}),
                "final_approval_allowed": False,
                "external_execution_allowed": False,
                "approval_required_for": agent.get("approval_required_for", []),
                "default_channels": agent.get("default_channels", []),
                "rag_profile": agent.get("rag_profile", []),
                "allowed_rag_sources": rag_access.get(agent_id, {}).get("allowed_sources", []),
                "tone_profile": agent.get("tone_profile", {}),
                "handoff_rules": agent.get("handoff_rules", {}),
                "prompt_path": prompt_path,
                "system_prompt": self.prompts.get(agent_id, ""),
                "report_format": self.report_format_for_agent(agent_id, report_doc),
                "routing_roles": routing_roles.get(agent_id, []),
                "forbidden_shortcuts": forbidden_shortcuts.get(agent_id, []),
            }
        return result

    def routing_roles_by_agent(self, routing_doc: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {agent: [] for agent in AGENTS}
        for route in routing_doc.get("routes", []):
            for role_key in ["primary_agent", "reviewer_agent"]:
                agent = route.get(role_key)
                if agent in result:
                    result[agent].append({"route_id": route.get("route_id"), "role": role_key})
        return result

    def forbidden_shortcuts_by_agent(self, routing_doc: dict[str, Any]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {agent: [] for agent in AGENTS}
        for route in routing_doc.get("routes", []):
            shortcuts = route.get("forbidden_shortcuts", [])
            for agent in [route.get("primary_agent"), route.get("reviewer_agent")]:
                if agent in result:
                    result[agent].extend(shortcuts)
        return {k: sorted(set(v)) for k, v in result.items()}

    def report_format_for_agent(self, agent_id: str, report_doc: dict[str, Any]) -> dict[str, Any]:
        for name, fmt in report_doc.get("formats", {}).items():
            if agent_id in fmt.get("used_by", []):
                return {"format_id": name, **fmt}
        return {}

    def build_channels(self, server_doc: dict[str, Any]) -> dict[str, Any]:
        channels = {}
        for category in server_doc.get("categories", []):
            for channel in category.get("channels", []):
                channel_name = channel.get("channel_name")
                channels[channel_name] = {
                    "category_id": channel.get("category_id"),
                    "category_name": channel.get("category_name"),
                    "channel_id": channel.get("channel_id"),
                    "channel_name": channel_name,
                    "purpose": channel.get("purpose"),
                    "workflow_role": channel.get("workflow_role"),
                    "allowed_agents": channel.get("allowed_agents", []),
                    "allowed_humans": channel.get("allowed_humans", []),
                    "approval_relevant": channel.get("approval_relevant"),
                    "archive_rule": channel.get("archive_rule"),
                }
        return channels

    def build_routing(self, routing_doc: dict[str, Any]) -> dict[str, Any]:
        return {
            route.get("route_id"): {
                "route_id": route.get("route_id"),
                "trigger_examples": route.get("trigger_examples", []),
                "source_channel_candidates": route.get("source_channel_candidates", []),
                "primary_agent": route.get("primary_agent"),
                "reviewer_agent": route.get("reviewer_agent"),
                "final_report_channel": route.get("final_report_channel"),
                "approval_required": route.get("approval_required"),
                "required_report_format": route.get("required_report_format"),
                "allowed_next_statuses": route.get("allowed_next_statuses", []),
                "forbidden_shortcuts": route.get("forbidden_shortcuts", []),
            }
            for route in routing_doc.get("routes", [])
        }

    def build_approval_gates(self, approval_doc: dict[str, Any]) -> dict[str, Any]:
        return {
            gate.get("gate_id"): {
                "gate_id": gate.get("gate_id"),
                "action_type": gate.get("action_type"),
                "approval_required": gate.get("approval_required"),
                "approver_roles": gate.get("approver_roles", []),
                "approver_display_names": gate.get("approver_display_names", []),
                "env_user_id_keys": gate.get("env_user_id_keys", []),
                "requesting_agents": gate.get("requesting_agents", []),
                "blocked_until_approved": gate.get("blocked_until_approved"),
                "external_execution_allowed_after_approval": gate.get("external_execution_allowed_after_approval"),
                "human_only_execution": gate.get("human_only_execution"),
                "required_report_fields": gate.get("required_report_fields", []),
            }
            for gate in approval_doc.get("approval_gates", [])
        }

    def build_handoff_rules(self, handoff_doc: dict[str, Any]) -> dict[str, Any]:
        return {
            handoff.get("handoff_id"): {
                "handoff_id": handoff.get("handoff_id"),
                "from_agent": handoff.get("from_agent"),
                "to_agent": handoff.get("to_agent"),
                "condition": handoff.get("condition"),
                "required_payload": handoff.get("required_payload", []),
                "target_channel": handoff.get("target_channel"),
                "allowed_status_transition": handoff.get("allowed_status_transition", []),
                "forbidden_payload": handoff.get("forbidden_payload", []),
            }
            for handoff in handoff_doc.get("handoffs", [])
        }

    def build_rag_access(self, rag_doc: dict[str, Any]) -> dict[str, Any]:
        return {
            "external_data_sources": rag_doc.get("external_data_sources", {}),
            "canonical_source_groups": rag_doc.get("canonical_source_groups", []),
            "agent_access": rag_doc.get("agent_access", {}),
            "sensitive_data_exclusion": rag_doc.get("sensitive_data_exclusion", {}),
        }

    def build_status_tags(self) -> dict[str, Any]:
        status_doc = self.yaml_data["config/stoxl/status_tags.yaml"]
        return {
            item.get("display_name"): item
            for item in status_doc.get("status_tags", [])
        }


def find_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "config/stoxl").exists() and (candidate / "prompts/agents").exists():
            return candidate
    return current


def write_registry(registry: dict[str, Any], out: Path | None) -> None:
    text = json.dumps(registry, ensure_ascii=False, indent=2)
    if out is None:
        print(text)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only STOXL agent registry.")
    parser.add_argument("--root", help="Repository root. Defaults to auto-detection from current working directory.")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout. This is the default when --out is not used.")
    parser.add_argument("--out", help="Write registry JSON to this path. Relative paths resolve from repo root.")
    parser.add_argument("--agent", help="Only include a specific agent_id.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else find_root(Path.cwd())
    loader = RegistryLoader(root)
    if not loader.load():
        for error in loader.errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    registry = loader.build(args.agent)
    if loader.errors:
        for error in loader.errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    out_path = None
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = root / out_path
    write_registry(registry, out_path)
    if out_path is not None:
        print(f"Wrote registry: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
