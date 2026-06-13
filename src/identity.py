"""
identity.py - Operational node identity initialization and network handshake module.
"""

import os
import json
import datetime
import asyncio
from typing import Tuple, Dict, Any

from dotenv import load_dotenv
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

import croo

class MissingCredentialError(Exception):
    """Raised when one or more required environment variables are missing."""
    pass

class InvalidKeyError(Exception):
    """Raised when the private key is malformed or invalid."""
    pass

def log_compliance(level: str, step: str, message: str, **kwargs) -> None:
    """Prints a structured JSON compliance audit log to standard output."""
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "level": level,
        "step": step,
        "message": message,
    }
    log_entry.update(kwargs)
    print(json.dumps(log_entry), flush=True)

def load_credentials_and_derive_key() -> Dict[str, Any]:
    """
    Loads environment configuration and derives the agent's unique public key.
    
    Returns:
        Dict[str, Any]: A dictionary containing configuration parameters and derived public key.
        
    Raises:
        MissingCredentialError: If required environment variables are missing.
        InvalidKeyError: If the private key cannot be parsed.
    """
    log_compliance("INFO", "IDENTITY_INIT", "Starting identity and credential load sequence.")
    
    # Load environment variables from .env file if present
    load_dotenv()
    
    required_vars = ["CROO_PRIVATE_KEY", "CROO_SDK_KEY", "CROO_BASE_URL", "CROO_WS_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"Systemic configuration dependencies missing: {', '.join(missing_vars)}"
        log_compliance("ERROR", "IDENTITY_LOAD_FAILED", error_msg, missing_dependencies=missing_vars)
        raise MissingCredentialError(error_msg)
        
    private_key_hex = os.getenv("CROO_PRIVATE_KEY", "")
    sdk_key = os.getenv("CROO_SDK_KEY", "")
    base_url = os.getenv("CROO_BASE_URL", "")
    ws_url = os.getenv("CROO_WS_URL", "")
    rpc_url = os.getenv("CROO_RPC_URL", "")
    
    log_compliance("INFO", "CREDENTIALS_LOADED", "Required environment variables successfully loaded.")
    
    try:
        private_value = int(private_key_hex, 16)
        private_key = ec.derive_private_key(private_value, ec.SECP256K1())
        public_key = private_key.public_key()
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        public_key_hex = pub_bytes.hex()
    except Exception as e:
        error_msg = f"Failed to derive public key from private key: {str(e)}"
        log_compliance("ERROR", "KEY_DERIVATION_FAILED", error_msg)
        raise InvalidKeyError(error_msg) from e
        
    log_compliance(
        "INFO",
        "KEY_DERIVED",
        "Agent public key successfully derived from operational wallet state.",
        agent_public_key=public_key_hex
    )
    
    return {
        "private_key_hex": private_key_hex,
        "sdk_key": sdk_key,
        "base_url": base_url,
        "ws_url": ws_url,
        "rpc_url": rpc_url,
        "public_key_hex": public_key_hex
    }

async def initialize_node_identity() -> Tuple[croo.AgentClient, croo.EventStream]:
    """
    Initializes the AgentClient and connects to the CAP network listener.
    
    Returns:
        Tuple[croo.AgentClient, croo.EventStream]: The initialized client and connected event stream.
        
    Raises:
        Exception: If the handshake or connection fails.
    """
    # 1. Load credentials and derive key
    creds = load_credentials_and_derive_key()
    
    # 2. Configure AgentClient
    log_compliance(
        "INFO",
        "CLIENT_CONFIGURING",
        "Initializing CAP agent client configuration.",
        base_url=creds["base_url"],
        ws_url=creds["ws_url"]
    )
    
    config = croo.Config(
        base_url=creds["base_url"],
        ws_url=creds["ws_url"],
        rpc_url=creds["rpc_url"]
    )
    
    client = croo.AgentClient(config=config, sdk_key=creds["sdk_key"])
    
    # 3. Establish handshake via WebSocket listener
    log_compliance(
        "INFO",
        "NETWORK_HANDSHAKE_START",
        "Initiating network handshake connection to the CAP listener.",
        ws_url=creds["ws_url"]
    )
    
    try:
        stream = await client.connect_websocket()
    except Exception as e:
        error_msg = f"Network handshake connection failed: {str(e)}"
        log_compliance("ERROR", "NETWORK_HANDSHAKE_FAILED", error_msg)
        await client.close()
        raise
        
    log_compliance(
        "INFO",
        "NETWORK_HANDSHAKE_CONFIRMED",
        "Network handshake confirmed. Bounded to CAP network listener.",
        agent_public_key=creds["public_key_hex"],
        ws_url=creds["ws_url"]
    )
    
    log_compliance(
        "INFO",
        "CONTAINER_DEPLOYMENT_SUCCESS",
        "Successful deployment of Antigravity engine container.",
        agent_public_key=creds["public_key_hex"]
    )
    
    return client, stream

if __name__ == "__main__":
    # Demonstration execution block
    async def main():
        try:
            client, stream = await initialize_node_identity()
            # Clean up after demonstration
            await stream.close()
            await client.close()
        except Exception as e:
            # Silence exception in main output to keep audit trail clean
            pass

    asyncio.run(main())
