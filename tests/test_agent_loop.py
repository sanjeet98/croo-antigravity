import os
import unittest
import json
import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent_loop import AgentOrchestrator
import croo

class TestAgentLoopOrchestration(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_client = AsyncMock(spec=croo.AgentClient)
        self.mock_client.close = AsyncMock()
        self.mock_client.accept_negotiation = AsyncMock()
        self.mock_client.deliver_order = AsyncMock()
        
        self.mock_stream = MagicMock(spec=croo.EventStream)
        self.mock_stream.on = MagicMock()
        
        self.public_key_hex = "04" + "01" * 64
        self.orchestrator = AgentOrchestrator(
            self.mock_client, 
            self.mock_stream, 
            self.public_key_hex
        )

    def test_setup_handlers(self):
        self.orchestrator.setup_handlers()
        
        # Verify handlers are registered on the stream
        self.mock_stream.on.assert_any_call(
            croo.EventType.NEGOTIATION_CREATED, 
            self.orchestrator.handle_negotiation_created
        )
        self.mock_stream.on.assert_any_call(
            croo.EventType.ORDER_PAID, 
            self.orchestrator.handle_order_paid
        )

    @patch("src.agent_loop.AgentOrchestrator.accept_negotiation", new_callable=AsyncMock)
    async def test_handle_negotiation_created(self, mock_accept):
        event = MagicMock(spec=croo.Event)
        event.negotiation_id = "neg_123"
        event.service_id = "service_test"
        event.raw = {"requirements": "Provide some test details"}
        
        self.orchestrator.handle_negotiation_created(event)
        
        # Yield execution to allow create_task to start and execute mock_accept
        await asyncio.sleep(0.01)
        mock_accept.assert_called_once_with("neg_123")

    @patch("src.agent_loop.AgentOrchestrator.process_and_deliver_order", new_callable=AsyncMock)
    async def test_handle_order_paid(self, mock_process):
        event = MagicMock(spec=croo.Event)
        event.order_id = "ord_123"
        event.service_id = "service_test"
        
        self.orchestrator.handle_order_paid(event)
        
        # Yield execution to allow create_task to start and execute mock_process
        await asyncio.sleep(0.01)
        mock_process.assert_called_once_with("ord_123")

    async def test_accept_negotiation_calls_client(self):
        await self.orchestrator.accept_negotiation("neg_123")
        self.mock_client.accept_negotiation.assert_called_once_with("neg_123")

if __name__ == "__main__":
    unittest.main()
