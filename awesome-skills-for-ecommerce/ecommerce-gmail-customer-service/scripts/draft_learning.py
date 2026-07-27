#!/usr/bin/env python3
"""Store short-lived redacted AI-draft baselines and compare later revisions."""
import argparse, difflib, hashlib, json, os, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
STATE=Path(os.environ.get("OPENCLAW_STATE_DIR",Path.home()/".openclaw"))/"ecommerce-gmail-customer-service"/"draft-baselines"
CONFIG=STATE.parent/"config.json"
def redact(s): return re.sub(r"https?://\S+|[\w.+-]+@[\w.-]+|\b\d{5,}\b","[REDACTED]",s)
def path(i): return STATE/f"{i}.json"
def require_learning_consent(a):
 if not getattr(a,"confirm_owner_request",False): raise SystemExit("Saving a draft baseline requires the current owner's request and --confirm-owner-request")
 try: config=json.loads(CONFIG.read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError) as exc: raise SystemExit(f"Unable to read runtime configuration: {exc}") from exc
 learning=config.get("learning",{})
 if learning.get("enabled") is not True or not learning.get("consent_granted_at"): raise SystemExit("Saving a draft baseline requires explicitly enabled learning with recorded consent")
def snapshot(a):
    require_learning_consent(a)
    STATE.mkdir(parents=True,exist_ok=True,mode=0o700); body=redact(Path(a.body_file).read_text()); data={"draft_id":a.draft_id,"thread_id":a.thread_id,"message_id":a.message_id,"intent":a.intent,"created_at":datetime.now(timezone.utc).isoformat(),"body":body,"hash":hashlib.sha256(body.encode()).hexdigest()}; path(a.draft_id).write_text(json.dumps(data),encoding="utf-8");os.chmod(path(a.draft_id),0o600);print(json.dumps({"saved":a.draft_id}))
def compare(a):
    old=json.loads(path(a.draft_id).read_text()); new=redact(Path(a.body_file).read_text()); diff=list(difflib.unified_diff(old["body"].splitlines(),new.splitlines(),lineterm=""));print(json.dumps({"changed":old["body"]!=new,"draft_id":a.draft_id,"diff":diff}))
def finalize(a): path(a.draft_id).unlink(missing_ok=True)
def purge(a):
    cutoff=datetime.now(timezone.utc)-timedelta(days=a.days); [p.unlink() for p in STATE.glob("*.json") if datetime.fromisoformat(json.loads(p.read_text())["created_at"])<cutoff]
if __name__=="__main__":
 p=argparse.ArgumentParser();s=p.add_subparsers(dest="cmd",required=True)
 for n,f in (("snapshot",snapshot),("compare",compare),("finalize",finalize),("purge",purge)):
  x=s.add_parser(n);x.set_defaults(func=f);x.add_argument("--draft-id")
  if n=="snapshot": x.add_argument("--thread-id",required=True);x.add_argument("--message-id",required=True);x.add_argument("--intent",required=True);x.add_argument("--body-file",required=True);x.add_argument("--confirm-owner-request",action="store_true")
  if n=="compare": x.add_argument("--body-file",required=True)
  if n=="purge": x.add_argument("--days",type=int,default=7)
 a=p.parse_args();a.func(a)
