# Autonomous Antigravity Intelligence Node (CROO Hackathon)

An autonomous, paid operational service node built on the **Google Antigravity** framework and fully integrated with the **CROO Agent Protocol (CAP)** commerce layer.

## Core Features
- **Antigravity Sandbox:** Secure, deterministic Linux container environment executing isolated Python research and indexing tools.
- **A2A Composability:** Programmatically routes data verification tasks to 3 external network counterparties over CAP.
- **Sybil Defenses:** Fully optimized to handle multi-buyer transaction volume concurrently without state cross-contamination.

## Project Structure
- `src/agent_loop.py`: Central background coordinator executing the main Antigravity reasoning block.
- `src/tools.py`: Deterministic local sandbox intelligence extraction utilities.
- `src/composability.py`: CAP lifecycle management for outbound agent-to-agent hiring.
- `src/simulation.py`: Multi-buyer traffic simulator representing 5 unique network wallets.

## Local Setup & Replication

1. **Clone and Install Dependencies:**
   ```bash
   git clone https://github.com/sanjeet98/croo-antigravity.git
   cd croo-antigravity
   pip install google-antigravity croo-cap-sdk python-dotenv
   ```

2. **Configure Environment Variables (.env):**
   ```text
   CROO_AGENT_WALLET_ADDRESS=0xYourLiveDeployedAgentWalletAddress
   CROO_CAP_API_KEY=your_production_cap_network_key
   ```

3. **Execute the Multi-Buyer Verification Suite:**
   ```bash
   python -m src.simulation
   ```
