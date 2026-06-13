"""
composability.py - Agent-to-Agent (A2A) orchestration and CAP order lifecycle simulation.
"""

import os
import json
import asyncio
import datetime
import logging
from typing import Dict, Any, Optional

import croo
from src.identity import log_compliance

# Anti-sybil protocol directory (immutable tracking registry of mandatory counterparties)
AGENT_DIRECTORY = {
    "FactChecker": "0xFactCheckerAgentAddress",
    "GasOptimizer": "0xGasOptimizerAgentAddress",
    "Formatter": "0xFormatterAgentAddress"
}

# Thread-safe global mock balance for USDC operations
MOCK_USDC_BALANCE = 100.0

class InsufficientUSDCBalanceError(Exception):
    """Raised when the mock USDC balance is insufficient for delegating an order."""
    pass

class InvalidCounterpartyError(Exception):
    """Raised when the specified agent address is not in the anti-sybil registry."""
    pass

async def delegate_to_counterparty(
    agent_address: str, 
    service_id: str, 
    requirements: str, 
    payment_amount: float
) -> Dict[str, Any]:
    """
    Simulates the CAP A2A order delegation lifecycle state machine with a counterparty agent.
    
    State Machine Lifecycle:
    NegotiationCreated -> AcceptNegotiation -> OrderPaid -> DeliverOrder -> OrderCompleted
    
    Args:
        agent_address (str): The address of the target counterparty agent.
        service_id (str): The target service ID to consume.
        requirements (str): Outbound requirement details for the task.
        payment_amount (float): Payment amount in mock USDC.
        
    Returns:
        Dict[str, Any]: A verified report object containing the final CAP Order structural payload.
        
    Raises:
        InvalidCounterpartyError: If the agent address is not found in the registry.
        InsufficientUSDCBalanceError: If the mock USDC balance is less than payment_amount.
        Exception: If any error occurs during the lifecycle simulation.
    """
    global MOCK_USDC_BALANCE
    
    # 1. Verify Counterparty Address is in registry
    valid_addresses = set(AGENT_DIRECTORY.values())
    if agent_address not in valid_addresses:
        error_msg = f"Counterparty address {agent_address} is not recognized by the anti-sybil registry."
        log_compliance("ERROR", "COUNTERPARTY_INVALID", error_msg, agent_address=agent_address)
        raise InvalidCounterpartyError(error_msg)
        
    log_compliance(
        "INFO",
        "A2A_DELEGATION_START",
        f"Initiating A2A delegation lifecycle with counterparty: {agent_address}",
        agent_address=agent_address,
        service_id=service_id,
        payment_amount=payment_amount
    )
    
    # Generate unique IDs for mock entities
    negotiation_id = f"neg_a2a_{os.urandom(8).hex()}"
    order_id = f"ord_a2a_{os.urandom(8).hex()}"
    
    # 2. State: NegotiationCreated
    log_compliance(
        "INFO",
        "STATE_NEGOTIATION_CREATED",
        f"Negotiation created with counterparty: {negotiation_id}",
        negotiation_id=negotiation_id,
        status="pending",
        requirements=requirements
    )
    await asyncio.sleep(0.1) # Simulate network lag
    
    # 3. State: AcceptNegotiation
    log_compliance(
        "INFO",
        "STATE_ACCEPT_NEGOTIATION",
        f"Counterparty accepted negotiation: {negotiation_id}. Order spawned: {order_id}",
        negotiation_id=negotiation_id,
        order_id=order_id,
        status="created"
    )
    await asyncio.sleep(0.1)
    
    # 4. State: OrderPaid (including mock USDC balance check)
    log_compliance(
        "INFO",
        "STATE_ORDER_PAID_START",
        f"Verifying USDC balance for payment of order: {order_id}",
        order_id=order_id,
        current_balance=MOCK_USDC_BALANCE,
        required=payment_amount
    )
    
    if MOCK_USDC_BALANCE < payment_amount:
        error_msg = f"Insufficient mock USDC balance. Required: {payment_amount}, Available: {MOCK_USDC_BALANCE}"
        log_compliance("ERROR", "USDC_BALANCE_INSUFFICIENT", error_msg, order_id=order_id)
        raise InsufficientUSDCBalanceError(error_msg)
        
    MOCK_USDC_BALANCE -= payment_amount
    log_compliance(
        "INFO",
        "STATE_ORDER_PAID",
        f"USDC payment completed for order: {order_id}",
        order_id=order_id,
        deducted=payment_amount,
        remaining_balance=MOCK_USDC_BALANCE,
        status="paid"
    )
    await asyncio.sleep(0.1)
    
    # 5. State: DeliverOrder
    simulated_delivery = {
        "delivery_id": f"del_a2a_{os.urandom(8).hex()}",
        "order_id": order_id,
        "deliverable_type": "text",
        "deliverable_text": f"Simulated output from agent at {agent_address} for task: {requirements}",
        "status": "submitted"
    }
    
    log_compliance(
        "INFO",
        "STATE_DELIVER_ORDER",
        f"Counterparty submitted deliverables for order: {order_id}",
        order_id=order_id,
        delivery=simulated_delivery,
        status="delivering"
    )
    await asyncio.sleep(0.1)
    
    # 6. State: OrderCompleted
    final_payload = {
        "order_id": order_id,
        "negotiation_id": negotiation_id,
        "counterparty_address": agent_address,
        "service_id": service_id,
        "price_usdc": payment_amount,
        "status": "completed",
        "deliverable": simulated_delivery,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    log_compliance(
        "INFO",
        "STATE_ORDER_COMPLETED",
        f"A2A order lifecycle completed successfully: {order_id}",
        order_id=order_id,
        final_payload=final_payload,
        status="completed"
    )
    
    return final_payload
