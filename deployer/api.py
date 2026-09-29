"""
Deployer API.

Exposes three endpoints consumed by the web:
    POST /orders          -> creates an order, returns payment address
    GET  /orders/{id}     -> returns order status
    GET  /health          -> healthcheck

Returns JSON. Does not sign transactions (executor/watcher do that).
Does not custody anything.
"""

import secrets
from typing import Any

from fasthtml.common import fast_app
from starlette.responses import JSONResponse
from web3 import Web3

from deployer.state import OrderState
from shared.config_hash import hash_config_hex


# ==================================================================
# Minimal Factory ABI
# ==================================================================

FACTORY_ABI = [
    {
        "inputs": [],
        "name": "master",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "deployer",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "_token", "type": "address"},
            {"name": "_beneficiaries", "type": "address[]"},
            {"name": "_shares", "type": "uint256[]"},
            {"name": "_treasury", "type": "address"},
            {"name": "_relayer_fee", "type": "uint256"},
            {"name": "_config_hash", "type": "bytes32"},
        ],
        "name": "create",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


# ==================================================================
# Utilities
# ==================================================================

def new_order_id() -> str:
    return secrets.token_hex(8)


def validate_order_payload(body: dict) -> tuple[bool, str | None]:
    required = ["beneficiaries", "shares", "treasury", "relayer_fee"]
    for field in required:
        if field not in body:
            return False, f"missing field '{field}'"

    bens = body["beneficiaries"]
    shares = body["shares"]

    if not isinstance(bens, list) or not isinstance(shares, list):
        return False, "beneficiaries and shares must be lists"
    if len(bens) != len(shares):
        return False, "beneficiaries and shares must have the same length"
    if len(bens) == 0:
        return False, "at least one beneficiary is required"
    if len(bens) > 20:
        return False, "maximum 20 beneficiaries"
    if sum(shares) != 10_000:
        return False, "shares must sum to 10000"

    return True, None


# ==================================================================
# App factory
# ==================================================================

def create_app(
    state: OrderState,
    w3: Web3,
    factory_address: str,
    usdc_address: str,
    deployer_address: str,
    treasury_address: str,
    fee_usdc: float,
) -> Any:
    app, rt = fast_app(pico=False, hdrs=(), default_hdrs=False, live=False)

    factory = w3.eth.contract(
        address=w3.to_checksum_address(factory_address),
        abi=FACTORY_ABI,
    )
    deployer_checksum = w3.to_checksum_address(deployer_address)
    usdc_checksum = w3.to_checksum_address(usdc_address)
    master_address = factory.functions.master().call()

    # ------------------------------------------------------------------
    # GET /health
    # ------------------------------------------------------------------
    @rt("/health")
    def health():
        return JSONResponse({
            "status": "ok",
            "chain_id": w3.eth.chain_id,
            "block": w3.eth.block_number,
            "factory": factory_address,
            "master": master_address,
            "pending_orders": len(state.list_pending()),
        })

    # ------------------------------------------------------------------
    # POST /orders
    # ------------------------------------------------------------------
    @rt("/orders", methods=["POST"])
    async def create_order(request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid JSON"}, status_code=400)

        ok, err = validate_order_payload(body)
        if not ok:
            return JSONResponse({"error": err}, status_code=400)

        beneficiaries = body["beneficiaries"]
        shares = body["shares"]
        treasury = body["treasury"]
        relayer_fee = int(body["relayer_fee"])

        for b in beneficiaries:
            if not w3.is_address(b):
                return JSONResponse(
                    {"error": f"invalid address: {b}"}, status_code=400
                )
        if not w3.is_address(treasury):
            return JSONResponse(
                {"error": "invalid treasury"}, status_code=400
            )

        beneficiaries = [w3.to_checksum_address(b) for b in beneficiaries]
        treasury = w3.to_checksum_address(treasury)

        order_id = new_order_id()
        config_hash_hex = hash_config_hex(
            beneficiaries, shares, int(order_id, 16)
        )
        config_hash = bytes.fromhex(config_hash_hex.replace("0x", ""))

        # Prediction: call create() in read-only mode
        try:
            splitter_address = factory.functions.create(
                usdc_checksum,
                beneficiaries,
                shares,
                treasury,
                relayer_fee,
                config_hash,
            ).call({"from": deployer_checksum})
        except Exception as e:
            return JSONResponse(
                {"error": f"error predicting address: {e}"},
                status_code=500,
            )

        state.add_order({
            "order_id": order_id,
            "beneficiaries": beneficiaries,
            "shares": shares,
            "treasury": treasury,
            "relayer_fee": relayer_fee,
            "config_hash": config_hash_hex,
            "predicted_splitter_address": splitter_address,
            "fee_usdc": fee_usdc,
            "fee_wei": int(fee_usdc * 1_000_000),
            "status": "pending",
            "deploy_attempts": 0,
        })

        return JSONResponse({
            "order_id": order_id,
            "payment_address": splitter_address,
            "predicted_splitter_address": splitter_address,
            "fee_usdc": fee_usdc,
            "status": "pending",
        })

    # ------------------------------------------------------------------
    # GET /orders/{order_id}
    # ------------------------------------------------------------------
    @rt("/orders/{order_id}")
    def get_order(order_id: str):
        order = state.get_order(order_id)
        if order is None:
            return JSONResponse(
                {"error": "order not found"}, status_code=404
            )
        return JSONResponse({
            "order_id": order["order_id"],
            "status": order["status"],
            "payment_address": order["predicted_splitter_address"],
            "predicted_splitter_address": order["predicted_splitter_address"],
            "splitter_address": order.get("splitter_address"),
            "fee_usdc": order["fee_usdc"],
            "tx_hash": order.get("tx_hash"),
            "deploy_tx_hash": order.get("deploy_tx_hash"),
            "error": order.get("error"),
        })

    return app, rt

