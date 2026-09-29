"""
Web configuration (Monad).

The web is a service consumer: it signs nothing, custodies nothing.
It only reads from the chain and calls the deployer and relayer over HTTP.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class WebSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- External services ---
    deployer_url: str = "http://localhost:5002"
    relayer_url: str = "http://localhost:5003"

    # --- Chain ---
    monad_rpc_url: str = "https://testnet-rpc.monad.xyz"
    chain_id: int = 10143

    # --- Contracts ---
    factory_address: str = ""
    usdc_address: str = "0x534b2f3A21130d7a60830c2Df862319e593943A3"

    # --- Web ---
    web_host: str = "0.0.0.0"
    web_port: int = 5001
    web_public_url: str = "http://localhost:5001"
    secret_key: str = "dev-secret-change-me"

    # --- Fees ---
    service_fee_usdc: float = 2.0
    relayer_fee_usdc: float = 0.10

    # --- HTTP ---
    http_timeout_seconds: float = 10.0

    # --- Treasury ---
    treasury_address: str = ""

    # --- Static assets ---
    static_dir: Path = Path(__file__).parent / "static"


settings = WebSettings()


# ==================================================================
# Explorer helpers (Monadscan, based on chain_id)
# ==================================================================

EXPLORER_MAINNET = "https://monadscan.com"
EXPLORER_TESTNET = "https://testnet.monadscan.com"


def get_explorer_base(chain_id: int | None = None) -> str:
    """Return the explorer base URL for the given chain_id."""
    cid = chain_id if chain_id is not None else settings.chain_id
    if cid == 143:
        return EXPLORER_MAINNET
    return EXPLORER_TESTNET


def explorer_address_url(address: str, chain_id: int | None = None) -> str:
    """Explorer URL for an address."""
    return f"{get_explorer_base(chain_id)}/address/{address}"


def explorer_tx_url(tx_hash: str, chain_id: int | None = None) -> str:
    """Explorer URL for a transaction."""
    return f"{get_explorer_base(chain_id)}/tx/{tx_hash}"
