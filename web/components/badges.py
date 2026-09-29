"""Small reusable components: Badge, ShortAddr, USDC."""

from decimal import Decimal

from fasthtml.common import Span


def Badge(text: str, color: str = "blue"):
    colors = {
        "blue": "bg-blue-500/10 text-blue-400 border-blue-500/20",
        "green": "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        "amber": "bg-amber-500/10 text-amber-400 border-amber-500/20",
        "slate": "bg-slate-500/10 text-slate-400 border-slate-500/20",
        "purple": "bg-purple-500/10 text-purple-400 border-purple-500/20",
        "red": "bg-red-500/10 text-red-400 border-red-500/20",
    }
    cls = colors.get(color, colors["blue"])
    return Span(
        text,
        cls=f"inline-block px-2.5 py-1 rounded-md text-xs font-medium border {cls}",
    )


def ShortAddr(addr: str | None, chars: int = 6):
    """0x1234...abcd, or '—' if no address."""
    if not addr:
        return Span("—", cls="text-slate-500")
    if len(addr) <= chars * 2 + 2:
        return Span(addr, cls="mono text-sm")
    return Span(
        f"{addr[:chars]}...{addr[-4:]}",
        cls="mono text-sm",
    )


def USDC(amount_wei: int, size: str = "base"):
    """
    Display a USDC amount, formatted.

    amount_wei: integer in the smallest unit of USDC (6 decimals).
    """
    sizes = {
        "base": "text-base",
        "lg": "text-2xl",
        "xl": "text-4xl",
    }
    d = Decimal(amount_wei) / Decimal(1_000_000)
    formatted = f"{d:,.2f}"
    return Span(
        Span(formatted, cls=f"{sizes[size]} font-bold mono"),
        Span(" USDC", cls="text-slate-400 text-sm ml-1"),
        cls="inline-flex items-baseline",
    )


def USDCFromFloat(amount: float, size: str = "base"):
    """Same as USDC but takes the amount already in human units."""
    sizes = {
        "base": "text-base",
        "lg": "text-2xl",
        "xl": "text-4xl",
    }
    formatted = f"{Decimal(str(amount)):,.2f}"
    return Span(
        Span(formatted, cls=f"{sizes[size]} font-bold mono"),
        Span(" USDC", cls="text-slate-400 text-sm ml-1"),
        cls="inline-flex items-baseline",
    )
