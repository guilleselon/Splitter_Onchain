"""Tables for beneficiaries and events."""

from fasthtml.common import A, Div, Span, Table, Tbody, Td, Th, Thead, Tr

from web.components.badges import Badge, ShortAddr


def BeneficiaryTableRow(
    address: str,
    share_bps: int,
    released_wei: int,
    pending_wei: int,
    show_action: bool = True,
):
    return Tr(
        Td(ShortAddr(address), cls="py-4 text-sm mono text-slate-300"),
        Td(f"{share_bps/100:.2f}%", cls="py-4 text-sm text-right mono"),
        Td(
            f"{released_wei / 1_000_000:,.2f}",
            cls="py-4 text-sm text-right mono text-slate-400",
        ),
        Td(
            f"{pending_wei / 1_000_000:,.2f}",
            cls="py-4 text-sm text-right mono text-amber-400",
        ),
        (
            Td(
                A(
                    "Claim →",
                    href=f"/claim/{address}",
                    cls="text-xs px-3 py-1.5 rounded-lg bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 no-underline transition",
                ),
                cls="py-4 text-right",
            )
            if show_action
            else Td("", cls="py-4")
        ),
        cls="border-t border-slate-800",
    )


def BeneficiariesTable(rows: list[dict], show_action: bool = True):
    """
    rows: list of dicts with keys:
        - address
        - share_bps
        - released_wei
        - pending_wei
    """
    return Table(
        Thead(
            Tr(
                Th("Beneficiary", cls="text-left text-xs text-slate-400 font-medium pb-3"),
                Th("Share", cls="text-right text-xs text-slate-400 font-medium pb-3"),
                Th("Released", cls="text-right text-xs text-slate-400 font-medium pb-3"),
                Th("Pending", cls="text-right text-xs text-slate-400 font-medium pb-3"),
                Th("", cls="text-right text-xs text-slate-400 font-medium pb-3"),
            )
        ),
        Tbody(
            *[
                BeneficiaryTableRow(
                    address=r["address"],
                    share_bps=r["share_bps"],
                    released_wei=r["released_wei"],
                    pending_wei=r["pending_wei"],
                    show_action=show_action,
                )
                for r in rows
            ]
        ),
        cls="w-full",
    )


def EventRow(event_type: str, amount_wei: int, tx_hash: str, date: str = ""):
    icons = {"PaymentReceived": "↓", "PaymentReleased": "↑"}
    colors = {
        "PaymentReceived": "text-emerald-400",
        "PaymentReleased": "text-blue-400",
    }
    return Div(
        Span(
            icons.get(event_type, "•"),
            cls=f"text-lg {colors.get(event_type, 'text-slate-400')}",
        ),
        Div(
            Span(event_type, cls="text-sm font-medium"),
            Span(f" · {date}" if date else "", cls="text-xs text-slate-500 ml-2"),
            cls="flex items-center",
        ),
        Div(
            Span(f"{amount_wei / 1_000_000:,.2f} USDC", cls="text-sm mono"),
            Div(tx_hash, cls="text-xs text-slate-500 mono"),
            cls="text-right",
        ),
        cls="flex items-center gap-4 p-4",
    )


def EventsList(events: list[dict]):
    """
    events: list of dicts with keys:
        - type
        - amount_wei
        - tx_hash
        - date (optional)
    """
    if not events:
        return Div(
            Span("No events yet", cls="text-slate-500 text-sm"),
            cls="p-6 text-center rounded-xl bg-slate-900 border border-slate-800",
        )
    return Div(
        *[
            EventRow(
                event_type=e["type"],
                amount_wei=e["amount_wei"],
                tx_hash=e["tx_hash"],
                date=e.get("date", ""),
            )
            for e in events
        ],
        cls="rounded-xl bg-slate-900 border border-slate-800 divide-y divide-slate-800",
    )
