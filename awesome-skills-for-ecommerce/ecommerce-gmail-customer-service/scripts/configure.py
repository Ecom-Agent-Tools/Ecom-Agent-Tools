#!/usr/bin/env python3
"""Manage runtime configuration without modifying immutable skill defaults."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
DISCLOSURE = "This email is automatically processed by AI. If manual processing is required, please include the words 'requires manual processing' in your reply."
DEFAULTS = {
    "config": ASSETS_DIR / "default-config.json",
    "system-prompt": ASSETS_DIR / "default-system-prompt.md",
    "workflow": ASSETS_DIR / "default-workflow.md",
    "persona": ASSETS_DIR / "default-persona.md",
    "user-memory": ASSETS_DIR / "default-user-memory.md",
}
RUNTIME_NAMES = {
    "config": "config.json",
    "system-prompt": "system-prompt.md",
    "workflow": "workflow.md",
    "persona": "persona.md",
    "user-memory": "user_memory.md",
}


def runtime_dir() -> Path:
    state_override = os.environ.get("OPENCLAW_STATE_DIR")
    state_root = (
        Path(state_override).expanduser()
        if state_override
        else Path.home() / ".openclaw"
    )
    return state_root / "ecommerce-gmail-customer-service"


def runtime_path(kind: str) -> Path:
    return runtime_dir() / RUNTIME_NAMES[kind]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = target.with_suffix(target.suffix + ".tmp")
    shutil.copyfile(source, temporary)
    os.chmod(temporary, 0o600)
    os.replace(temporary, target)


def atomic_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def merge_missing(target: dict, defaults: dict) -> bool:
    """Add new safe defaults without replacing any configured value."""
    changed = False
    for key, value in defaults.items():
        if key not in target:
            target[key] = value
            changed = True
        elif isinstance(value, dict) and isinstance(target[key], dict):
            changed = merge_missing(target[key], value) or changed
    return changed


def upgrade_runtime_config() -> bool:
    config_path = runtime_path("config")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    defaults = json.loads(DEFAULTS["config"].read_text(encoding="utf-8"))
    changed = merge_missing(config, defaults)
    if (
        isinstance(config.get("version"), int)
        and config["version"] < defaults["version"]
    ):
        config["version"] = defaults["version"]
        changed = True
    if changed:
        atomic_json(config_path, config)
    return changed


def protect_baseline() -> None:
    """Make the shipped recovery source read-only at install/runtime, not in Git."""
    try:
        os.chmod(DEFAULTS["system-prompt"], 0o444)
    except OSError as exc:
        raise SystemExit(
            f"Unable to protect the default system prompt baseline: {exc}"
        ) from exc


def ensure_initialized() -> None:
    missing = [name for name in RUNTIME_NAMES if not runtime_path(name).exists()]
    if missing:
        raise SystemExit(
            "The running configuration has not been initialized or is incomplete:"
            + ", ".join(missing)
            + ". Please run python3 scripts/configure.py init first"
        )


def init_runtime(_: argparse.Namespace) -> None:
    protect_baseline()
    destination = runtime_dir()
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(destination, 0o700)
    created = []
    kept = []
    for kind, source in DEFAULTS.items():
        target = runtime_path(kind)
        if target.exists():
            kept.append(str(target))
            continue
        atomic_copy(source, target)
        created.append(str(target))
    try:
        upgraded = upgrade_runtime_config()
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Unable to safely upgrade the running config: {exc}") from exc
    print(f"Running directory: {destination}")
    for path in created:
        print(f"Created: {path}")
    for path in kept:
        print(f"Existing file reserved: {path}")
    if upgraded:
        print(
            "Added newly introduced safe defaults to config.json without replacing configured values"
        )
    print("Default sending mode: draft_only")
    print(
        "Next step: Review config.json, system-prompt.md, workflow.md, persona.md, and user_memory.md, then run verify."
    )


def read_config() -> dict:
    ensure_initialized()
    try:
        return json.loads(runtime_path("config").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Unable to read running configuration: {exc}") from exc


def print_status(args: argparse.Namespace) -> None:
    destination = runtime_dir()
    initialized = all(runtime_path(name).exists() for name in RUNTIME_NAMES)
    payload = {
        "skill_dir": str(SKILL_DIR),
        "runtime_dir": str(destination),
        "initialized": initialized,
        "files": {name: str(runtime_path(name)) for name in RUNTIME_NAMES},
        "immutable_baseline": str(DEFAULTS["system-prompt"]),
    }
    if initialized:
        config = read_config()
        payload.update(
            {
                "store_name": config.get("store_name", ""),
                "config_version": config.get("version"),
                "gmail_account": config.get("gmail", {}).get("account", ""),
                "commerce_provider": config.get("commerce", {}).get(
                    "provider", "unconfigured"
                ),
                "storefront_url": config.get("storefront", {}).get("url", ""),
                "storefront_status": config.get("storefront", {}).get(
                    "status", "unconfigured"
                ),
                "store_discovery_file": config.get("storefront", {}).get(
                    "discovery_file", ""
                ),
                "store_last_discovered_at": config.get("storefront", {}).get(
                    "last_discovered_at"
                ),
                "send_mode": config.get("automation", {}).get("send_mode", "unknown"),
                "ai_disclosure": config.get("automation", {})
                .get("ai_disclosure", {})
                .get("enabled"),
                "learning_enabled": config.get("learning", {}).get("enabled", False),
            }
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        if key == "files":
            print("Run file:")
            for name, path in value.items():
                print(f"  {name}: {path}")
        else:
            print(f"{key}: {value}")


def resolve_named_path(name: str) -> Path:
    if name in RUNTIME_NAMES:
        return runtime_path(name)
    if name == "default-system-prompt":
        return DEFAULTS["system-prompt"]
    if name == "runtime":
        return runtime_dir()
    if name == "store-discovery":
        return runtime_dir() / "store-discovery.json"
    raise SystemExit(f"Unknown path name: {name}")


def print_path(args: argparse.Namespace) -> None:
    if args.name in RUNTIME_NAMES:
        ensure_initialized()
    print(resolve_named_path(args.name))


def edit_runtime(args: argparse.Namespace) -> None:
    if args.name not in RUNTIME_NAMES:
        raise SystemExit(
            "Only running copies can be edited: config, system-prompt, workflow, persona, or user-memory. The default baseline is not editable."
        )
    ensure_initialized()
    editor_text = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
    editor = shlex.split(editor_text)
    if not editor:
        raise SystemExit("EDITOR/VISUAL configuration is empty")
    completed = subprocess.run([*editor, str(runtime_path(args.name))], check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    print(f"Edited: {runtime_path(args.name)}")
    print("Please run python3 scripts/configure.py verify")


def set_disclosure(args: argparse.Namespace) -> None:
    config = read_config()
    automation = config.setdefault("automation", {})
    disclosure = automation.setdefault("ai_disclosure", {})
    disclosure["enabled"] = args.value == "on"
    disclosure["text"] = DISCLOSURE
    atomic_json(runtime_path("config"), config)
    print(f"AI statement: {'open' if disclosure['enabled'] else 'closed'}")
    print(DISCLOSURE)


def set_learning(args: argparse.Namespace) -> None:
    config = read_config()
    learning = config.setdefault("learning", {})
    enabled = args.value == "on"
    learning["enabled"] = enabled
    learning["consent_granted_at"] = (
        datetime.now(timezone.utc).isoformat() if enabled else None
    )
    atomic_json(runtime_path("config"), config)
    print(f"Learning: {'enabled' if enabled else 'disabled'}")
    if enabled:
        print(
            "Only use this after the owner has explicitly agreed to the 30-day, customer-service-only, redacted learning scope."
        )


def set_storefront_status(args: argparse.Namespace) -> None:
    config = read_config()
    storefront = config.setdefault("storefront", {})
    if args.value == "confirmed":
        url = storefront.get("url")
        discovery_path = Path(
            storefront.get("discovery_file") or resolve_named_path("store-discovery")
        )
        if not url or not discovery_path.is_file():
            raise SystemExit(
                "Run scripts/discover_store.py with the merchant-supplied URL before confirming the storefront"
            )
        storefront["status"] = "confirmed"
        message = f"Confirmed public storefront: {url}"
    else:
        storefront.update(
            {
                "status": "none",
                "url": "",
                "discovery_file": "",
                "last_discovered_at": None,
            }
        )
        message = "Recorded: this merchant has no public storefront"
    atomic_json(runtime_path("config"), config)
    print(message)


def restore_runtime(args: argparse.Namespace) -> None:
    if args.name not in {"system-prompt", "workflow", "persona"}:
        raise SystemExit("restore only supports system-prompt, workflow or persona")
    ensure_initialized()
    target = runtime_path(args.name)
    backup_dir = runtime_dir() / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = backup_dir / f"{target.name}.{timestamp}.bak"
    atomic_copy(target, backup)
    atomic_copy(DEFAULTS[args.name], target)
    print(f"Backed up: {backup}")
    print(f"Restored from read-only baseline: {target}")


def verify_runtime(_: argparse.Namespace) -> None:
    protect_baseline()
    ensure_initialized()
    errors = []
    prompt = runtime_path("system-prompt").read_text(encoding="utf-8")
    workflow = runtime_path("workflow").read_text(encoding="utf-8")
    persona = runtime_path("persona").read_text(encoding="utf-8")
    rule_numbers = [int(value) for value in re.findall(r"\[R(\d{3})\]", prompt)]
    if len(rule_numbers) < 100:
        errors.append(
            f"The running version system prompt words only have {len(rule_numbers)} numbering rules, at least 100 are required"
        )
    if len(rule_numbers) != len(set(rule_numbers)):
        errors.append(
            "There is a duplicate rule number in the running version system prompt word"
        )
    required_workflow = [
        "Phase 1",
        "Phase 2",
        "Phase 3",
        "Phase 4",
        "complete orders",
        "Activities",
        "Policy",
    ]
    for marker in required_workflow:
        if marker not in workflow:
            errors.append(f"The running version of the workflow is missing: {marker}")
    if not persona.strip():
        errors.append("Run version user is set to empty")
    config = read_config()
    if config.get("version") != 3:
        errors.append(
            "config.version must be 3; run python3 scripts/configure.py init to add new safe defaults"
        )
    send_mode = config.get("automation", {}).get("send_mode")
    if send_mode not in {"draft_only", "auto_send"}:
        errors.append("automation.send_mode must be draft_only or auto_send")
    disclosure = config.get("automation", {}).get("ai_disclosure", {})
    if disclosure.get("text") != DISCLOSURE:
        errors.append(
            "AI statement text has been rewritten; please restore the specified original text"
        )
    if not isinstance(disclosure.get("enabled"), bool):
        errors.append("ai_disclosure.enabled must be a Boolean value")
    learning = config.get("learning", {})
    if not isinstance(learning.get("enabled"), bool):
        errors.append("learning.enabled must be a Boolean value")
    storefront = config.get("storefront", {})
    if storefront.get("status") not in {
        "unconfigured",
        "discovered",
        "confirmed",
        "none",
    }:
        errors.append(
            "storefront.status must be unconfigured, discovered, confirmed, or none"
        )
    if not isinstance(storefront.get("discovery_enabled", False), bool):
        errors.append("storefront.discovery_enabled must be a Boolean value")
    if storefront.get("respect_robots_txt") is not True:
        errors.append("storefront.respect_robots_txt must remain true")
    if storefront.get("public_sources_only") is not True:
        errors.append("storefront.public_sources_only must remain true")
    storefront_url = storefront.get("url", "")
    if storefront.get("status") in {"discovered", "confirmed"} and not storefront_url:
        errors.append(
            "A discovered or confirmed storefront must include storefront.url"
        )
    if storefront.get("status") == "none" and storefront_url:
        errors.append("storefront.url must be empty when storefront.status is none")
    if storefront_url:
        discovery_path = Path(
            storefront.get("discovery_file") or resolve_named_path("store-discovery")
        )
        if not discovery_path.is_file():
            errors.append(
                "A storefront URL is configured but store-discovery.json is missing; run scripts/discover_store.py again"
            )
        else:
            try:
                discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
                if discovery.get("public_sources_only") is not True:
                    errors.append(
                        "store-discovery.json is not marked public_sources_only"
                    )
                if discovery.get("storefront_url") != storefront_url:
                    errors.append(
                        "The configured storefront URL does not match store-discovery.json"
                    )
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"Unable to read store-discovery.json: {exc}")
    memory = runtime_path("user-memory").read_text(encoding="utf-8")
    if "ECS_MEMORY_JSON_BEGIN" not in memory or "ECS_MEMORY_JSON_END" not in memory:
        errors.append("user_memory.md is missing its managed-memory markers")
    manifest_path = ASSETS_DIR / "baseline-manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = manifest.get("default-system-prompt.md")
        if expected and sha256(DEFAULTS["system-prompt"]) != expected:
            errors.append(
                "The hash of the read-only default system prompt word is inconsistent with the release baseline"
            )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Verification passed: {len(rule_numbers)} system rules")
    print(f"Send mode: {send_mode}")
    print(f"AI statement: {'open' if disclosure['enabled'] else 'closed'}")
    print(f"Running directory: {runtime_dir()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Configuring a running copy of the e-commerce Gmail customer service skill"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init", help="Create missing run configuration, do not overwrite existing files"
    )
    init_parser.set_defaults(func=init_runtime)

    status_parser = subparsers.add_parser(
        "status", help="Display path and non-sensitive configuration status"
    )
    status_parser.add_argument("--json", action="store_true")
    status_parser.set_defaults(func=print_status)

    path_parser = subparsers.add_parser("path", help="Display the specified file path")
    path_parser.add_argument(
        "name",
        choices=[*RUNTIME_NAMES, "default-system-prompt", "runtime", "store-discovery"],
    )
    path_parser.set_defaults(func=print_path)

    edit_parser = subparsers.add_parser(
        "edit", help="Open running copy with safe argument list"
    )
    edit_parser.add_argument("name", choices=list(RUNTIME_NAMES))
    edit_parser.set_defaults(func=edit_runtime)

    set_parser = subparsers.add_parser("set", help="Set controlled options")
    set_parser.add_argument("setting", choices=["disclosure", "learning"])
    set_parser.add_argument("value", choices=["on", "off"])
    set_parser.set_defaults(
        func=lambda args: (
            set_disclosure(args) if args.setting == "disclosure" else set_learning(args)
        )
    )

    storefront_parser = subparsers.add_parser(
        "storefront", help="Confirm a discovered storefront or record that none exists"
    )
    storefront_parser.add_argument("value", choices=["confirmed", "none"])
    storefront_parser.set_defaults(func=set_storefront_status)

    restore_parser = subparsers.add_parser(
        "restore", help="Restore running files from read-only baseline after backup"
    )
    restore_parser.add_argument(
        "name", choices=["system-prompt", "workflow", "persona"]
    )
    restore_parser.set_defaults(func=restore_runtime)

    verify_parser = subparsers.add_parser(
        "verify", help="Verify running copy and read-only baseline"
    )
    verify_parser.set_defaults(func=verify_runtime)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if (
        getattr(args, "setting", None) not in {None, "disclosure", "learning"}
        and args.command == "set"
    ):
        raise SystemExit("Unknown setting")
    args.func(args)


if __name__ == "__main__":
    main()
