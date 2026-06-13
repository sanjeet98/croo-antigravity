import os
import asyncio
from unittest.mock import patch, AsyncMock
import sys

# Ensure src is on path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Set mock env variables for local execution/verification
os.environ["CROO_PRIVATE_KEY"] = "01" * 32
os.environ["CROO_SDK_KEY"] = "test-sdk-key"
os.environ["CROO_BASE_URL"] = "http://localhost:8000"
os.environ["CROO_WS_URL"] = "ws://localhost:8000"

from src.identity import initialize_node_identity

async def main():
    # Mock connect_websocket to simulate a successful CAP connection handshake
    mock_stream = AsyncMock()
    mock_stream.close = AsyncMock()
    
    with patch("croo.AgentClient.connect_websocket", return_value=mock_stream):
        client, stream = await initialize_node_identity()
        # Clean up
        await stream.close()
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
