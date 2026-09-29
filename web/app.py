"""
Web entry point (Monad).

Run from the project root:
    python -m web.app
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fasthtml.common import fast_app
from web3 import Web3

from web.clients.chain import ChainReader
from web.clients.deployer import DeployerClient
from web.clients.relayer import RelayerClient
from web.config import settings
from web.routes import api, claim, create, marketing, request, split


def create_app():
    app, rt = fast_app(
        pico=False,
        hdrs=(),
        default_hdrs=False,
        live=False,
    )

    if not settings.treasury_address:
        raise RuntimeError(
            "Missing TREASURY_ADDRESS in .env. "
            "Run the deployer to get the treasury address."
        )

    # Clients
    deployer_client = DeployerClient(
        base_url=settings.deployer_url,
        timeout=settings.http_timeout_seconds,
    )
    relayer_client = RelayerClient(
        base_url=settings.relayer_url,
        timeout=settings.http_timeout_seconds,
    )

    w3 = Web3(Web3.HTTPProvider(settings.monad_rpc_url))
    chain_reader = ChainReader(w3=w3, usdc_address=settings.usdc_address)

    relayer_fee_wei = int(settings.relayer_fee_usdc * 1_000_000)
    treasury_address = settings.treasury_address

    # In-memory map: splitter_address_lower -> order info dict
    known_orders: dict = {}

    # Register routes
    marketing.register(rt)
    create.register(rt)
    request.register(
        rt,
        deployer_client=deployer_client,
        relayer_fee_wei=relayer_fee_wei,
        treasury_address=treasury_address,
        known_orders=known_orders,
    )
    split.register(
        rt,
        chain_reader=chain_reader,
        known_orders=known_orders,
        web_public_url=settings.web_public_url,
    )
    claim.register(
        rt,
        chain_reader=chain_reader,
        relayer_client=relayer_client,
        known_orders=known_orders,
    )
    api.register(
        rt,
        deployer_client=deployer_client,
        relayer_client=relayer_client,
    )

    return app, rt


def main():
    app, rt = create_app()
    print("=" * 70)
    print("  Splitter Web — Monad")
    print("=" * 70)
    print(f"\n  http://{settings.web_host}:{settings.web_port}")
    print(f"  Public URL: {settings.web_public_url}")
    print("\n  Routes:")
    print("    GET  /")
    print("    GET  /how-it-works")
    print("    GET  /create")
    print("    POST /request")
    print("    GET  /split/{address}")
    print("    GET  /claim")
    print("    GET  /claim/{address}")
    print("    GET  /claim/{address}/consultar?beneficiary=0x...")
    print("    GET  /api/order/{id}")
    print("    GET  /api/pending/{splitter}/{beneficiary}")
    print("    POST /api/relay")
    print("\n  Ctrl+C to stop.\n")

    import uvicorn
    uvicorn.run(
        app,
        host=settings.web_host,
        port=settings.web_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
