"""Offline smoke tests; no Gmail, OAuth, or merchant connection is required."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import discover_store
import import_browser_discovery


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

    def test_guarded_browser_discovery_import(self):
        snapshot = {
            "storefront_url": "https://shop.example/",
            "public_sources_only": True,
            "read_only": True,
            "fallback_reason": "direct_fetch_failed",
            "browser_tool": "browser",
            "robots": {
                "status": "enforced_by_browser_tool",
                "respected": True,
            },
            "platform": {
                "name": "shopify",
                "confidence": 0.9,
                "evidence": ["Shopify marker on a public page"],
            },
            "products": [
                {
                    "name": "Trail Bottle",
                    "url": "https://shop.example/products/trail-bottle",
                    "source_url": "https://shop.example/products/trail-bottle",
                    "price": "24.00",
                    "currency": "USD",
                }
            ],
            "campaigns": [
                {
                    "evidence": "Summer sale: save 20% today.",
                    "url": "https://shop.example/collections/sale",
                }
            ],
            "policies": [
                {
                    "kind": "refund",
                    "title": "Refund policy",
                    "url": "https://shop.example/policies/refund-policy",
                    "text_excerpt": "Returns are accepted within 30 days.",
                }
            ],
            "sources": [{"url": "https://shop.example/", "type": "page"}],
            "warnings": [],
        }
        normalized = import_browser_discovery.normalize_snapshot(snapshot)
        self.assertEqual(normalized["discovery_method"], "browser_fallback")
        self.assertTrue(normalized["read_only"])
        self.assertEqual(normalized["products"][0]["status"], "public_source_unverified_applicability")
        self.assertTrue(normalized["robots"]["respected"])

        cross_host = json.loads(json.dumps(snapshot))
        cross_host["policies"][0]["url"] = "https://support.example.net/refunds"
        with self.assertRaises(ValueError):
            import_browser_discovery.normalize_snapshot(cross_host)
        private_host = json.loads(json.dumps(snapshot))
        private_host["storefront_url"] = "http://127.0.0.1/"
        with self.assertRaises(ValueError):
            import_browser_discovery.normalize_snapshot(private_host)

        with tempfile.TemporaryDirectory() as state:
            env = {**os.environ, "OPENCLAW_STATE_DIR": state}
            subprocess.run(
                ["python3", "scripts/configure.py", "init"],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            input_path = Path(state) / "browser-input.json"
            input_path.write_text(json.dumps(snapshot), encoding="utf-8")
            result = subprocess.run(
                [
                    "python3",
                    "scripts/import_browser_discovery.py",
                    "--input",
                    str(input_path),
                ],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            summary = json.loads(result.stdout)
            self.assertEqual(summary["discovery_method"], "browser_fallback")
            output = Path(summary["output"])
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["platform"]["name"], "shopify")
            self.assertEqual(len(payload["products"]), 1)


if __name__ == "__main__":
    unittest.main()
