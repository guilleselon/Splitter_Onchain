"""Reusable cards: FeatureCard, StatCard, SplitterCard, InfoRow, CopyBox."""

from fasthtml.common import A, Div, H3, P, Span

from web.components.badges import Badge, ShortAddr, USDC


def FeatureCard(icon: str, title: str, desc: str):
    return Div(
        Div(icon, cls="text-3xl mb-4"),
        H3(title, cls="text-lg font-semibold mb-2"),
        P(desc, cls="text-slate-400 text-sm leading-relaxed"),
        cls="p-6 rounded-xl bg-slate-900 border border-slate-800 card-hover",
    )


def StatCard(label: str, value, color: str = "blue"):
    colors = {
        "blue": "text-blue-400",
        "green": "text-emerald-400",
        "amber": "text-amber-400",
        "purple": "text-purple-400",
    }
    cls = colors.get(color, colors["blue"])
    return Div(
        P(label, cls="text-slate-400 text-xs uppercase tracking-wide mb-2"),
        P(str(value), cls=f"text-2xl font-bold mono {cls}"),
        cls="p-5 rounded-xl bg-slate-900 border border-slate-800",
    )


def InfoRow(label: str, value, accent: bool = False):
    cls = "text-sm mono text-amber-400" if accent else "text-sm mono text-slate-200"
    return Div(
        Span(label, cls="text-slate-400 text-sm"),
        Span(str(value), cls=cls),
        cls="flex justify-between py-2 border-b border-slate-800 last:border-b-0",
    )


def CopyBox(label: str, value: str):
    return Div(
        Div(label, cls="text-xs text-slate-500 uppercase tracking-wide mb-2"),
        Div(
            Span(value, cls="text-sm text-white mono break-all"),
            cls="p-4 rounded-lg bg-slate-950 border border-slate-800",
        ),
        cls="mb-4",
    )


def SplitterCard(
    splitter_address: str,
    total_received_wei: int,
    pending_wei: int,
    network: str = "Monad",
):
    return A(
        Div(
            Div(
                Span("Splitter", cls="font-semibold text-white"),
                Badge(network, "blue"),
                cls="flex items-center gap-3 mb-1",
            ),
            ShortAddr(splitter_address),
            cls="flex-1",
        ),
        Div(
            Div(
                Span("Received: ", cls="text-slate-400 text-sm"),
                USDC(total_received_wei),
                cls="text-right",
            ),
            Div(
                Span("Pending: ", cls="text-slate-400 text-sm"),
                USDC(pending_wei),
                cls="text-right",
            ),
            cls="text-right",
        ),
        cls="flex justify-between items-center p-5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition",
        href=f"/split/{splitter_address}",
    )
