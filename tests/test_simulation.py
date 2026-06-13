import os
import unittest
import sys
import asyncio
from unittest.mock import patch, AsyncMock

# Add src to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation import (
    BUYER_WALLETS,
    execute_autonomous_job,
    run_multi_buyer_simulation
)

class TestSimulationHarness(unittest.IsolatedAsyncioTestCase):

    def test_multi_wallet_registry_length(self):
        # Must define an array of exactly 5 unique mock Web3 addresses
        self.assertEqual(len(BUYER_WALLETS), 5)
        self.assertEqual(len(set(BUYER_WALLETS)), 5)
        for address in BUYER_WALLETS:
            self.assertTrue(address.startswith("0x"))

    @patch("src.simulation.fetch_market_indices", new_callable=AsyncMock)
    @patch("src.simulation.generate_audit_payload")
    async def test_execute_autonomous_job_success(self, mock_generate, mock_fetch):
        mock_fetch.return_value = '{"BTC": {"price": 64000.0, "volume_24h": 1000000.0}}'
        mock_generate.return_value = '{"report": "mock_report"}'
        
        result = await execute_autonomous_job(
            buyer_address="0xTestBuyer",
            task_id="task_001",
            payment_amount=10.0,
            agent_public_key="04test"
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["buyer_address"], "0xTestBuyer")
        self.assertEqual(result["revenue_usdc"], 10.0)

    @patch("src.simulation.execute_autonomous_job", new_callable=AsyncMock)
    async def test_run_multi_buyer_simulation(self, mock_job):
        mock_job.side_effect = [
            {"status": "success", "buyer_address": BUYER_WALLETS[0], "revenue_usdc": 10.0},
            {"status": "success", "buyer_address": BUYER_WALLETS[1], "revenue_usdc": 15.0},
            {"status": "success", "buyer_address": BUYER_WALLETS[2], "revenue_usdc": 20.0},
            {"status": "success", "buyer_address": BUYER_WALLETS[3], "revenue_usdc": 25.0},
            {"status": "success", "buyer_address": BUYER_WALLETS[4], "revenue_usdc": 30.0},
        ]
        
        with patch("src.simulation.log_compliance") as mock_log:
            await run_multi_buyer_simulation()
            
            # Verify simulation summary contains expected keys
            summary_called = False
            for call in mock_log.call_args_list:
                args, kwargs = call
                if args[1] == "SIMULATION_SUMMARY":
                    summary_called = True
                    self.assertEqual(kwargs["total_successful_deliveries"], 5)
                    self.assertEqual(kwargs["unique_addresses_serviced"], 5)
                    self.assertEqual(kwargs["total_simulated_usdc_revenue"], 100.0)
                    self.assertEqual(kwargs["total_attempted"], 5)
            self.assertTrue(summary_called)

if __name__ == "__main__":
    unittest.main()
