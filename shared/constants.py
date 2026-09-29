"""Shared constants for the Splitter service (Monad)."""

from decimal import Decimal
from eth_utils import to_checksum_address

# ------------------------------------------------------------------
# Chains
# ------------------------------------------------------------------
CHAIN_ID_MONAD = 143
CHAIN_ID_MONAD_TESTNET = 10143

# ------------------------------------------------------------------
# USDC
# ------------------------------------------------------------------
USDC_MONAD = to_checksum_address("0x754704Bc059F8C67012fEd69BC8A327a5aafb603")
USDC_MONAD_TESTNET = to_checksum_address("0x534b2f3A21130d7a60830c2Df862319e593943A3")

USDC_DECIMALS = 6

# ------------------------------------------------------------------
# Factory (fill after deployment)
# ------------------------------------------------------------------
FACTORY_MONAD = to_checksum_address("0x0000000000000000000000000000000000000000")
FACTORY_MONAD_TESTNET = to_checksum_address("0x0000000000000000000000000000000000000000")

# ------------------------------------------------------------------
# Business rules
# ------------------------------------------------------------------
TOTAL_BPS = 10_000
MAX_BENEFICIARIES = 20

# ------------------------------------------------------------------
# Default fees (USDC)
# ------------------------------------------------------------------
DEFAULT_SERVICE_FEE_USDC = Decimal("2.00")
DEFAULT_GAS_BUFFER_USDC = Decimal("0.05")
DEFAULT_RELAYER_FEE_USDC = Decimal("0.10")


def usdc_address(chain_id: int) -> str:
    if chain_id == CHAIN_ID_MONAD:
        return USDC_MONAD
    if chain_id == CHAIN_ID_MONAD_TESTNET:
        return USDC_MONAD_TESTNET
    raise ValueError(f"Unsupported chain: {chain_id}")


def factory_address(chain_id: int) -> str:
    if chain_id == CHAIN_ID_MONAD:
        return FACTORY_MONAD
    if chain_id == CHAIN_ID_MONAD_TESTNET:
        return FACTORY_MONAD_TESTNET
    raise ValueError(f"Unsupported chain: {chain_id}")
