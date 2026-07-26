#!/usr/bin/env python3
"""Deterministic validation for the skill package."""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DISCLOSURE = "This email is automatically processed by AI. If manual processing is required, please include the words 'requires manual processing' in your reply."


def error(messages: list[str], message: str) -> None:
    messages.append(message)


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    result = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if line[0].isspace() or line.lstrip().startswith("-"):
            continue
        if ":" not in line:
            return {}
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def main() -> int:
    errors: list[str] = []
    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(skill_text)
    if set(frontmatter) != {"name", "description", "version", "metadata"}:
        error(
            errors,
            f"SKILL.md frontmatter must contain name, description, version, and metadata; actual keys: {sorted(frontmatter)}",
        )
    if frontmatter.get("name") != ROOT.name:
        error(errors, "Skill name is inconsistent with the directory name")
    if not re.fullmatch(
        r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?",
        frontmatter.get("version", ""),
    ):
        error(errors, "SKILL.md version must be valid semver")
    if "metadata:\n  openclaw:" not in skill_text:
        error(errors, "SKILL.md metadata must declare metadata.openclaw")
    if not (ROOT / ".clawhubignore").is_file():
        error(errors, "Missing .clawhubignore")
    for relative in ["scripts/discover_store.py", "references/storefront-discovery.md"]:
        if not (ROOT / relative).is_file():
            error(errors, f"Missing storefront discovery component: {relative}")
    if "TODO" in skill_text:
        error(errors, "SKILL.md still contains TODO")

    prompt_path = ROOT / "assets" / "default-system-prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    rules = [int(value) for value in re.findall(r"\[R(\d{3})\]", prompt)]
    if len(rules) < 100:
        error(
            errors,
            f"The default system prompt word rules are less than 100: {len(rules)}",
        )
    if rules != list(range(1, len(rules) + 1)):
        error(
            errors,
            "The default system prompt word numbers are not consecutive or do not start from R001",
        )
    if DISCLOSURE not in prompt:
        error(
            errors,
            "The default system prompt word lacks the original text of the specified AI statement",
        )
    # Git and ClawHub bundles do not preserve a portable read-only file mode.
    # configure.py applies that protection at runtime after installation.

    playbook_text = (ROOT / "references" / "reply-playbooks.md").read_text(
        encoding="utf-8"
    )
    plan_ids = set(re.findall(r"^### ([A-Z0-9-]+)｜", playbook_text, re.MULTILINE))
    if len(plan_ids) < 50:
        error(errors, f"Too few reply plans: {len(plan_ids)}")

    taxonomy_path = ROOT / "references" / "intent-taxonomy.csv"
    with taxonomy_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required_columns = {
        "l1_code",
        "l1_name",
        "l2_code",
        "l2_name",
        "l3_code",
        "l3_name",
        "plan_a",
        "plan_b",
        "plan_c",
        "risk",
    }
    if not rows:
        error(errors, "The three-level classification table is empty")
    elif set(rows[0]) != required_columns:
        error(
            errors, "The structure of the three-level classification table is incorrect"
        )
    l1_to_l2: dict[str, set[str]] = defaultdict(set)
    l2_to_l3: dict[str, set[str]] = defaultdict(set)
    seen_l3: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        l1_to_l2[row["l1_code"]].add(row["l2_code"])
        l2_to_l3[row["l2_code"]].add(row["l3_code"])
        if row["l3_code"] in seen_l3:
            error(errors, f"Level 3 code duplication: {row['l3_code']}")
        seen_l3.add(row["l3_code"])
        plans = [row["plan_a"], row["plan_b"], row["plan_c"]]
        if len(set(plans)) < 2:
            error(errors, f"Line {line_number} does not have 2–3 different replies")
        for plan in plans:
            if plan not in plan_ids:
                error(errors, f"Line {line_number} refers to an unknown plan: {plan}")
        if row["risk"] not in {"low", "medium", "high", "manual"}:
            error(
                errors, f"The risk value of row {line_number} is invalid: {row['risk']}"
            )
    if len(l1_to_l2) < 12:
        error(errors, f"Insufficient first-level classification: {len(l1_to_l2)}")
    for l1, l2s in l1_to_l2.items():
        if len(l2s) < 2:
            error(
                errors,
                f"The first-level classification {l1} is less than two second-level classifications",
            )
    for l2, l3s in l2_to_l3.items():
        if len(l3s) < 2:
            error(
                errors,
                f"Level 2 classification {l2} is less than two level 3 classifications",
            )

    workflow = (ROOT / "assets" / "default-workflow.md").read_text(encoding="utf-8")
    for marker in [
        "Phase 1",
        "Phase 2",
        "Phase 3",
        "Phase 4",
        "recently purchased",
        "complete orders",
        "Activities",
        "Policy",
    ]:
        if marker not in workflow:
            error(errors, f"Default workflow is missing: {marker}")

    onboarding = (ROOT / "references" / "onboarding.md").read_text(encoding="utf-8")
    for marker in [
        "console.cloud.google.com",
        "gog auth credentials",
        "openclaw cron add",
        "--disabled",
        "Agent name",
        "edit persona",
        "edit system-prompt",
        "edit workflow",
        "set disclosure",
        "simulation testing",
        "requires manual processing",
        "completion",
    ]:
        if marker not in onboarding:
            error(errors, f"The installation guide is missing: {marker}")

    config = json.loads(
        (ROOT / "assets" / "default-config.json").read_text(encoding="utf-8")
    )
    if config.get("version") != 3:
        error(errors, "The default configuration version must be 3")
    if config.get("automation", {}).get("send_mode") != "draft_only":
        error(errors, "The default sending mode must be draft_only")
    if config.get("automation", {}).get("ai_disclosure", {}).get("text") != DISCLOSURE:
        error(errors, "The default configuration AI declaration text is incorrect")
    storefront = config.get("storefront", {})
    if storefront.get("status") != "unconfigured":
        error(errors, "The default storefront status must be unconfigured")
    if storefront.get("discovery_enabled") is not True:
        error(errors, "Public storefront discovery must be enabled by default")
    if storefront.get("respect_robots_txt") is not True:
        error(errors, "Public storefront discovery must respect robots.txt")
    if storefront.get("public_sources_only") is not True:
        error(errors, "Public storefront discovery must be limited to public sources")
    if storefront.get("refresh_interval_hours") != 24:
        error(errors, "The default storefront refresh interval must be 24 hours")

    sources = (ROOT / "references" / "research-sources.md").read_text(encoding="utf-8")
    source_urls = re.findall(r"https://[^)\s]+", sources)
    if len(source_urls) < 15:
        error(errors, f"Insufficient research sources: {len(source_urls)}")

    openai_yaml = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if "$ecommerce-gmail-customer-service" not in openai_yaml:
        error(
            errors,
            "agents/openai.yaml default prompt does not explicitly mention Skill",
        )

    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".py", ".json", ".csv", ".yaml"}:
            text = path.read_text(encoding="utf-8")
            if "TODO" in text and path.name != "validate_skill.py":
                error(errors, f"The file still contains TODO: {path.relative_to(ROOT)}")

    if errors:
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        return 1
    print("Skill validation passed")
    print(f"system_rules={len(rules)}")
    print(f"l1_categories={len(l1_to_l2)}")
    print(f"l2_categories={len(l2_to_l3)}")
    print(f"l3_categories={len(rows)}")
    print(f"reply_playbooks={len(plan_ids)}")
    print(f"research_sources={len(source_urls)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
