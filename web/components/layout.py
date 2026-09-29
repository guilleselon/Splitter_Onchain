"""Base layout: SiteNav, SiteFooter, Layout."""

from fasthtml.common import (
    A,
    Body,
    Div,
    Footer,
    H4,
    Header,
    Li,
    Link,
    Main,
    Nav,
    P,
    Script,
    Span,
    Style,
    Title,
    Ul,
)


GLOBAL_STYLE = """
body { font-family: 'Inter', sans-serif; background-color: #020617; }
.mono { font-family: 'JetBrains Mono', monospace; }
.gradient-text {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.card-hover { transition: transform .15s ease, box-shadow .15s ease; }
.card-hover:hover { transform: translateY(-2px); box-shadow: 0 12px 32px -12px rgba(59,130,246,.35); }
"""


def _head_assets():
    return [
        Script(src="https://cdn.tailwindcss.com"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap",
        ),
        Style(GLOBAL_STYLE),
    ]


def SiteNav():
    return Header(
        Div(
            A(
                Span("⬢", cls="text-2xl text-blue-400 mr-2"),
                Span("Splitter", cls="font-bold text-xl tracking-tight"),
                href="/",
                cls="flex items-center no-underline text-white",
            ),
            Nav(
                A("How it works", href="/how-it-works",
                  cls="text-slate-300 hover:text-white px-3 py-2 text-sm no-underline"),
                A("Claim", href="/claim",
                  cls="text-emerald-300 hover:text-emerald-200 px-3 py-2 text-sm no-underline font-medium"),
                A("Security", href="/docs/security",
                  cls="text-slate-300 hover:text-white px-3 py-2 text-sm no-underline"),
                A("FAQ", href="/docs/faq",
                  cls="text-slate-300 hover:text-white px-3 py-2 text-sm no-underline"),
                cls="hidden md:flex items-center gap-1",
            ),
            A(
                "Create splitter",
                href="/create",
                cls="text-sm px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium no-underline transition",
            ),
            cls="max-w-7xl mx-auto flex items-center justify-between px-6 py-4",
        ),
        cls="sticky top-0 z-50 bg-slate-950/80 backdrop-blur border-b border-slate-800",
    )


def SiteFooter():
    return Footer(
        Div(
            Div(
                Div(
                    Span("⬢", cls="text-2xl text-blue-400 mr-2"),
                    Span("Splitter", cls="font-bold text-lg"),
                    cls="flex items-center mb-3",
                ),
                P(
                    "Distribute USDC payments on Monad. Immutable. Non-custodial. No KYC.",
                    cls="text-slate-400 text-sm max-w-xs",
                ),
            ),
            Div(
                H4("Product", cls="font-semibold text-sm mb-3 text-white"),
                Ul(
                    Li(A("Create splitter", href="/create",
                         cls="text-slate-400 hover:text-white text-sm no-underline")),
                    Li(A("Claim funds", href="/claim",
                         cls="text-emerald-400 hover:text-emerald-300 text-sm no-underline")),
                    Li(A("How it works", href="/how-it-works",
                         cls="text-slate-400 hover:text-white text-sm no-underline")),
                    cls="space-y-2 list-none p-0",
                ),
            ),
            Div(
                H4("Trust", cls="font-semibold text-sm mb-3 text-white"),
                Ul(
                    Li(A("Security", href="/docs/security",
                         cls="text-slate-400 hover:text-white text-sm no-underline")),
                    Li(A("FAQ", href="/docs/faq",
                         cls="text-slate-400 hover:text-white text-sm no-underline")),
                    cls="space-y-2 list-none p-0",
                ),
            ),
            Div(
                H4("Legal", cls="font-semibold text-sm mb-3 text-white"),
                Ul(
                    Li(A("Terms", href="#",
                         cls="text-slate-400 hover:text-white text-sm no-underline")),
                    Li(A("Privacy", href="#",
                         cls="text-slate-400 hover:text-white text-sm no-underline")),
                    cls="space-y-2 list-none p-0",
                ),
            ),
            cls="grid grid-cols-2 md:grid-cols-4 gap-8",
        ),
        Div(
            P(
                "© 2026 Splitter. Immutable contracts on Monad. USDC. Non-custodial.",
                cls="text-slate-500 text-xs text-center mt-8 pt-6 border-t border-slate-800",
            ),
            cls="max-w-7xl mx-auto px-6 py-12",
        ),
        cls="bg-slate-950 border-t border-slate-800 mt-20",
    )


def Layout(*content, title: str = "Splitter"):
    return (
        Title(title),
        *_head_assets(),
        Body(
            SiteNav(),
            Main(*content, cls="min-h-screen bg-slate-950 text-slate-100"),
            SiteFooter(),
            cls="bg-slate-950",
        ),
    )
