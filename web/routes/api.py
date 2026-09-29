"""Internal JSON routes for the frontend."""

from starlette.responses import JSONResponse

from web.clients.deployer import DeployerClient, DeployerError
from web.clients.relayer import RelayerClient, RelayerError


def register(
    rt,
    deployer_client: DeployerClient,
    relayer_client: RelayerClient,
):
    @rt("/api/order/{order_id}")
    def get_order(order_id: str):
        try:
            data = deployer_client.get_order(order_id)
            return JSONResponse(data)
        except DeployerError as e:
            return JSONResponse({"error": str(e)}, status_code=502)

    @rt("/api/pending/{splitter_address}/{beneficiary}")
    def get_pending(splitter_address: str, beneficiary: str):
        try:
            data = relayer_client.get_pending(splitter_address, beneficiary)
            return JSONResponse(data)
        except RelayerError as e:
            return JSONResponse({"error": str(e)}, status_code=502)

    @rt("/api/relay", methods=["POST"])
    async def relay(request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid JSON"}, status_code=400)

        splitter = body.get("splitter_address", "").strip()
        beneficiary = body.get("beneficiary", "").strip()

        if not splitter or not beneficiary:
            return JSONResponse(
                {"error": "missing splitter_address or beneficiary"},
                status_code=400,
            )

        try:
            data = relayer_client.relay(splitter, beneficiary)
            return JSONResponse(data)
        except RelayerError as e:
            return JSONResponse({"error": str(e)}, status_code=502)
