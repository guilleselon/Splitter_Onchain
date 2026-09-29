"""Address and share validation helpers."""

from eth_utils import is_address, to_checksum_address


def normalize_address(address: str) -> str:
    """Return the address with EIP-55 checksum.

    Raises ValueError if the address is invalid.
    """
    if not isinstance(address, str) or not is_address(address):
        raise ValueError(f"Invalid address: {address!r}")
    return to_checksum_address(address)


def is_valid_address(address: str) -> bool:
    return isinstance(address, str) and is_address(address)


def validate_shares(shares: list[int], total_bps: int = 10_000) -> None:
    """Validate that shares are positive and sum exactly to total_bps."""
    if not shares:
        raise ValueError("There must be at least one beneficiary")
    if any(not isinstance(s, int) or s <= 0 for s in shares):
        raise ValueError("Each share must be an integer greater than 0")
    if sum(shares) != total_bps:
        raise ValueError(
            f"Shares must sum to {total_bps}, got {sum(shares)}"
        )


def validate_beneficiaries(
    beneficiaries: list[str],
    shares: list[int],
    total_bps: int = 10_000,
) -> None:
    """Validate addresses and shares together."""
    if len(beneficiaries) != len(shares):
        raise ValueError(
            "beneficiaries and shares must have the same length "
            f"({len(beneficiaries)} vs {len(shares)})"
        )

    normalized = [normalize_address(b) for b in beneficiaries]
    if len(set(normalized)) != len(normalized):
        raise ValueError("Duplicate addresses found")

    validate_shares(shares, total_bps)
