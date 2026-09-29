"""
Global configuration for the Splitter service.

Used by both the deployer and the relayer. The web has its own config
in web/config.py.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Chain ---
    monad_rpc_url: str = "https://testnet-rpc.monad.xyz"
    monad_mainnet_rpc_url: str = "https://rpc.monad.xyz"
    chain_id: int = 10143

    # --- Contracts ---
    factory_address: str = ""
    usdc_address: str = "0x534b2f3A21130d7a60830c2Df862319e593943A3"

    # --- Service wallet ---
    wallet_private_key: str = ""
    treasury_address: str = ""

    # --- Fees ---
    service_fee_usdc: float = 2.0
    relayer_fee_usdc: float = 0.10

    # --- State ---
    state_dir: Path = Path("state")

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 5002

    # --- Watcher ---
    watcher_interval_seconds: int = 60
    max_deploy_attempts: int = 3
    lookback_blocks: int = 100


settings = Settings()
