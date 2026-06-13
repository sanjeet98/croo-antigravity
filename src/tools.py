"""
tools.py - Functional utility tools for the Antigravity agent node.
"""

import json
import datetime
import hashlib
import hmac
import os
import logging
from typing import List, Dict, Any, Optional

import httpx

logger = logging.getLogger("croo")

# Fallback mock market indices
DEFAULT_MARKET_DATA = {
    "BTC": {"price": 67340.50, "volume_24h": 28490510200.0},
    "ETH": {"price": 3495.20, "volume_24h": 14920480300.0},
    "SOL": {"price": 145.75, "volume_24h": 3290450000.0}
}

async def fetch_market_indices(assets: Optional[List[str]] = None) -> str:
    """
    Asynchronously fetches market index data (prices and 24h trade volumes) 
    for specified cryptographic assets.
    
    If the remote fallback API (CoinGecko) is unreachable or fails, 
    the function returns deterministic mock data for the requested assets.
    
    Args:
        assets (Optional[List[str]]): A list of asset symbols to retrieve (e.g. ['BTC', 'ETH']).
                                      If None, default assets ['BTC', 'ETH', 'SOL'] will be returned.
                                      
    Returns:
        str: A deterministic JSON string mapping assets to their USD prices and trade volumes.
             Example format:
             {
                 "BTC": {"price": 67340.5, "volume_24h": 28490510200.0},
                 ...
             }
             
    Raises:
        RuntimeError: If JSON serialization fails or unexpected exceptions occur.
    """
    if not assets:
        assets = ["BTC", "ETH", "SOL"]
    
    # Standardize asset names for CoinGecko simple price API mapping
    symbol_to_id = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana"
    }
    
    selected_ids = [symbol_to_id[a] for a in assets if a in symbol_to_id]
    result_data: Dict[str, Dict[str, float]] = {}
    
    if selected_ids:
        ids_param = ",".join(selected_ids)
        api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies=usd&include_24hr_vol=true"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(api_url)
                if response.status_code == 200:
                    api_data = response.json()
                    # Map the response back to symbols
                    id_to_symbol = {v: k for k, v in symbol_to_id.items()}
                    for coin_id, prices in api_data.items():
                        symbol = id_to_symbol.get(coin_id)
                        if symbol:
                            result_data[symbol] = {
                                "price": float(prices.get("usd", 0.0)),
                                "volume_24h": float(prices.get("usd_24h_vol", 0.0))
                            }
                else:
                    logger.warning(
                        "CoinGecko API returned status %d, falling back to mock data.", 
                        response.status_code
                    )
        except Exception as e:
            logger.warning("Failed to fetch from external API (%s), using mock fallback.", str(e))
            
    # Populate missing assets with fallback mock data to guarantee deterministic output
    for symbol in assets:
        if symbol not in result_data and symbol in DEFAULT_MARKET_DATA:
            result_data[symbol] = DEFAULT_MARKET_DATA[symbol]
            
    try:
        return json.dumps(result_data, sort_keys=True)
    except Exception as e:
        error_msg = f"Failed to serialize market index data to JSON: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def generate_audit_payload(
    raw_data: str, 
    operator_id: str, 
    metadata_headers: Optional[Dict[str, str]] = None
) -> str:
    """
    Formats raw analytical data into a unified report layout and appends 
    cryptographic verification headers and signatures (HMAC-SHA256).
    
    Args:
        raw_data (str): The raw analytical report string.
        operator_id (str): The unique identifier of the node operator.
        metadata_headers (Optional[Dict[str, str]]): Additional headers to embed in report metadata.
        
    Returns:
        str: A JSON string containing the formatted report, compliance metadata, 
             and HMAC verification signature.
             
    Raises:
        ValueError: If raw_data or operator_id are empty.
        RuntimeError: If serialization fails.
    """
    if not raw_data:
        raise ValueError("Data verification error: raw_data cannot be empty.")
    if not operator_id:
        raise ValueError("Data verification error: operator_id cannot be empty.")
        
    # Construct unified report layout
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    formatted_report = (
        f"=== COMPLIANCE AUDIT REPORT ===\n"
        f"Timestamp: {timestamp}\n"
        f"Operator: {operator_id}\n"
        f"--------------------------------\n"
        f"Payload:\n{raw_data}\n"
        f"=== END OF REPORT ==="
    )
    
    # Retrieve private key/secret for HMAC tag computation. Use env variable or standard fallback key.
    secret_key = os.getenv("CROO_PRIVATE_KEY", "default_secure_audit_secret_key_128_bits").encode('utf-8')
    
    try:
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            secret_key,
            formatted_report.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "X-Node-Operator": operator_id,
            "X-Audit-Version": "1.0",
        }
        if metadata_headers:
            headers.update(metadata_headers)
            
        payload = {
            "report_id": f"audit_{hashlib.sha256(formatted_report.encode('utf-8')).hexdigest()[:16]}",
            "timestamp": timestamp,
            "operator_id": operator_id,
            "content": formatted_report,
            "verification": {
                "algorithm": "HMAC-SHA256",
                "signature_tag": signature,
                "headers": headers
            }
        }
        
        return json.dumps(payload, sort_keys=True)
    except Exception as e:
        error_msg = f"Failed to generate audit payload JSON: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
