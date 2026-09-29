"""Formatting utilities for USDC, addresses and basis points."""

from decimal import Decimal, ROUND_DOWN


def format_usdc(amount: Decimal | float | int, decimals: int = 2) -> str:
    """Format a USDC amount with thousands separator and fixed decimals."""
    d = Decimal(str(amount)).quantize(
        Decimal("0." + "0" * decimals), rounding=ROUND_DOWN
    )
    return f"{d:,.{decimals}f}"


def parse_usdc(text: str) -> Decimal:
    """Convert '1,234.56 USDC' into Decimal('1234.56')."""
    cleaned = (
        text.replace(",", "")
        .replace(" ", "")
        .replace("USDC", "")
        .strip()
    )
    return Decimal(cleaned)


def short_address(address: str, chars: int = 6) -> str:
    """Shorten to 0x1234...abcd. Return the full address if already short."""
    if not address or len(address) <= chars * 2 + 2:
        return address
    return f"{address[:chars]}...{address[-4:]}"


def parse_bps(percent: float | Decimal | str) -> int:
    """Convert a percentage (e.g. 40.00) to basis points (4000)."""
    return int((Decimal(str(percent)) * 100).to_integral_value())


def format_bps(bps: int) -> str:
    """Convert basis points to a readable percentage (e.g. 4000 -> '40.00%')."""
    return f"{bps / 100:.2f}%"
