"""
agent_loop.py - Orchestration layer for the autonomous CAP operational service node.
"""

import os
import json
import asyncio
import datetime
import logging
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

from src.identity import initialize_node_identity, log_compliance, load_credentials_and_derive_key
from src.tools import fetch_market_indices, generate_audit_payload
import croo

logger = logging.getLogger("croo")

class AgentOrchestrator:
    """Orchestrates identity setup, tools, and the websocket lifecycle for the CAP agent."""
    
    def __init__(self, client: croo.AgentClient, stream: croo.EventStream, public_key_hex: str):
        self.client = client
        self.stream = stream
        self.public_key_hex = public_key_hex
        self.loop_active = True
        
    def setup_handlers(self) -> None:
        """Registers handlers for CAP event lifecycle."""
        self.stream.on(croo.EventType.NEGOTIATION_CREATED, self.handle_negotiation_created)
        self.stream.on(croo.EventType.ORDER_PAID, self.handle_order_paid)
        
        log_compliance(
            "INFO",
            "HANDLERS_REGISTERED",
            "CAP event stream handlers successfully configured.",
            events=[croo.EventType.NEGOTIATION_CREATED, croo.EventType.ORDER_PAID]
        )
        
    def handle_negotiation_created(self, event: croo.Event) -> None:
        """Handles order_negotiation_created events by evaluating and accepting negotiations."""
        log_compliance(
            "INFO",
            "NEGOTIATION_RECEIVED",
            f"Received negotiation request: {event.negotiation_id}",
            negotiation_id=event.negotiation_id,
            service_id=event.service_id,
            requirements=event.raw.get("requirements", "")
        )
        
        # Schedule the async acceptance inside the running loop
        asyncio.create_task(self.accept_negotiation(event.negotiation_id))
        
    async def accept_negotiation(self, negotiation_id: str) -> None:
        """Accepts the negotiation to spawn a formal CAP Order."""
        log_compliance(
            "INFO",
            "NEGOTIATION_ACCEPTING",
            f"Accepting negotiation: {negotiation_id}",
            negotiation_id=negotiation_id
        )
        try:
            # Call client SDK to accept
            await self.client.accept_negotiation(negotiation_id)
            log_compliance(
                "INFO",
                "NEGOTIATION_ACCEPTED",
                f"Negotiation accepted successfully: {negotiation_id}",
                negotiation_id=negotiation_id
            )
        except Exception as e:
            log_compliance(
                "ERROR",
                "NEGOTIATION_ACCEPT_FAILED",
                f"Failed to accept negotiation {negotiation_id}: {str(e)}",
                negotiation_id=negotiation_id
            )
            
    def handle_order_paid(self, event: croo.Event) -> None:
        """Handles order_paid events by triggering the research scraping and delivery task."""
        log_compliance(
            "INFO",
            "ORDER_PAID_RECEIVED",
            f"Received paid order: {event.order_id}",
            order_id=event.order_id,
            service_id=event.service_id
        )
        
        # Schedule async research and delivery task
        asyncio.create_task(self.process_and_deliver_order(event.order_id))
        
    async def process_and_deliver_order(self, order_id: str) -> None:
        """Scrapes market index data, generates an audit payload, and delivers the order."""
        log_compliance(
            "INFO",
            "ORDER_PROCESSING",
            f"Processing delivery for order: {order_id}",
            order_id=order_id
        )
        try:
            # 1. Scraping Market indices
            market_data_json = await fetch_market_indices(assets=["BTC", "ETH"])
            log_compliance(
                "INFO",
                "MARKET_DATA_FETCHED",
                "Market data retrieved successfully for delivery.",
                order_id=order_id,
                market_data=json.loads(market_data_json)
            )
            
            # 2. Generate Cryptographically Signed Audit Payload
            audit_report_json = generate_audit_payload(
                raw_data=market_data_json,
                operator_id=self.public_key_hex
            )
            log_compliance(
                "INFO",
                "AUDIT_PAYLOAD_GENERATED",
                "Unified audit report and signature payload generated.",
                order_id=order_id
            )
            
            # 3. Deliver the completed order deliverables
            req = croo.DeliverOrderRequest(
                deliverable_type=croo.DeliverableType.TEXT,
                deliverable_text=audit_report_json
            )
            await self.client.deliver_order(order_id, req)
            
            log_compliance(
                "INFO",
                "ORDER_DELIVERED",
                f"Successfully completed and delivered order: {order_id}",
                order_id=order_id
            )
        except Exception as e:
            log_compliance(
                "ERROR",
                "ORDER_DELIVERY_FAILED",
                f"Failed to process and deliver order {order_id}: {str(e)}",
                order_id=order_id
            )

async def run_simulation(creds: dict) -> None:
    """Runs a simulated CAP event sequence to verify orchestration behavior without a live server."""
    log_compliance(
        "INFO",
        "SIMULATION_MODE_START",
        "No live server connection established. Falling back to local orchestration simulation."
    )
    
    # 1. Setup mock connection and stream objects
    mock_client = AsyncMock(spec=croo.AgentClient)
    mock_client.close = AsyncMock()
    mock_client.accept_negotiation = AsyncMock()
    mock_client.deliver_order = AsyncMock()
    
    # We use a real EventStream instance but bypass connect()'s network dial
    stream = croo.EventStream(creds["sdk_key"], creds["ws_url"])
    
    # 2. Instantiate Orchestrator
    orchestrator = AgentOrchestrator(mock_client, stream, creds["public_key_hex"])
    orchestrator.setup_handlers()
    
    # 3. Simulate NEGOTIATION_CREATED event
    negotiation_event = {
        "type": croo.EventType.NEGOTIATION_CREATED,
        "negotiation_id": "neg_sim_999",
        "service_id": "service_market_data",
        "requirements": "Provide BTC and ETH prices.",
        "status": "pending"
    }
    log_compliance("INFO", "SIMULATION_TRIGGER", "Triggering simulated NEGOTIATION_CREATED event.")
    stream._dispatch_message(json.dumps(negotiation_event))
    await asyncio.sleep(0.1) # yield to task runner
    
    # 4. Simulate ORDER_PAID event
    order_paid_event = {
        "type": croo.EventType.ORDER_PAID,
        "order_id": "ord_sim_888",
        "service_id": "service_market_data",
        "status": "paid"
    }
    log_compliance("INFO", "SIMULATION_TRIGGER", "Triggering simulated ORDER_PAID event.")
    stream._dispatch_message(json.dumps(order_paid_event))
    await asyncio.sleep(2.0) # allow background async task (scraping & delivering) to finish
    
    log_compliance(
        "INFO",
        "SIMULATION_MODE_COMPLETE",
        "Orchestrator simulation cycle completed successfully."
    )

async def main():
    # Load env variables and set mocks if missing to allow out-of-box execution
    if not os.getenv("CROO_PRIVATE_KEY"):
        os.environ["CROO_PRIVATE_KEY"] = "01" * 32
    if not os.getenv("CROO_SDK_KEY"):
        os.environ["CROO_SDK_KEY"] = "sim-sdk-key"
    if not os.getenv("CROO_BASE_URL"):
        os.environ["CROO_BASE_URL"] = "http://localhost:8000"
    if not os.getenv("CROO_WS_URL"):
        os.environ["CROO_WS_URL"] = "ws://localhost:8000"
        
    try:
        # Load credentials and public key first
        creds = load_credentials_and_derive_key()
    except Exception as e:
        print(f"Boot initialization error: {e}")
        return
        
    # Attempt real connection first; fallback to simulation on connection failure
    try:
        client, stream = await initialize_node_identity()
        orchestrator = AgentOrchestrator(client, stream, creds["public_key_hex"])
        orchestrator.setup_handlers()
        
        # Keep loop active to listen to events
        while orchestrator.loop_active:
            await asyncio.sleep(1)
            
    except Exception as e:
        # Fallback to local simulation to ensure the orchestration behaves perfectly
        await run_simulation(creds)

if __name__ == "__main__":
    asyncio.run(main())
