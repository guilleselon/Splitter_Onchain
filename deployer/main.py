"""
Deployer entry point (production, Monad).

Connects to the RPC from .env, signs with the wallet from .env,
starts the watcher, and serves the API.

Run from the project root:
    python -m deployer.main

Requires .env with:
    MONAD_RPC_URL, WALLET_PRIVATE_KEY, FACTORY_ADDRESS, USDC_ADDRESS, ...
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from eth_account import Account
from web3 import Web3

from config import settings
from deployer.api import create_app
from deployer.state import OrderState
from deployer.watcher import Watcher


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("deployer")


def _require_env():
    """Fail fast and clearly if critical config is missing."""
    missing = []
    if not settings.monad_rpc_url:
        missing.append("MONAD_RPC_URL")
    if not settings.wallet_private_key:
        missing.append("WALLET_PRIVATE_KEY")
    if not settings.factory_address:
        missing.append("FACTORY_ADDRESS")
    if not settings.usdc_address:
        missing.append("USDC_ADDRESS")
    if missing:
        raise RuntimeError("Missing .env variables: " + ", ".join(missing))


def main():
    print("=" * 70)
    print("  Splitter Deployer — Monad")
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
    log.info("wallet: %s", account.address)

    treasury = settings.treasury_address or account.address
    log.info("treasury: %s", treasury)

    # State
    state_dir = Path(settings.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state = OrderState(state_dir)
    log.info(
        "state: %s (pending=%d processed=%d)",
        state_dir.resolve(),
        len(state.list_pending()),
        len(state.list_processed()),
    )

    # Watcher
    watcher = Watcher(
        w3=w3,
        state=state,
        factory_address=settings.factory_address,
        usdc_address=settings.usdc_address,
        interval_seconds=settings.watcher_interval_seconds,
        max_attempts=settings.max_deploy_attempts,
        lookback_blocks=settings.lookback_blocks,
        private_key=settings.wallet_private_key,
    )
    watcher.start()

    # API
    app, rt = create_app(
        state=state,
        w3=w3,
        factory_address=settings.factory_address,
        usdc_address=settings.usdc_address,
        deployer_address=account.address,
        treasury_address=treasury,
        fee_usdc=settings.service_fee_usdc,
    )

    print(f"\n  http://{settings.api_host}:{settings.api_port}")
    print("  Ctrl+C to stop.\n")

    try:
        import uvicorn
        uvicorn.run(
            app,
            host=settings.api_host,
            port=settings.api_port,
            log_level="info",
        )
    finally:
        watcher.stop()


if __name__ == "__main__":
    main()

