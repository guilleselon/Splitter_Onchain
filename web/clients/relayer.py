"""
HTTP client for the relayer.

The web calls these methods to query pending amounts and sign claims.
"""

import httpx


class RelayerError(Exception):
    """Generic error while talking to the relayer."""


class RelayerClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def _handle(self, response: httpx.Response) -> dict:
        try:
            data = response.json()
        except Exception:
            raise RelayerError(
                f"non-JSON response from relayer (status {response.status_code})"
            )
        if response.status_code >= 400:
            msg = data.get("error") or f"HTTP {response.status_code}"
            raise RelayerError(msg)
        return data

    def health(self) -> dict:
        try:
            with self._client() as c:
                r = c.get("/health")
        except httpx.HTTPError as e:
            raise RelayerError(f"could not reach relayer: {e}") from e
        return self._handle(r)

    def get_pending(self, splitter_address: str, beneficiary: str) -> dict:
        url = f"/splitter/{splitter_address}/pending/{beneficiary}"
        try:
            with self._client() as c:
                r = c.get(url)
        except httpx.HTTPError as e:
            raise RelayerError(f"could not reach relayer: {e}") from e
        return self._handle(r)

    def relay(self, splitter_address: str, beneficiary: str) -> dict:
        payload = {
            "splitter_address": splitter_address,
            "beneficiary": beneficiary,
        }
        try:
            with self._client() as c:
                r = c.post("/relay", json=payload)
        except httpx.HTTPError as e:
            raise RelayerError(f"could not reach relayer: {e}") from e
        return self._handle(r)
