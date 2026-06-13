import os
import unittest
import json
import sys
import asyncio

# Add src to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.composability import (
    delegate_to_counterparty,
    AGENT_DIRECTORY,
    InvalidCounterpartyError,
    InsufficientUSDCBalanceError
)
import src.composability as composability

class TestComposability(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Reset mock balance
        composability.MOCK_USDC_BALANCE = 100.0

    async def test_delegate_to_counterparty_success(self):
        agent_addr = AGENT_DIRECTORY["FactChecker"] # 0xFactCheckerAgentAddress
        result = await delegate_to_counterparty(
            agent_address=agent_addr,
            service_id="service_fact_check",
            requirements="Verify historical market price data.",
            payment_amount=15.0
        )
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["counterparty_address"], agent_addr)
        self.assertEqual(result["price_usdc"], 15.0)
        self.assertEqual(composability.MOCK_USDC_BALANCE, 85.0)

    async def test_delegate_to_counterparty_invalid_address(self):
        invalid_addr = "0xUnknownAgentAddress"
        with self.assertRaises(InvalidCounterpartyError):
            await delegate_to_counterparty(
                agent_address=invalid_addr,
                service_id="service_fact_check",
                requirements="Verify data.",
                payment_amount=10.0
            )

    async def test_delegate_to_counterparty_insufficient_balance(self):
        agent_addr = AGENT_DIRECTORY["GasOptimizer"] # 0xGasOptimizerAgentAddress
        # Exceeds the initial 100.0 USDC mock balance
        with self.assertRaises(InsufficientUSDCBalanceError):
            await delegate_to_counterparty(
                agent_address=agent_addr,
                service_id="service_gas_opt",
                requirements="Optimize transaction fees.",
                payment_amount=150.0
            )

if __name__ == "__main__":
    unittest.main()
