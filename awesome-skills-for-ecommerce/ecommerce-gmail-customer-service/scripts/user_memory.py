#!/usr/bin/env python3
"""Merge redacted, structured customer-service preferences into user_memory.md."""
import argparse, json, os, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BEGIN, END = "<!-- ECS_MEMORY_JSON_BEGIN -->", "<!-- ECS_MEMORY_JSON_END -->"
MEMORY = (Path(os.environ.get("OPENCLAW_STATE_DIR", Path.home()/".openclaw")) / "ecommerce-gmail-customer-service" / "user_memory.md")

def load():
    text = MEMORY.read_text(encoding="utf-8")
    body = text.split(BEGIN,1)[1].split(END,1)[0].strip().removeprefix("```json").removesuffix("```").strip()
    return text, json.loads(body)
def write(text, data):
    replacement = f"{BEGIN}\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```\n{END}"
    tmp = MEMORY.with_suffix(".tmp"); tmp.write_text(text.split(BEGIN,1)[0] + replacement + text.split(END,1)[1], encoding="utf-8"); os.chmod(tmp,0o600); os.replace(tmp,MEMORY)
def unique(values): return list(dict.fromkeys(v for v in values if v))
def merge(args):
    text, data = load(); update=json.loads(Path(args.input).read_text(encoding="utf-8")); now=datetime.now(timezone.utc).isoformat()
    profile=update.get("style_profile",{}); target=data.setdefault("style_profile", {"status":"not_reviewed","items":[]})
    if profile.get("status"): target["status"]=profile["status"]
    for item in profile.get("items",[]):
        key=item.get("key");
        if not key: raise SystemExit("style item requires key")
        existing=next((x for x in target["items"] if x.get("key")==key),None)
        if existing: existing.update({k:v for k,v in item.items() if v is not None})
        else: target["items"].append(item)
    plans=data.setdefault("handling_playbooks",[])
    for item in update.get("handling_playbooks",[]):
        key=f"{item.get('intent_id','')}::{item.get('scenario_key','')}"
        if "::"==key or not all(key.split("::")): raise SystemExit("playbook requires intent_id and scenario_key")
        existing=next((x for x in plans if f"{x.get('intent_id')}::{x.get('scenario_key')}"==key),None)
        if existing:
            for field in ("handling_steps","preferred_phrasing","avoid_phrasing","constraints","observation_ids"):
                existing[field]=unique(existing.get(field,[])+item.get(field,[]))
            existing.update({k:v for k,v in item.items() if k not in {"handling_steps","preferred_phrasing","avoid_phrasing","constraints","observation_ids"} and v is not None})
        else: plans.append(item)
    if "history_learning" in update: data["history_learning"].update(update["history_learning"])
    data["updated_at"]=now; write(text,data); print(json.dumps({"updated":True,"playbooks":len(plans)}))
if __name__=="__main__":
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True); m=s.add_parser("merge");m.add_argument("--input",required=True);m.set_defaults(func=merge); a=p.parse_args();a.func(a)
