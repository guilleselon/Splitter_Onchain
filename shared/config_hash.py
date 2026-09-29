"""Canonical config hash for a splitter.

The hash is deterministic regardless of the order of beneficiaries.
It is used as the CREATE2 salt so that the splitter address is
predictable before deployment.
"""

from eth_utils import keccak

from shared.validation import normalize_address

# Payload layout:
#   for each beneficiary (sorted ascending by address):
#       address (20 bytes) || share_bps (4 bytes, big-endian)
#   nonce (32 bytes, big-endian)
#
# The payload is hashed with keccak256 -> 32 bytes used as the salt.


def _encode_config(
    beneficiaries: list[str],
    shares: list[int],
    nonce: int,
) -> bytes:
    if len(beneficiaries) != len(shares):
        raise ValueError("beneficiaries and shares must have the same length")
    if not isinstance(nonce, int) or nonce < 0:
        raise ValueError("nonce must be a non-negative integer")
    if nonce >= 2**256:
        raise ValueError("nonce must fit in 32 bytes")

    # Normalize addresses and sort by address (lowercase) so the
    # hash is independent of the input order.
    pairs = sorted(
        (
            normalize_address(b).lower(),
            s,
        )
        for b, s in zip(beneficiaries, shares)
    )

    payload = b""
    for addr_lower, share in pairs:
        addr_bytes = bytes.fromhex(addr_lower[2:])
        if len(addr_bytes) != 20:
            raise ValueError(f"Malformed address: {addr_lower}")
        if not (0 <= share < 2**32):
            raise ValueError(f"share out of range: {share}")
        payload += addr_bytes + share.to_bytes(4, "big")

    payload += nonce.to_bytes(32, "big")
    return payload


def hash_config(
    beneficiaries: list[str],
    shares: list[int],
    nonce: int,
) -> bytes:
    """Return the keccak256 of the config as bytes (32)."""
    return keccak(_encode_config(beneficiaries, shares, nonce))


def hash_config_hex(
    beneficiaries: list[str],
    shares: list[int],
    nonce: int,
) -> str:
    """Same as hash_config but returns a hex string 0x..."""
    return "0x" + hash_config(beneficiaries, shares, nonce).hex()
