"""
HTTP client for the deployer.

The web calls these methods to create and query orders.
Synchronous, using httpx. Timeouts and network errors are raised as
DeployerError so routes can handle them.
"""

from typing import Any

import httpx


class DeployerError(Exception):
    """Generic error while talking to the deployer."""


class DeployerClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def _handle(self, response: httpx.Response) -> dict:
        try:
            data = response.json()
        except Exception:
            raise DeployerError(
                f"non-JSON response from deployer (status {response.status_code})"
            )
        if response.status_code >= 400:
            msg = data.get("error") or f"HTTP {response.status_code}"
            raise DeployerError(msg)
        return data

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------

    def health(self) -> dict:
        try:
            with self._client() as c:
                r = c.get("/health")
        except httpx.HTTPError as e:
            raise DeployerError(f"could not reach deployer: {e}") from e
        return self._handle(r)

    def create_order(
        self,
        beneficiaries: list[str],
        shares: list[int],
        treasury: str,
        relayer_fee: int,
    ) -> dict:
        payload = {
            "beneficiaries": beneficiaries,
            "shares": shares,
            "treasury": treasury,
            "relayer_fee": relayer_fee,
        }
        try:
            with self._client() as c:
                r = c.post("/orders", json=payload)
        except httpx.HTTPError as e:
            raise DeployerError(f"could not reach deployer: {e}") from e
        return self._handle(r)

    def get_order(self, order_id: str) -> dict:
        try:
            with self._client() as c:
                r = c.get(f"/orders/{order_id}")
        except httpx.HTTPError as e:
            raise DeployerError(f"could not reach deployer: {e}") from e
        return self._handle(r)
