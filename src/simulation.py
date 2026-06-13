"""
simulation.py - Multi-buyer workload generator and stress-test harness.
"""

import os
import json
import asyncio
import random
import datetime
from typing import List, Dict, Any, Set

from dotenv import load_dotenv
from src.identity import log_compliance, load_credentials_and_derive_key
from src.tools import fetch_market_indices, generate_audit_payload

# Exactly 5 unique mock Web3 buyer addresses for anti-sybil compliance testing
BUYER_WALLETS = [
    "0x1000000000000000000000000000000000000001",
    "0x2000000000000000000000000000000000000002",
    "0x3000000000000000000000000000000000000003",
    "0x4000000000000000000000000000000000000004",
    "0x5000000000000000000000000000000000000005"
]

async def execute_autonomous_job(
    buyer_address: str, 
    task_id: str, 
    payment_amount: float,
    agent_public_key: str
) -> Dict[str, Any]:
    """
    Executes a single autonomous query and delivery job on behalf of a buyer.
    
    Args:
        buyer_address (str): The mock wallet address of the buyer.
        task_id (str): The unique identifier for this task.
        payment_amount (float): USDC price for this job.
        agent_public_key (str): The derived public key of the servicing agent.
        
    Returns:
        Dict[str, Any]: A record of the completed job including delivery status and metadata.
    """
    # 1. Organic delay offset to mimic human buyer trigger patterns
    start_delay = random.uniform(0.2, 1.5)
    await asyncio.sleep(start_delay)
    
    log_compliance(
        "INFO",
        "JOB_START",
        f"Starting autonomous job execution for buyer: {buyer_address}",
        task_id=task_id,
        buyer_address=buyer_address,
        start_delay=start_delay
    )
    
    try:
        # 2. Invoke Tool 1 (Market Index Scraper)
        market_data_json = await fetch_market_indices(assets=["BTC", "ETH"])
        
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.1, 0.4))
        
        # 3. Invoke Tool 2 (Signed Audit Payload Generation)
        audit_payload_json = generate_audit_payload(
            raw_data=market_data_json,
            operator_id=agent_public_key
        )
        
        log_compliance(
            "INFO",
            "JOB_DELIVERED",
            f"Successfully delivered audit payload for task: {task_id}",
            task_id=task_id,
            buyer_address=buyer_address,
            payment_amount=payment_amount
        )
        
        return {
            "task_id": task_id,
            "buyer_address": buyer_address,
            "status": "success",
            "revenue_usdc": payment_amount,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
    except Exception as e:
        error_msg = f"Job execution failed for task {task_id}: {str(e)}"
        log_compliance(
            "ERROR",
            "JOB_FAILED",
            error_msg,
            task_id=task_id,
            buyer_address=buyer_address
        )
        return {
            "task_id": task_id,
            "buyer_address": buyer_address,
            "status": "failed",
            "revenue_usdc": 0.0,
            "error": str(e),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

async def run_multi_buyer_simulation() -> None:
    """
    Launches a concurrent workload generator simulating exactly 5 distinct buyers
    submitting queries to the research node.
    """
    log_compliance("INFO", "SIMULATION_START", "Starting multi-buyer concurrent stress test simulation.")
    
    # Pre-configure mock keys if not set to ensure local out-of-box compatibility
    if not os.getenv("CROO_PRIVATE_KEY"):
        os.environ["CROO_PRIVATE_KEY"] = "01" * 32
    if not os.getenv("CROO_SDK_KEY"):
        os.environ["CROO_SDK_KEY"] = "sim-sdk-key"
    if not os.getenv("CROO_BASE_URL"):
        os.environ["CROO_BASE_URL"] = "http://localhost:8000"
    if not os.getenv("CROO_WS_URL"):
        os.environ["CROO_WS_URL"] = "ws://localhost:8000"
        
    # Load credentials to get the agent's derived public key
    creds = load_credentials_and_derive_key()
    agent_public_key = creds["public_key_hex"]
    
    tasks = []
    # Dispatch exactly one job for each of the 5 buyer wallets
    for idx, buyer_wallet in enumerate(BUYER_WALLETS):
        task_id = f"task_sim_{idx:03d}_{os.urandom(4).hex()}"
        payment_amount = round(random.uniform(5.0, 25.0), 2)
        tasks.append(
            execute_autonomous_job(
                buyer_address=buyer_wallet,
                task_id=task_id,
                payment_amount=payment_amount,
                agent_public_key=agent_public_key
            )
        )
        
    # Execute all workloads concurrently
    log_compliance("INFO", "SIMULATION_CONCURRENT_DISPATCH", f"Dispatching {len(tasks)} concurrent tasks.")
    records = await asyncio.gather(*tasks)
    
    # 4. Metrics Recording & Summary Statement
    successful_deliveries = 0
    unique_addresses_serviced: Set[str] = set()
    total_usdc_revenue = 0.0
    
    for record in records:
        if record["status"] == "success":
            successful_deliveries += 1
            unique_addresses_serviced.add(record["buyer_address"])
            total_usdc_revenue += record["revenue_usdc"]
            
    summary = {
        "total_successful_deliveries": successful_deliveries,
        "unique_addresses_serviced": len(unique_addresses_serviced),
        "total_simulated_usdc_revenue": round(total_usdc_revenue, 2),
        "total_attempted": len(records)
    }
    
    log_compliance(
        "INFO",
        "SIMULATION_SUMMARY",
        "=== MULTI-BUYER SIMULATION WORKLOAD SUMMARY ===",
        **summary
    )

if __name__ == "__main__":
    asyncio.run(run_multi_buyer_simulation())
