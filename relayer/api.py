"""
Relayer API.

Exposes endpoints consumed by the web:
    GET  /health
    GET  /splitter/{address}/pending/{beneficiary}
    POST /relay

Returns JSON. Signs with the wallet configured in w3.eth.default_account.
Does not custody anything.
"""

from typing import Any

from fasthtml.common import fast_app
from starlette.responses import JSONResponse
from web3 import Web3

from relayer.client import (
    get_pending,
    get_relayer_fee,
    get_share,
    is_beneficiary,
    relay_release,
)


def validate_relay_payload(body: dict) -> tuple[bool, str | None]:
    required = ["splitter_address", "beneficiary"]
    for field in required:
        if field not in body:
            return False, f"missing field '{field}'"
    if not isinstance(body["splitter_address"], str):
        return False, "splitter_address must be a string"
    if not isinstance(body["beneficiary"], str):
        return False, "beneficiary must be a string"
    return True, None


def create_app(
    w3: Web3,
    relayer_address: str,
    private_key: str | None = None,
    min_pending_wei: int = 0,
) -> Any:
    app, rt = fast_app(pico=False, hdrs=(), default_hdrs=False, live=False)

    relayer_checksum = w3.to_checksum_address(relayer_address)

    @rt("/health")
    def health():
        return JSONResponse({
            "status": "ok",
            "chain_id": w3.eth.chain_id,
            "block": w3.eth.block_number,
            "relayer": relayer_checksum,
            "min_pending_wei": min_pending_wei,
        })

    @rt("/splitter/{splitter_address}/pending/{beneficiary}")
    def get_pending_endpoint(splitter_address: str, beneficiary: str):
        if not w3.is_address(splitter_address):
            return JSONResponse({"error": "invalid splitter_address"}, status_code=400)
        if not w3.is_address(beneficiary):
            return JSONResponse({"error": "invalid beneficiary"}, status_code=400)

        splitter_checksum = w3.to_checksum_address(splitter_address)
        beneficiary_checksum = w3.to_checksum_address(beneficiary)

        try:
            share = get_share(w3, splitter_checksum, beneficiary_checksum)
            pending = get_pending(w3, splitter_checksum, beneficiary_checksum)
            fee = get_relayer_fee(w3, splitter_checksum)
        except Exception as e:
            return JSONResponse(
                {"error": f"error reading splitter: {e}"},
                status_code=500,
            )

        if share == 0:
            return JSONResponse(
                {"error": "not a beneficiary of this splitter"},
                status_code=404,
            )

        applied_fee = min(fee, pending) if pending > 0 else 0
        net_to_beneficiary = pending - applied_fee

        return JSONResponse({
            "splitter_address": splitter_checksum,
            "beneficiary": beneficiary_checksum,
            "share_bps": share,
            "pending_wei": pending,
            "relayer_fee_wei": applied_fee,
            "net_to_beneficiary_wei": net_to_beneficiary,
            "relayable": pending > 0 and pending >= min_pending_wei,
            "min_pending_wei": min_pending_wei,
        })

    @rt("/relay", methods=["POST"])
    async def relay_endpoint(request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid JSON"}, status_code=400)

        ok, err = validate_relay_payload(body)
        if not ok:
            return JSONResponse({"error": err}, status_code=400)

        splitter_address = body["splitter_address"]
        beneficiary = body["beneficiary"]

        if not w3.is_address(splitter_address):
            return JSONResponse({"error": "invalid splitter_address"}, status_code=400)
        if not w3.is_address(beneficiary):
            return JSONResponse({"error": "invalid beneficiary"}, status_code=400)

        splitter_checksum = w3.to_checksum_address(splitter_address)
        beneficiary_checksum = w3.to_checksum_address(beneficiary)

        try:
            if not is_beneficiary(w3, splitter_checksum, beneficiary_checksum):
                return JSONResponse(
                    {"error": "not a beneficiary of this splitter"},
                    status_code=400,
                )
        except Exception as e:
            return JSONResponse(
                {"error": f"error reading splitter: {e}"},
                status_code=500,
            )

        try:
            pending = get_pending(w3, splitter_checksum, beneficiary_checksum)
        except Exception as e:
            return JSONResponse(
                {"error": f"error calculating pending: {e}"},
                status_code=500,
            )

        if pending <= 0:
            return JSONResponse(
                {"error": "nothing to claim"},
                status_code=400,
            )

        if pending < min_pending_wei:
            return JSONResponse(
                {
                    "error": "pending below configured minimum",
                    "pending_wei": pending,
                    "min_pending_wei": min_pending_wei,
                },
                status_code=400,
            )

        tx_hash, err = relay_release(
            w3, splitter_checksum, beneficiary_checksum,
            private_key=private_key,
        )

        if err is not None:
            return JSONResponse(
                {"error": f"relay failed: {err}"},
                status_code=500,
            )

        return JSONResponse({
            "status": "relayed",
            "tx_hash": tx_hash,
            "splitter_address": splitter_checksum,
            "beneficiary": beneficiary_checksum,
            "pending_wei": pending,
        })

    return app, rt
