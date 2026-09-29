"""Claim routes:
- /claim                       -> landing with search
- /claim/{address}             -> splitter home (asks for your address)
- /claim/{address}/consultar   -> shows beneficiary pending
"""

import logging

from fasthtml.common import (
    A,
    Button,
    Div,
    Form,
    H1,
    H2,
    H3,
    Input,
    Label,
    P,
    Script,
    Section,
    Span,
)

from web.clients.chain import ChainReader
from web.clients.relayer import RelayerClient
from web.components.badges import Badge, USDC
from web.components.cards import CopyBox, InfoRow
from web.components.layout import Layout
from web.config import explorer_address_url


log = logging.getLogger(__name__)


def register(rt, chain_reader: ChainReader, relayer_client: RelayerClient,
             known_orders: dict):

    # ==================================================================
    # /claim  (landing with search)
    # ==================================================================
    @rt("/claim")
    def landing():
        return _landing_page(known_orders)

    # ==================================================================
    # /claim/{splitter_address}  (asks for beneficiary address)
    # ==================================================================
    @rt("/claim/{splitter_address}")
    def home(splitter_address: str):
        splitter_address = splitter_address.strip()

        try:
            snap = chain_reader.splitter_snapshot(splitter_address)
        except Exception as e:
            return _error_page(splitter_address, f"Error reading contract: {e}")

        if not snap.get("initialized"):
            return _not_active_page(splitter_address)

        return _claim_home(snap)

    # ==================================================================
    # /claim/{splitter_address}/consultar?beneficiary=0x...
    # ==================================================================
    @rt("/claim/{splitter_address}/consultar")
    def consultar(splitter_address: str, beneficiary: str = ""):
        splitter_address = splitter_address.strip()
        beneficiary = beneficiary.strip()

        try:
            snap = chain_reader.splitter_snapshot(splitter_address)
        except Exception as e:
            return _error_page(splitter_address, f"Error reading contract: {e}")

        if not snap.get("initialized"):
            return _not_active_page(splitter_address)

        if not beneficiary:
            return _error_page(splitter_address, "Missing beneficiary address")

        try:
            b_snap = chain_reader.beneficiary_snapshot(splitter_address, beneficiary)
        except Exception as e:
            return _error_page(splitter_address, f"Error reading beneficiary: {e}")

        if not b_snap.get("is_beneficiary"):
            return _not_beneficiary_page(snap, beneficiary)

        return _beneficiary_page(snap, b_snap, relayer_client)


# ==================================================================
# Pages
# ==================================================================

def _landing_page(known_orders: dict):
    """Landing /claim with search bar."""

    search_script = """
    (function() {
        const input = document.getElementById('search-address');
        const btn = document.getElementById('search-btn');
        const err = document.getElementById('search-error');

        function go() {
            const val = input.value.trim();
            err.style.display = 'none';
            if (!val) {
                err.textContent = 'Enter an address';
                err.style.display = 'block';
                return;
            }
            if (!/^0x[a-fA-F0-9]{40}$/.test(val)) {
                err.textContent = 'Does not look like a valid address (0x + 40 hex)';
                err.style.display = 'block';
                return;
            }
            window.location.href = '/claim/' + val;
        }

        btn.addEventListener('click', go);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') go();
        });
    })();
    """

    examples = []
    for addr, info in list(known_orders.items())[:5]:
        order_id = info.get("order_id") if isinstance(info, dict) else info
        examples.append(
            A(
                "0x" + addr[2:10] + "..." + addr[-4:],
                href=f"/claim/{addr}",
                cls="block text-sm text-blue-400 hover:text-blue-300 no-underline mono mb-1",
            )
        )

    return Layout(
        Section(
            Div(
                Badge("Claim funds", "blue"),
                H1("Find your splitter", cls="text-4xl font-bold mt-4 mb-3"),
                P(
                    "Enter the splitter address the organizer shared with you. "
                    "If you don't have it, ask for it: it's the address where "
                    "payments are distributed.",
                    cls="text-slate-400 mb-8 max-w-2xl",
                ),

                Div(
                    Label("Splitter address",
                          cls="block text-sm font-medium mb-2 text-slate-200"),
                    Div(
                        Input(
                            type="text",
                            id="search-address",
                            placeholder="0x...",
                            cls="flex-1 px-4 py-3 rounded-lg bg-slate-900 border border-slate-700 text-white mono focus:border-blue-500 focus:outline-none transition",
                        ),
                        Button(
                            "Search →",
                            type="button",
                            id="search-btn",
                            cls="ml-2 px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition",
                        ),
                        cls="flex",
                    ),
                    P("", id="search-error",
                      cls="text-sm text-red-400 mt-2 hidden"),
                    cls="mb-8",
                ),

                (
                    Div(
                        H3("Splitters you visited in this session",
                           cls="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-3"),
                        Div(*examples, cls=""),
                        cls="p-6 rounded-xl bg-slate-900 border border-slate-800 mb-8",
                    )
                    if examples
                    else None
                ),

                Div(
                    H3("How do I find my splitter?", cls="font-semibold mb-4"),
                    Div(
                        Div("1", cls="w-8 h-8 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center flex-shrink-0 text-sm"),
                        Div(
                            P("Ask the organizer for the splitter address",
                              cls="font-medium mb-1"),
                            P("It looks like 0x1234...abcd. Whoever created "
                              "the distribution has it.",
                              cls="text-slate-400 text-sm"),
                            cls="ml-4",
                        ),
                        cls="flex items-start mb-4",
                    ),
                    Div(
                        Div("2", cls="w-8 h-8 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center flex-shrink-0 text-sm"),
                        Div(
                            P("Paste it in the search bar above",
                              cls="font-medium mb-1"),
                            P("It will take you to the claim page for that splitter.",
                              cls="text-slate-400 text-sm"),
                            cls="ml-4",
                        ),
                        cls="flex items-start mb-4",
                    ),
                    Div(
                        Div("3", cls="w-8 h-8 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center flex-shrink-0 text-sm"),
                        Div(
                            P("Enter your beneficiary address",
                              cls="font-medium mb-1"),
                            P("We'll show you how much is pending and let you "
                              "claim it.",
                              cls="text-slate-400 text-sm"),
                            cls="ml-4",
                        ),
                        cls="flex items-start",
                    ),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800",
                ),

                cls="max-w-2xl",
            ),
            cls="max-w-7xl mx-auto px-6 py-16",
        ),
        Script(search_script),
        title="Claim · Splitter",
    )


def _claim_home(snap: dict):
    """Page /claim/{address} that asks for the beneficiary address."""
    address = snap["splitter_address"]
    balance = snap["balance_wei"]
    total_released = snap["total_released"]
    relayer_fee = snap["relayer_fee"]
    treasury = snap["treasury"]

    return Layout(
        Section(
            Div(
                Badge("Claim funds", "blue"),
                H1("Claim your funds", cls="text-4xl font-bold mt-4 mb-3"),
                P(
                    "Enter your beneficiary address to see how much belongs "
                    "to you and claim it. Funds always go to your wallet.",
                    cls="text-slate-400 mb-8",
                ),

                Div(
                    H3("Your beneficiary address", cls="font-semibold mb-4"),
                    Form(
                        Div(
                            Label("Address",
                                  cls="block text-sm font-medium mb-2 text-slate-200"),
                            Input(
                                type="text",
                                name="beneficiary",
                                placeholder="0x...",
                                cls="w-full px-4 py-3 rounded-lg bg-slate-900 border border-slate-700 text-white mono focus:border-blue-500 focus:outline-none transition",
                                required=True,
                            ),
                            cls="mb-4",
                        ),
                        Div(
                            A(
                                "Back to splitter",
                                href=f"/split/{address}",
                                cls="px-6 py-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-white no-underline transition",
                            ),
                            Input(
                                type="submit",
                                value="Check →",
                                cls="px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition cursor-pointer",
                            ),
                            cls="flex gap-3 justify-end",
                        ),
                        method="get",
                        action=f"/claim/{address}/consultar",
                    ),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800 mb-10",
                ),

                H2("Splitter status", cls="text-xl font-bold mb-4"),
                Div(
                    Div(
                        P("Balance pending distribution",
                          cls="text-slate-400 text-xs uppercase tracking-wide mb-2"),
                        USDC(balance, "lg"),
                        cls="p-6 rounded-xl bg-slate-900 border border-slate-800",
                    ),
                    Div(
                        P("Already withdrawn in total",
                          cls="text-slate-400 text-xs uppercase tracking-wide mb-2"),
                        USDC(total_released, "lg"),
                        cls="p-6 rounded-xl bg-slate-900 border border-slate-800",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8",
                ),

                Div(
                    H3("Contract details", cls="font-semibold mb-4"),
                    InfoRow("Splitter", address),
                    InfoRow("Treasury", treasury),
                    InfoRow("Relayer fee",
                            f"{relayer_fee / 1_000_000:.2f} USDC"),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800 mb-10",
                ),

                Div(
                    Span("ℹ️ ", cls="text-blue-400"),
                    Span(
                        "You can also claim yourself from any wallet by "
                        "calling release() on the contract. In that case you "
                        "pay no commission, only gas.",
                        cls="text-sm text-blue-200",
                    ),
                    cls="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20",
                ),

                cls="max-w-3xl",
            ),
            cls="max-w-7xl mx-auto px-6 py-12",
        ),
        title="Claim · Splitter",
    )


def _not_active_page(address: str):
    return Layout(
        Section(
            Div(
                Badge("Contract not active", "amber"),
                H1("This splitter is not deployed yet",
                   cls="text-3xl font-bold mt-4 mb-3"),
                P(
                    "The address does not correspond to an active contract. "
                    "Check that you are using the correct address.",
                    cls="text-slate-400 mb-6",
                ),
                CopyBox("Address", address),
                A(
                    "← Back",
                    href="/claim",
                    cls="inline-block px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white no-underline transition",
                ),
                cls="max-w-2xl",
            ),
            cls="max-w-7xl mx-auto px-6 py-16",
        ),
        title="Contract not active · Splitter",
    )


def _not_beneficiary_page(snap: dict, beneficiary: str):
    address = snap["splitter_address"]
    return Layout(
        Section(
            Div(
                Badge("Not a beneficiary", "amber"),
                H1("This address is not part of the distribution",
                   cls="text-3xl font-bold mt-4 mb-3"),
                P(
                    "The address you entered does not appear among the "
                    "beneficiaries of this splitter.",
                    cls="text-slate-400 mb-6",
                ),
                CopyBox("Queried address", beneficiary),
                A(
                    "← Try again",
                    href=f"/claim/{address}",
                    cls="inline-block px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white no-underline transition",
                ),
                cls="max-w-2xl",
            ),
            cls="max-w-7xl mx-auto px-6 py-16",
        ),
        title="Not a beneficiary · Splitter",
    )


def _error_page(address: str, message: str):
    return Layout(
        Section(
            Div(
                Badge("Error", "red"),
                H1("Something went wrong", cls="text-3xl font-bold mt-4 mb-3"),
                P(message, cls="text-slate-400 mb-6"),
                CopyBox("Address", address),
                A(
                    "← Back",
                    href="/claim",
                    cls="inline-block px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white no-underline transition",
                ),
                cls="max-w-2xl",
            ),
            cls="max-w-7xl mx-auto px-6 py-16",
        ),
        title="Error · Splitter",
    )


def _beneficiary_page(snap: dict, b_snap: dict, relayer_client: RelayerClient):
    address = snap["splitter_address"]
    beneficiary = b_snap["beneficiary"]
    share_bps = b_snap["share_bps"]
    pending = b_snap["pending_wei"]
    released = b_snap["released_wei"]
    relayer_fee = snap["relayer_fee"]

    applied_fee = min(relayer_fee, pending) if pending > 0 else 0
    net = pending - applied_fee
    can_claim = pending > 0

    explorer_url = explorer_address_url(address)

    script = f"""
    const splitterAddr = "{address}";
    const beneficiaryAddr = "{beneficiary}";

    async function doRelay() {{
        const btn = document.getElementById('relay-btn');
        const status = document.getElementById('relay-status');
        btn.disabled = true;
        btn.innerText = 'Claiming...';
        status.innerHTML = '<span class="text-amber-400">●</span> Signing transaction...';
        try {{
            const r = await fetch('/api/relay', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    splitter_address: splitterAddr,
                    beneficiary: beneficiaryAddr,
                }}),
            }});
            const data = await r.json();
            if (r.ok) {{
                status.innerHTML = '<span class="text-emerald-400">●</span> Claimed. Redirecting...';
                setTimeout(() => window.location.reload(), 2000);
            }} else {{
                status.innerHTML = '<span class="text-red-400">●</span> Error: ' + (data.error || 'unknown');
                btn.disabled = false;
                btn.innerText = 'Retry claim';
            }}
        }} catch (e) {{
            status.innerHTML = '<span class="text-red-400">●</span> Network error: ' + e.message;
            btn.disabled = false;
            btn.innerText = 'Retry claim';
        }}
    }}

    document.addEventListener('DOMContentLoaded', () => {{
        const btn = document.getElementById('relay-btn');
        if (btn) btn.addEventListener('click', doRelay);
    }});
    """

    return Layout(
        Section(
            Div(
                Badge("Beneficiary", "green"),
                H1("Your share of the distribution", cls="text-4xl font-bold mt-4 mb-3"),
                P(
                    f"Address: {beneficiary[:6]}...{beneficiary[-4:]}",
                    cls="text-slate-400 mb-8 mono text-sm",
                ),

                Div(
                    Div(
                        P("Pending claim",
                          cls="text-slate-400 text-xs uppercase tracking-wide mb-2"),
                        USDC(pending, "xl"),
                        cls="p-6 rounded-xl bg-slate-900 border border-amber-500/30",
                    ),
                    Div(
                        P("Already claimed",
                          cls="text-slate-400 text-xs uppercase tracking-wide mb-2"),
                        USDC(released, "lg"),
                        cls="p-6 rounded-xl bg-slate-900 border border-slate-800",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8",
                ),

                Div(
                    H3("Details", cls="font-semibold mb-4"),
                    InfoRow("Your share", f"{share_bps / 100:.2f}%"),
                    InfoRow("Relayer fee",
                            f"{applied_fee / 1_000_000:.2f} USDC" if can_claim else "—"),
                    InfoRow("You will receive",
                            f"{net / 1_000_000:.2f} USDC" if can_claim else "—",
                            accent=True),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800 mb-8",
                ),

                (
                    Div(
                        H3("Claim", cls="font-semibold mb-4"),
                        Div(
                            Span("● ", cls="text-slate-400"),
                            Span("Ready to claim", cls="text-sm", id="relay-status"),
                            cls="flex items-center gap-2 mb-4",
                        ),
                        Div(
                            A(
                                "Claim with relayer →",
                                href="#",
                                id="relay-btn",
                                cls="inline-block px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium no-underline transition cursor-pointer",
                            ),
                            cls="",
                        ),
                        P(
                            "The relayer signs the transaction for you and "
                            "charges the fee shown above. Funds go straight "
                            "to your wallet.",
                            cls="text-xs text-slate-500 mt-4",
                        ),
                        cls="p-6 rounded-xl bg-blue-500/5 border border-blue-500/20 mb-8",
                    )
                    if can_claim
                    else Div(
                        H3("Nothing to claim", cls="font-semibold mb-3"),
                        P(
                            "You have no pending funds in this splitter. "
                            "If you expect payments, check that the organizer "
                            "has already deposited USDC.",
                            cls="text-slate-400 text-sm",
                        ),
                        cls="p-6 rounded-xl bg-slate-900 border border-slate-800 mb-8",
                    )
                ),

                Div(
                    H3("Claim without relayer", cls="font-semibold mb-3"),
                    P(
                        "If you prefer not to pay the relayer fee, you can "
                        "call the contract directly from any wallet using "
                        "the release() function. You only pay gas.",
                        cls="text-slate-400 text-sm mb-4",
                    ),
                    CopyBox("Splitter contract", address),
                    A(
                        "View contract on explorer ↗",
                        href=explorer_url,
                        target="_blank",
                        rel="noopener noreferrer",
                        cls="inline-block text-sm text-blue-400 hover:text-blue-300 no-underline mb-3",
                    ),
                    CopyBox("Function to call", "release(address)"),
                    P(
                        f"As the parameter, enter your address: {beneficiary}",
                        cls="text-xs text-slate-500",
                    ),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800 mb-8",
                ),

                Div(
                    A(
                        "← Back to splitter",
                        href=f"/split/{address}",
                        cls="text-sm text-blue-400 hover:text-blue-300 no-underline",
                    ),
                ),

                Script(script),

                cls="max-w-3xl",
            ),
            cls="max-w-7xl mx-auto px-6 py-12",
        ),
        title="Claim · Splitter",
    )
