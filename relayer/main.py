"""
Relayer entry point (production, Monad).

Connects to the RPC from .env, signs with the wallet from .env,
and serves the API the web uses to handle claims.

Run from the project root:
    python -m relayer.main

Requires .env with:
    MONAD_RPC_URL, WALLET_PRIVATE_KEY, ...
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from eth_account import Account
from web3 import Web3

from config import settings
from relayer.api import create_app


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("relayer")


# The relayer only acts if pending >= this value.
# Below it, it's not worth spending gas.
# In testnet, 0 = accept any amount.
MIN_PENDING_WEI = 0  # Testnet. Production: 100_000 (0.10 USDC)


def _require_env():
    missing = []
    if not settings.monad_rpc_url:
        missing.append("MONAD_RPC_URL")
    if not settings.wallet_private_key:
        missing.append("WALLET_PRIVATE_KEY")
    if missing:
        raise RuntimeError("Missing .env variables: " + ", ".join(missing))


def main():
    print("=" * 70)
    print("  Splitter Relayer — Monad")
    print("=" * 70)

    _require_env()

    # Chain
    w3 = Web3(Web3.HTTPProvider(settings.monad_rpc_url))
    if not w3.is_connected():
        raise RuntimeError(
            f"Could not connect to {settings.monad_rpc_url}"
        )
    log.info("RPC OK: %s (chain_id=%s)", settings.monad_rpc_url, w3.eth.chain_id)

    # Wallet
    account = Account.from_key(settings.wallet_private_key)
    w3.eth.default_account = account.address
    log.info("relayer wallet: %s", account.address)
    log.info("min_pending_wei: %d", MIN_PENDING_WEI)

    # API (with private_key for local signing)
    app, rt = create_app(
        w3=w3,
        relayer_address=account.address,
        private_key=settings.wallet_private_key,
        min_pending_wei=MIN_PENDING_WEI,
    )

    print(f"\n  http://{settings.api_host}:5003")
    print("  Endpoints:")
    print("    GET  /health")
    print("    GET  /splitter/{address}/pending/{beneficiary}")
    print("    POST /relay")
    print("\n  Ctrl+C to stop.\n")

    try:
        import uvicorn
        uvicorn.run(
            app,
            host=settings.api_host,
            port=5003,
            log_level="info",
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
