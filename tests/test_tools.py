import os
import unittest
import json
import sys
import asyncio
from unittest.mock import patch, AsyncMock

# Add src to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools import fetch_market_indices, generate_audit_payload

class TestTools(unittest.TestCase):

    def test_fetch_market_indices_default(self):
        # We need an event loop to run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            res_str = loop.run_until_complete(fetch_market_indices())
            res = json.loads(res_str)
            
            # Verify defaults are present
            self.assertIn("BTC", res)
            self.assertIn("ETH", res)
            self.assertIn("SOL", res)
            self.assertIn("price", res["BTC"])
            self.assertIn("volume_24h", res["BTC"])
        finally:
            loop.close()

    def test_fetch_market_indices_custom(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            res_str = loop.run_until_complete(fetch_market_indices(assets=["BTC"]))
            res = json.loads(res_str)
            
            self.assertIn("BTC", res)
            self.assertNotIn("ETH", res)
            self.assertNotIn("SOL", res)
        finally:
            loop.close()

    def test_generate_audit_payload(self):
        raw_data = "some analytical information"
        operator = "operator_node_1"
        res_str = generate_audit_payload(raw_data, operator, {"X-Custom": "value"})
        res = json.loads(res_str)
        
        self.assertEqual(res["operator_id"], operator)
        self.assertIn("=== COMPLIANCE AUDIT REPORT ===", res["content"])
        self.assertEqual(res["verification"]["algorithm"], "HMAC-SHA256")
        self.assertEqual(res["verification"]["headers"]["X-Custom"], "value")
        self.assertTrue(len(res["verification"]["signature_tag"]) > 0)

    def test_generate_audit_payload_invalid(self):
        with self.assertRaises(ValueError):
            generate_audit_payload("", "operator")
        with self.assertRaises(ValueError):
            generate_audit_payload("data", "")

if __name__ == "__main__":
    unittest.main()
