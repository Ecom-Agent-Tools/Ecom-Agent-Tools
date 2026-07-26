"""Offline smoke tests; no Gmail, OAuth, or merchant connection is required."""
import json, os, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RuntimeTests(unittest.TestCase):
    def run(self, *args, **kwargs):
        return super().run(*args, **kwargs)
    def test_runtime_and_learning_tools(self):
        with tempfile.TemporaryDirectory() as state:
            env = {**os.environ, "OPENCLAW_STATE_DIR": state}
            def call(*parts): return subprocess.run(["python3", *parts], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
            call("scripts/configure.py", "init"); call("scripts/configure.py", "verify")
            update = Path(state) / "update.json"
            update.write_text(json.dumps({"handling_playbooks":[{"intent_id":"SHIP-DELAY","scenario_key":"scanned","handling_steps":["Check scan"],"observation_ids":["offline-1"]}]}))
            call("scripts/user_memory.py", "merge", "--input", str(update))
            before, after = Path(state)/"before.txt", Path(state)/"after.txt"
            before.write_text("Order 123456 is delayed."); after.write_text("We are sorry order 123456 is delayed.")
            call("scripts/draft_learning.py", "snapshot", "--draft-id", "d1", "--thread-id", "t1", "--message-id", "m1", "--intent", "SHIP-DELAY", "--body-file", str(before))
            result = call("scripts/draft_learning.py", "compare", "--draft-id", "d1", "--body-file", str(after))
            self.assertTrue(json.loads(result.stdout)["changed"])

if __name__ == "__main__": unittest.main()
