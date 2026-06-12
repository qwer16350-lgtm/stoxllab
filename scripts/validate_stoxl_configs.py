#!/usr/bin/env python
"""Read-only validator for STOXL Hermes Discord Agent Organization files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


AGENTS = ["lucy", "marin", "meiko", "kasumi", "reze"]
DEPARTMENTS = ["decision_makers", "marketing_team", "operation_team", "strategy_office"]
RAG_GROUPS = ["brand", "marketing", "operation", "strategy", "shared"]
STATUSES = ["발견됨", "초안", "검토중", "수정필요", "추천", "비추천", "보류", "승인대기", "승인됨", "진행중", "완료", "폐기", "아카이브"]
APPROVAL_ACTIONS = [
    "sns_publish",
    "homepage_upload",
    "competition_submit",
    "grant_submit",
    "external_email_send",
    "price_confirm",
    "contract_confirm",
    "delivery_schedule_confirm",
    "official_brand_direction_confirm",
    "external_collaboration_condition_confirm",
]
REQUIRED_ENV_KEYS = [
    "DISCORD_BOT_TOKEN",
    "OPENAI_API_KEY",
    "DISCORD_GUILD_ID",
    "OWNER_KIM_DISCORD_ID",
    "OWNER_LEE_DISCORD_ID",
    "HERMES_CONFIG_PATH",
    "STOXL_WORKSPACE_PATH",
    "RAG_BASE_PATH",
    "STOXL_DB_ROOT",
    "STOXL_DB_ROOT_UNC",
    "STOXL_RAG_SOURCE_ROOT",
    "STOXL_RAG_SOURCE_ROOT_UNC",
    "STOXL_BRAND_SOURCE_ROOT",
    "STOXL_MARKETING_SOURCE_ROOT",
    "STOXL_OPERATION_SOURCE_ROOT",
    "STOXL_STRATEGY_SOURCE_ROOT",
    "STOXL_SHARED_SOURCE_ROOT",
]

PHASE_2_TO_6_FILES = [
    ".env.example",
    "ENV_REQUIRED.md",
    "RAG_PATHS_REQUIRED.md",
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
    "prompts/agents/lucy.md",
    "prompts/agents/marin.md",
    "prompts/agents/meiko.md",
    "prompts/agents/kasumi.md",
    "prompts/agents/reze.md",
    "discord/server_structure.dryrun.json",
    "discord/role_structure.dryrun.json",
    "discord/channel_permissions.dryrun.json",
    "discord/routing_workflow.dryrun.json",
    "discord/approval_gate.dryrun.json",
    "discord/handoff_rules.dryrun.json",
    "docs/STOXL_DISCORD_SERVER_STRUCTURE.md",
    "docs/STOXL_ROUTING_AND_WORKFLOW_SPEC.md",
    "docs/STOXL_TEST_PLAN.md",
    "tests/stoxl/routing_guardrails.dryrun.json",
    "tests/stoxl/permission_guardrails.dryrun.json",
    "tests/stoxl/approval_gate_guardrails.dryrun.json",
    "tests/stoxl/handoff_guardrails.dryrun.json",
    "tests/stoxl/rag_access_guardrails.dryrun.json",
    "tests/stoxl/tone_guardrails.dryrun.json",
    "tests/stoxl/status_transition_guardrails.dryrun.json",
]
PHASE_7_OPTIONAL_FILES = [
    "README.md",
    "docs/STOXL_HERMES_AGENT_ORG_README.md",
    "docs/STOXL_AGENT_OPERATION_HANDBOOK.md",
    "docs/STOXL_IMPLEMENTATION_PHASES.md",
    "docs/STOXL_CURRENT_DECISIONS_AND_TODOS.md",
]
PROMPT_HEADINGS = [
    "Agent Identity",
    "Core Mission",
    "Responsibilities",
    "Permission Boundaries",
    "Forbidden Actions",
    "Approval Gate Rules",
    "Routing and Handoff",
    "Report Format",
    "RAG Access Policy",
    "Tone and Expression Rules",
    "Uncertainty Handling",
    "Example Responses",
]


class Validator:
    def __init__(self, root: Path):
        self.root = root
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.passed: list[str] = []
        self.skipped: list[str] = []
        self.yaml_data: dict[str, Any] = {}
        self.json_data: dict[str, Any] = {}

    def path(self, rel: str) -> Path:
        return self.root / rel

    def error(self, msg: str) -> None:
        self.errors.append(f"[ERROR] {msg}")

    def warning(self, msg: str) -> None:
        self.warnings.append(f"[WARNING] {msg}")

    def pass_(self, msg: str) -> None:
        self.passed.append(msg)

    def skip(self, msg: str) -> None:
        self.skipped.append(msg)

    def read_text(self, rel: str) -> str:
        return self.path(rel).read_text(encoding="utf-8")

    def load_yaml_json(self) -> bool:
        try:
            import yaml  # type: ignore
        except Exception:
            self.error("PyYAML is required: pip install pyyaml")
            return False

        for rel in sorted(str(p.relative_to(self.root)).replace("\\", "/") for p in (self.root / "config/stoxl").glob("*.yaml")):
            try:
                self.yaml_data[rel] = yaml.safe_load(self.read_text(rel))
                self.pass_(f"Parsed YAML: {rel}")
            except Exception as exc:
                self.error(f"Failed to parse YAML {rel}: {exc}")

        for folder in ["discord", "tests/stoxl"]:
            for p in sorted((self.root / folder).glob("*.dryrun.json")):
                rel = str(p.relative_to(self.root)).replace("\\", "/")
                try:
                    self.json_data[rel] = json.loads(self.read_text(rel))
                    self.pass_(f"Parsed JSON: {rel}")
                except Exception as exc:
                    self.error(f"Failed to parse JSON {rel}: {exc}")
        return True

    def check_required_files(self) -> None:
        for rel in PHASE_2_TO_6_FILES:
            if not self.path(rel).exists():
                self.error(f"Missing required file: {rel}")
        for rel in PHASE_7_OPTIONAL_FILES:
            if not self.path(rel).exists():
                self.warning(f"Optional Phase 7 document missing: {rel}")
        if not any("Missing required file" in e for e in self.errors):
            self.pass_("All Phase 2-6 required files are present")

    def check_agents(self) -> None:
        agents_doc = self.yaml_data.get("config/stoxl/agents.yaml") or {}
        config_lists = self.yaml_data.get("config/stoxl/config_lists.yaml") or {}
        agents = {a.get("agent_id"): a for a in agents_doc.get("agents", []) if isinstance(a, dict)}
        missing = sorted(set(AGENTS) - set(agents))
        extra = sorted(set(agents) - set(AGENTS))
        if missing:
            self.error(f"agents.yaml missing agent_id(s): {', '.join(missing)}")
        if extra:
            self.error(f"agents.yaml has unknown agent_id(s): {', '.join(extra)}")
        if sorted(config_lists.get("agent_ids", [])) != sorted(AGENTS):
            self.error("config_lists.yaml agent_ids must match lucy, marin, meiko, kasumi, reze")
        prompt_ids = sorted(p.stem for p in (self.root / "prompts/agents").glob("*.md"))
        if prompt_ids != sorted(AGENTS):
            self.error(f"Prompt files must match agent ids. Found: {prompt_ids}")
        self._expect_handoff(agents, "marin", ["lucy"], "marin must hand off to lucy")
        self._expect_handoff(agents, "kasumi", ["meiko"], "kasumi must hand off to meiko")
        reze = agents.get("reze", {})
        if reze.get("handoff_rules", {}).get("flow") and "결정권자" not in str(reze.get("handoff_rules", {}).get("flow")):
            self.error("reze flow must report to decision makers")
        if "명령" not in " ".join(map(str, reze.get("forbidden_work", []))):
            self.error("reze forbidden_work must prohibit direct practical/team commands")

        allowed_refs = set(AGENTS) | {
            "none", "all_agents", "decision_makers", "owners", "approval", "blocked", "null",
            "relevant_senior_agent", "lucy_or_meiko_or_reze", "system_or_owner", "any_agent",
            "all", "assigned_agent", "marin_or_kasumi", "authorized_senior_or_owner",
            "decision_maker", "김태호_STOXL", "이주호_STOXL",
        }
        for rel, data in {**self.json_data, **self.yaml_data}.items():
            refs = self._collect_agent_refs(data)
            unknown = sorted(r for r in refs if r not in allowed_refs and not r.endswith("_agent"))
            if unknown:
                self.error(f"Unknown agent_id referenced in {rel}: {', '.join(unknown)}")
        self.pass_("Agent consistency checks completed")

    def _expect_handoff(self, agents: dict[str, Any], agent: str, expected: list[str], msg: str) -> None:
        outbound = agents.get(agent, {}).get("handoff_rules", {}).get("outbound_to", [])
        if not all(x in outbound for x in expected):
            self.error(msg)

    def _collect_agent_refs(self, obj: Any) -> set[str]:
        refs: set[str] = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = str(k)
                if key in {"agent", "primary_agent", "reviewer_agent", "from_agent", "to_agent", "expected_primary_agent", "expected_reviewer_agent"} or key.endswith("_agent"):
                    for item in self._as_list(v):
                        if item is not None:
                            refs.add(str(item))
                if key in {"allowed_agents", "assigned_agents", "requesting_agents", "responsible_agents"}:
                    for item in self._as_list(v):
                        refs.add(str(item))
                refs |= self._collect_agent_refs(v)
        elif isinstance(obj, list):
            for item in obj:
                refs |= self._collect_agent_refs(item)
        return refs

    def check_departments(self) -> None:
        departments = self.yaml_data.get("config/stoxl/departments.yaml", {}).get("departments", {})
        config_lists = self.yaml_data.get("config/stoxl/config_lists.yaml") or {}
        if sorted(departments.keys()) != sorted(DEPARTMENTS):
            self.error("departments.yaml must contain decision_makers, marketing_team, operation_team, strategy_office")
        agents = self.yaml_data.get("config/stoxl/agents.yaml", {}).get("agents", [])
        for agent in agents:
            dept = agent.get("department_id")
            if dept not in DEPARTMENTS:
                self.error(f"Agent {agent.get('agent_id')} has unknown department_id: {dept}")
        if sorted(config_lists.get("department_ids", [])) != sorted(DEPARTMENTS):
            self.error("config_lists.yaml department_ids must match canonical departments")
        self.pass_("Department consistency checks completed")

    def check_permissions(self) -> None:
        perms = self.yaml_data.get("config/stoxl/permissions.yaml", {}).get("agent_permissions", {})
        for agent in AGENTS:
            if perms.get(agent, {}).get("L5_External_Execute") is not False:
                self.error(f"Agent {agent} must have L5_External_Execute=false")
            if perms.get(agent, {}).get("L6_Final_Approval") is not False:
                self.error(f"Agent {agent} must have L6_Final_Approval=false")

        roles = self.json_data.get("discord/role_structure.dryrun.json", {}).get("roles", [])
        for role in roles:
            name = role.get("role_name")
            assigned_agents = role.get("assigned_agents") or []
            if name == "Decision Maker":
                if role.get("can_approve") is not True:
                    self.error("Decision Maker role must have can_approve=true")
                if role.get("can_execute_external_actions") is not False:
                    self.error("Decision Maker role must have can_execute_external_actions=false")
            if assigned_agents:
                if role.get("can_approve") is not False:
                    self.error(f"Agent role {name} must have can_approve=false")
                if role.get("can_execute_external_actions") is not False:
                    self.error(f"Agent role {name} must have can_execute_external_actions=false")

        global_policy = self.json_data.get("discord/approval_gate.dryrun.json", {}).get("global_policy", {})
        if global_policy.get("external_execution_allowed_after_approval") is not False:
            self.error("approval_gate global policy must set external_execution_allowed_after_approval=false")
        if global_policy.get("human_only_execution") is not True:
            self.error("approval_gate global policy must set human_only_execution=true")
        self.pass_("Permission consistency checks completed")

    def check_approval_gates(self) -> None:
        approval_rules = self.yaml_data.get("config/stoxl/approval_rules.yaml", {}).get("approval_rules", [])
        rules = {r.get("action_type"): r for r in approval_rules}
        gates = self.json_data.get("discord/approval_gate.dryrun.json", {}).get("approval_gates", [])
        gate_map = {g.get("action_type"): g for g in gates}
        for action in APPROVAL_ACTIONS:
            if action not in rules:
                self.error(f"approval_rules.yaml missing required action_type: {action}")
                continue
            if rules[action].get("approval_required") is not True:
                self.error(f"approval_rules.yaml action {action} must have approval_required=true")
            if action not in gate_map:
                self.error(f"approval_gate.dryrun.json missing required action_type: {action}")
                continue
            gate = gate_map[action]
            if gate.get("approval_required") is not True:
                self.error(f"approval_gate action {action} must have approval_required=true")
            if gate.get("external_execution_allowed_after_approval") is not False:
                self.error(f"approval_gate action {action} must have external_execution_allowed_after_approval=false")
            if gate.get("human_only_execution") is not True:
                self.error(f"approval_gate action {action} must have human_only_execution=true")
        self.pass_("Approval gate consistency checks completed")

    def check_channels(self) -> None:
        expected = {
            "00-결정권자": ["공지-결정사항", "대표-회의실", "최종-승인요청"],
            "10-마케팅팀": ["marketing-brief", "lucy-검토", "marin-초안", "sns-콘텐츠", "homepage"],
            "20-운영팀": ["operation-brief", "meiko-검토", "kasumi-리서치", "공모전-지원사업", "일정-마감관리"],
            "30-전략기획실": ["reze-전략기획", "brand-rag", "new-business", "product-ideas"],
            "90-archive": ["완료된-안건", "보류된-안건", "폐기된-안건"],
        }
        yaml_channels = self._channels_from_yaml()
        server_channels = self._channels_from_server()
        for category, channels in expected.items():
            if sorted(yaml_channels.get(category, [])) != sorted(channels):
                self.error(f"discord_channels.yaml channel list mismatch for {category}")
            if sorted(server_channels.get(category, [])) != sorted(channels):
                self.error(f"server_structure.dryrun.json channel list mismatch for {category}")
        all_channels = {c for channels in expected.values() for c in channels}
        for rel in ["discord/routing_workflow.dryrun.json", "discord/handoff_rules.dryrun.json"]:
            refs = self._collect_channel_refs(self.json_data.get(rel, {}))
            unknown = sorted(c for c in refs if c not in all_channels and c not in {"lucy-검토 또는 최종-승인요청", "marketing-brief 또는 대표-회의실", "대표-회의실 or relevant team brief"})
            if unknown:
                self.error(f"Unknown channel referenced in {rel}: {', '.join(unknown)}")
        self.pass_("Discord channel consistency checks completed")

    def _channels_from_yaml(self) -> dict[str, list[str]]:
        data = self.yaml_data.get("config/stoxl/discord_channels.yaml", {})
        out: dict[str, list[str]] = {}
        for cat in data.get("categories", []):
            out[cat.get("category")] = [c.get("channel_name") for c in cat.get("channels", [])]
        return out

    def _channels_from_server(self) -> dict[str, list[str]]:
        data = self.json_data.get("discord/server_structure.dryrun.json", {})
        out: dict[str, list[str]] = {}
        for cat in data.get("categories", []):
            out[cat.get("category_name")] = [c.get("channel_name") for c in cat.get("channels", [])]
        return out

    def _collect_channel_refs(self, obj: Any) -> set[str]:
        refs: set[str] = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                if str(k) in {"final_report_channel", "target_channel", "expected_final_channel", "channel", "expected_channel"}:
                    if v is not None:
                        refs.add(str(v))
                refs |= self._collect_channel_refs(v)
        elif isinstance(obj, list):
            for item in obj:
                refs |= self._collect_channel_refs(item)
        return refs

    def check_routing_handoff(self) -> None:
        routes = {r.get("route_id"): r for r in self.json_data.get("discord/routing_workflow.dryrun.json", {}).get("routes", [])}
        expected_routes = {
            "sns_post_draft": ("marin", "lucy", "최종-승인요청"),
            "homepage_copy_draft": ("marin", "lucy", None),
            "competition_search": ("kasumi", "meiko", "meiko-검토"),
            "grant_or_competition_decision": ("meiko", None, "최종-승인요청"),
            "strategy_product_idea": ("reze", None, "대표-회의실"),
        }
        for route_id, (primary, reviewer, channel) in expected_routes.items():
            route = routes.get(route_id)
            if not route:
                self.error(f"Missing route in routing_workflow.dryrun.json: {route_id}")
                continue
            if route.get("primary_agent") != primary:
                self.error(f"Route {route_id} primary_agent must be {primary}")
            if reviewer is not None and route.get("reviewer_agent") != reviewer:
                self.error(f"Route {route_id} reviewer_agent must be {reviewer}")
            if channel is not None and route.get("final_report_channel") != channel:
                self.error(f"Route {route_id} final_report_channel must be {channel}")
        reze_opinion = routes.get("strategy_review_of_marketing_or_operation", {})
        if "direct_order_to_team" not in reze_opinion.get("forbidden_shortcuts", []):
            self.error("Reze marketing/operation opinion route must forbid direct_order_to_team")

        handoffs = {h.get("handoff_id"): h for h in self.json_data.get("discord/handoff_rules.dryrun.json", {}).get("handoffs", [])}
        for hid in [
            "marin_to_lucy_for_review",
            "lucy_to_decision_makers_for_approval",
            "kasumi_to_meiko_for_review",
            "meiko_to_decision_makers_for_approval",
            "reze_to_decision_makers_for_strategy_report",
            "reze_to_lucy_for_marketing_strategy_opinion",
            "reze_to_meiko_for_operation_strategy_opinion",
        ]:
            if hid not in handoffs:
                self.error(f"Missing required handoff: {hid}")
        self.pass_("Routing and handoff consistency checks completed")

    def check_rag(self) -> None:
        rag = self.yaml_data.get("config/stoxl/rag_access.yaml", {})
        groups = rag.get("canonical_source_groups", [])
        if sorted(groups) != sorted(RAG_GROUPS):
            self.error("rag_access.yaml canonical_source_groups must be brand, marketing, operation, strategy, shared")
        if re.search(r"(?<![A-Za-z])operations(?![A-Za-z])", self._stringify({rel: data for rel, data in self.yaml_data.items() if rel.startswith("config/")})):
            self.error("Config files must use canonical 'operation', not 'operations'")
        expected = {
            "lucy": ["brand", "marketing", "shared"],
            "marin": ["brand", "marketing", "shared"],
            "meiko": ["operation", "shared"],
            "kasumi": ["operation", "shared"],
            "reze": ["brand", "marketing", "operation", "strategy", "shared"],
        }
        access = rag.get("agent_access", {})
        for agent, groups_expected in expected.items():
            actual = access.get(agent, {}).get("allowed_sources", [])
            if sorted(actual) != sorted(groups_expected):
                self.error(f"RAG allowed_sources for {agent} must be {groups_expected}")
        policy = rag.get("external_data_sources", {}).get("policy", {})
        if policy.get("copy_originals_into_repo") is not False:
            self.error("rag_access.yaml must prohibit copying original DB/RAG files into repo")
        exposure = rag.get("sensitive_data_exclusion", {}).get("exposure_policy", {})
        if exposure.get("tokens_passwords_api_keys") != "forbidden":
            self.error("rag_access.yaml must forbid token/password/API key exposure")
        self.pass_("RAG access consistency checks completed")

    def check_status(self) -> None:
        status_yaml = [s.get("display_name") for s in self.yaml_data.get("config/stoxl/status_tags.yaml", {}).get("status_tags", [])]
        config_status = self.yaml_data.get("config/stoxl/config_lists.yaml", {}).get("status_tags", [])
        if status_yaml != STATUSES:
            self.error("status_tags.yaml must contain canonical statuses in order")
        if config_status != STATUSES:
            self.error("config_lists.yaml status_tags must contain canonical statuses in order")
        guard = self.json_data.get("tests/stoxl/status_transition_guardrails.dryrun.json", {})
        guard_text = self._stringify(guard)
        for phrase in ["후임이 직접 승인됨", "승인대기 없이 승인됨", "완료 후에는 아카이브", "폐기 후에는 아카이브"]:
            if phrase not in guard_text:
                self.error(f"status_transition_guardrails.dryrun.json missing core block test phrase: {phrase}")
        self.pass_("Status tag consistency checks completed")

    def check_prompts(self) -> None:
        risky = ["외부 실행 가능", "승인 없이 게시", "승인 없이 제출", "토큰을 출력", "API key를 출력", "비밀번호를 출력"]
        for agent in AGENTS:
            rel = f"prompts/agents/{agent}.md"
            if not self.path(rel).exists():
                continue
            text = self.read_text(rel)
            for heading in PROMPT_HEADINGS:
                if heading not in text:
                    self.error(f"{rel} missing prompt section heading: {heading}")
            for phrase in risky:
                for line_no, line in enumerate(text.splitlines(), 1):
                    if phrase in line and not any(marker in line for marker in ["금지", "하지", "불가", "Cannot", "Do not", "No "]):
                        self.warning(f"Potential risky phrase in {rel}:{line_no}: {phrase}")
        self.pass_("Prompt file consistency checks completed")

    def check_env(self) -> None:
        if self.path(".env").exists():
            self.warning("Real .env file exists; this project expects only .env.example in current phase")
        if not self.path(".env.example").exists():
            self.error("Missing .env.example")
            return
        env = self._parse_env_example(self.read_text(".env.example"))
        for key in REQUIRED_ENV_KEYS:
            if key not in env:
                self.error(f".env.example missing required key: {key}")
        if env.get("STOXL_WORKSPACE_PATH") != r"C:\tmp\STOXL_LAB":
            self.error(r".env.example must include STOXL_WORKSPACE_PATH=C:\tmp\STOXL_LAB")
        for key in ["STOXL_DB_ROOT", "STOXL_RAG_SOURCE_ROOT"]:
            if key in env and not env[key].startswith("Z:\\"):
                self.warning(f"{key} should keep a Z:\\TODO-style mapped-drive placeholder")
        for key in ["STOXL_DB_ROOT_UNC", "STOXL_RAG_SOURCE_ROOT_UNC"]:
            if key in env and not env[key].startswith("\\\\NAS\\"):
                self.warning(f"{key} should keep a \\\\NAS\\... UNC placeholder")
        for key in ["DISCORD_BOT_TOKEN", "OPENAI_API_KEY", "DISCORD_GUILD_ID", "OWNER_KIM_DISCORD_ID", "OWNER_LEE_DISCORD_ID"]:
            value = env.get(key, "")
            if value and "TODO" not in value:
                self.warning(f"{key} in .env.example does not look like a TODO placeholder")
        self.pass_(".env.example consistency checks completed")

    def _parse_env_example(self, text: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
        return out

    def _stringify(self, obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True)

    def _as_list(self, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def result(self) -> dict[str, Any]:
        return {
            "summary": {
                "root": str(self.root),
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
                "passed_count": len(self.passed),
                "skipped_count": len(self.skipped),
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "passed_checks": self.passed,
            "skipped_checks": self.skipped,
            "next_actions": self.next_actions(),
        }

    def next_actions(self) -> list[str]:
        if not self.errors and not self.warnings:
            return ["No action required."]
        actions = []
        if self.errors:
            actions.append("Fix [ERROR] items in the referenced source files, then run the validator again.")
        if self.warnings:
            actions.append("Review [WARNING] items; warnings do not fail the validator.")
        actions.append("Do not let this validator modify files automatically; apply fixes manually in the appropriate phase.")
        return actions


def find_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "config/stoxl").exists() and (candidate / "docs/planning").exists():
            return candidate
    return current


def print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("STOXL config validation")
    print(f"Root: {summary['root']}")
    print(f"Errors: {summary['error_count']} | Warnings: {summary['warning_count']} | Passed: {summary['passed_count']} | Skipped: {summary['skipped_count']}")
    for title, key in [("Errors", "errors"), ("Warnings", "warnings"), ("Skipped", "skipped_checks")]:
        items = result[key]
        if items:
            print(f"\n{title}:")
            for item in items:
                print(f"- {item}")
    if result["passed_checks"]:
        print("\nPassed checks:")
        for item in result["passed_checks"]:
            print(f"- {item}")
    print("\nNext actions:")
    for item in result["next_actions"]:
        print(f"- {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate STOXL Hermes config, prompts, dry-run JSON, and docs.")
    parser.add_argument("--root", help="Repository root. Defaults to auto-detection from current working directory.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else find_root(Path.cwd())
    validator = Validator(root)
    validator.check_required_files()
    yaml_ready = validator.load_yaml_json()
    if yaml_ready:
        validator.check_agents()
        validator.check_departments()
        validator.check_permissions()
        validator.check_approval_gates()
        validator.check_channels()
        validator.check_routing_handoff()
        validator.check_rag()
        validator.check_status()
        validator.check_prompts()
        validator.check_env()
    result = validator.result()

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
