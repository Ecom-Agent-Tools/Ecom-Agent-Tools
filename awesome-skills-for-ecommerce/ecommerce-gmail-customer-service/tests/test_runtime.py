"""Offline smoke tests; no Gmail, OAuth, or merchant connection is required."""

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DISCOVERY_SPEC = importlib.util.spec_from_file_location(
    "discover_store", ROOT / "scripts" / "discover_store.py"
)
discover_store = importlib.util.module_from_spec(DISCOVERY_SPEC)
assert DISCOVERY_SPEC.loader
DISCOVERY_SPEC.loader.exec_module(discover_store)


class RuntimeTests(unittest.TestCase):
    def run(self, *args, **kwargs):
        return super().run(*args, **kwargs)

    def test_runtime_and_learning_tools(self):
        with tempfile.TemporaryDirectory() as state:
            env = {**os.environ, "OPENCLAW_STATE_DIR": state}

            def call(*parts):
                return subprocess.run(
                    ["python3", *parts],
                    cwd=ROOT,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            call("scripts/configure.py", "init")
            call("scripts/configure.py", "verify")
            config_path = (
                Path(state) / "ecommerce-gmail-customer-service" / "config.json"
            )
            old_config = json.loads(config_path.read_text())
            old_config["version"] = 2
            old_config.pop("storefront")
            config_path.write_text(json.dumps(old_config))
            call("scripts/configure.py", "init")
            upgraded = json.loads(config_path.read_text())
            self.assertEqual(upgraded["version"], 3)
            self.assertTrue(upgraded["storefront"]["public_sources_only"])
            call("scripts/configure.py", "verify")
            discovery_path = (
                Path(state)
                / "ecommerce-gmail-customer-service"
                / "store-discovery.json"
            )
            discovery_path.write_text(
                json.dumps(
                    {
                        "storefront_url": "https://shop.example/",
                        "public_sources_only": True,
                    }
                )
            )
            upgraded["storefront"].update(
                {
                    "status": "discovered",
                    "url": "https://shop.example/",
                    "discovery_file": str(discovery_path),
                }
            )
            config_path.write_text(json.dumps(upgraded))
            call("scripts/configure.py", "storefront", "confirmed")
            self.assertEqual(
                json.loads(config_path.read_text())["storefront"]["status"], "confirmed"
            )
            call("scripts/configure.py", "verify")
            update = Path(state) / "update.json"
            update.write_text(
                json.dumps(
                    {
                        "handling_playbooks": [
                            {
                                "intent_id": "SHIP-DELAY",
                                "scenario_key": "scanned",
                                "handling_steps": ["Check scan"],
                                "observation_ids": ["offline-1"],
                            }
                        ]
                    }
                )
            )
            call("scripts/user_memory.py", "merge", "--input", str(update))
            before, after = Path(state) / "before.txt", Path(state) / "after.txt"
            before.write_text("Order 123456 is delayed.")
            after.write_text("We are sorry order 123456 is delayed.")
            call(
                "scripts/draft_learning.py",
                "snapshot",
                "--draft-id",
                "d1",
                "--thread-id",
                "t1",
                "--message-id",
                "m1",
                "--intent",
                "SHIP-DELAY",
                "--body-file",
                str(before),
            )
            result = call(
                "scripts/draft_learning.py",
                "compare",
                "--draft-id",
                "d1",
                "--body-file",
                str(after),
            )
            self.assertTrue(json.loads(result.stdout)["changed"])

    def test_public_storefront_parser_and_network_guard(self):
        html = """
        <html><head><title>Example Store</title>
        <script src="https://cdn.shopify.com/theme.js"></script>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "Trail Bottle",
          "sku": "TB-1",
          "url": "/products/trail-bottle",
          "offers": {"price": "24.00", "priceCurrency": "USD", "availability": "https://schema.org/InStock"}
        }
        </script></head><body>
        <p>Summer sale: save 20% today.</p>
        <a href="/policies/refund-policy">Refund policy</a>
        <a href="/products/trail-bottle">Trail Bottle</a>
        </body></html>
        """
        result = discover_store.analyze_html(html, "https://shop.example/")
        self.assertEqual(result["platform"]["name"], "shopify")
        self.assertEqual(result["products"][0]["sku"], "TB-1")
        self.assertEqual(result["policy_links"][0]["kind"], "refund")
        self.assertTrue(result["campaign_evidence"])
        with self.assertRaises(ValueError):
            discover_store.validate_public_url("http://127.0.0.1/private")


if __name__ == "__main__":
    unittest.main()
