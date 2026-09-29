"""Route /split/{address}: public splitter page."""

from fasthtml.common import (
    A,
    Button,
    Div,
    H1,
    H2,
    H3,
    P,
    Script,
    Section,
    Span,
)

from web.clients.chain import ChainReader
from web.components.badges import Badge, ShortAddr, USDC
from web.components.cards import CopyBox, InfoRow
from web.components.layout import Layout
from web.config import explorer_address_url, get_explorer_base


PAGE_SCRIPT = """
(function() {
    // --- Copy splitter address ---
    function copyAddress() {
        const addr = document.getElementById('splitter-address').innerText.trim();
        navigator.clipboard.writeText(addr).then(() => {
            const btn = document.getElementById('copy-btn');
            const original = btn.innerText;
            btn.innerText = '✓ Copied';
            btn.classList.add('text-emerald-400');
            setTimeout(() => {
                btn.innerText = original;
                btn.classList.remove('text-emerald-400');
            }, 1500);
        }).catch(err => console.error('Copy error:', err));
    }

    // --- Copy claim share link ---
    function copyShareLink() {
        const url = document.getElementById('share-url').innerText.trim();
        navigator.clipboard.writeText(url).then(() => {
            const btn = document.getElementById('share-btn');
            const original = btn.innerText;
            btn.innerText = '✓ Link copied';
            btn.classList.add('text-emerald-400');
            setTimeout(() => {
                btn.innerText = original;
                btn.classList.remove('text-emerald-400');
            }, 1500);
        }).catch(err => console.error('Copy error:', err));
    }

    // --- Copy individual beneficiary link ---
    function copyBeneficiaryLink(btn) {
        const addr = btn.id.replace('copy-', '');
        if (!addr) return;
        const url = window.location.origin + '/claim/' + addr;
        navigator.clipboard.writeText(url).then(() => {
            const original = btn.innerText;
            btn.innerText = '✓';
            btn.classList.add('text-emerald-400');
            setTimeout(() => {
                btn.innerText = original;
                btn.classList.remove('text-emerald-400');
            }, 1500);
        }).catch(err => console.error('Copy error:', err));
    }

    // --- Claim link QR ---
    function initShareQR() {
        const container = document.getElementById('share-qr');
        const urlEl = document.getElementById('share-url');
        if (!container || !urlEl) return;
        new QRCode(container, {
            text: urlEl.innerText.trim(),
            width: 220,
            height: 220,
            colorDark: '#020617',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.M,
        });
    }

    // --- Splitter address QR ---
    function initAddressQR() {
        const container = document.getElementById('qr-container');
        const addrEl = document.getElementById('splitter-address');
        if (!container || !addrEl) return;
        new QRCode(container, {
            text: addrEl.innerText.trim(),
            width: 180,
            height: 180,
            colorDark: '#020617',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.M,
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        const btn = document.getElementById('copy-btn');
        if (btn) btn.addEventListener('click', copyAddress);

        const shareBtn = document.getElementById('share-btn');
        if (shareBtn) shareBtn.addEventListener('click', copyShareLink);

        // Beneficiary buttons — use class selector, always works
        document.querySelectorAll('.copy-beneficiary-btn').forEach(el => {
            el.addEventListener('click', function() {
                copyBeneficiaryLink(this);
            });
        });

        initAddressQR();
        initShareQR();
    });
})();
"""


def register(rt, chain_reader: ChainReader, known_orders: dict,
             web_public_url: str):

    @rt("/split/{address}")
    def get(address: str):
        try:
            address = address.strip()
            snap = chain_reader.splitter_snapshot(address)
        except Exception as e:
            return _not_found_page(address, f"error reading contract: {e}")

        if not snap.get("initialized"):
            return _pending_page(address)

        return _splitter_page(snap, known_orders, web_public_url)


def _pending_page(address: str):
    return Layout(
        Section(
            Div(
                Badge("Pending deployment", "amber"),
                H1("The contract is not active yet", cls="text-3xl font-bold mt-4 mb-3"),
                P(
                    "This is the splitter address, but the contract has not "
                    "been deployed yet. It will become active as soon as the "
                    "deployer detects the fee payment.",
                    cls="text-slate-400 mb-6",
                ),
                CopyBox("Address", address),
                A(
                    "← Back",
                    href="/create",
                    cls="inline-block px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white no-underline transition",
                ),
                cls="max-w-2xl",
            ),
            cls="max-w-7xl mx-auto px-6 py-16",
        ),
        title="Pending · Splitter",
    )


def _not_found_page(address: str, message: str):
    return Layout(
        Section(
            Div(
                Badge("Not found", "red"),
                H1("Could not read the splitter", cls="text-3xl font-bold mt-4 mb-3"),
                P(message, cls="text-slate-400 mb-6"),
                CopyBox("Address", address),
                A(
                    "← Back to home",
                    href="/",
                    cls="inline-block px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white no-underline transition",
                ),
                cls="max-w-2xl",
            ),
            cls="max-w-7xl mx-auto px-6 py-16",
        ),
        title="Not found · Splitter",
    )


def _splitter_page(snap: dict, known_orders: dict, web_public_url: str):
    address = snap["splitter_address"]
    balance = snap["balance_wei"]
    total_released = snap["total_released"]
    total_shares = snap["total_shares"]
    relayer_fee = snap["relayer_fee"]
    treasury = snap["treasury"]

    info = known_orders.get(address.lower())
    order_id = None
    beneficiaries = []
    shares = []
    if isinstance(info, dict):
        order_id = info.get("order_id")
        beneficiaries = info.get("beneficiaries", [])
        shares = info.get("shares", [])
    elif isinstance(info, str):
        order_id = info

    share_url = f"{web_public_url.rstrip('/')}/claim/{address}"
    explorer_url = explorer_address_url(address)
    explorer_name = "Monadscan" if "monadscan.com" in get_explorer_base() else "Explorer"

    share_block = None
    if beneficiaries:
        rows = []
        for ben, sh in zip(beneficiaries, shares):
            rows.append(
                Div(
                    Div(
                        ShortAddr(ben),
                        Span(f"{sh/100:.2f}%", cls="text-xs text-slate-500 mono ml-2"),
                        cls="flex items-center gap-2",
                    ),
                    Button(
                        "Copy link",
                        type="button",
                        id=f"copy-{ben}",
                        cls="copy-beneficiary-btn px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition",
                    ),
                    cls="flex items-center justify-between py-2 border-b border-slate-800 last:border-b-0",
                )
            )
        share_block = Div(
            Div(
                Div(
                    H3("Share with beneficiaries", cls="font-semibold mb-4"),
                    P(
                        "Send this link to beneficiaries so they can claim "
                        "their share. You can also copy individual links.",
                        cls="text-slate-400 text-sm mb-4",
                    ),
                    Div(
                        Div(
                            Span(share_url, cls="text-sm text-white mono break-all", id="share-url"),
                            cls="flex-1",
                        ),
                        Button(
                            "Copy link",
                            type="button",
                            id="share-btn",
                            cls="ml-3 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition whitespace-nowrap",
                        ),
                        cls="flex items-start justify-between p-4 rounded-lg bg-slate-950 border border-slate-800",
                    ),
                    cls="flex-1",
                ),
                Div(
                    Div(id="share-qr", cls="bg-white p-2 rounded-lg inline-block"),
                    P("Scan to claim", cls="text-xs text-slate-500 text-center mt-3"),
                    cls="flex flex-col items-center",
                ),
                cls="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-6 items-start mb-6",
            ),
            Div(
                H3("Individual links", cls="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-3"),
                Div(*rows, cls=""),
            ),
            cls="p-6 rounded-xl bg-emerald-500/5 border border-emerald-500/20 mb-10",
        )

    return Layout(
        Script(src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"),

        Section(
            Div(
                Badge("Contract active on Monad", "green"),
                H1("Splitter", cls="text-4xl font-bold mt-4 mb-3"),

                Div(
                    Span("Address: ", cls="text-slate-500 text-sm"),
                    A(
                        address,
                        href=explorer_url,
                        target="_blank",
                        rel="noopener noreferrer",
                        cls="text-sm mono text-blue-400 hover:text-blue-300 no-underline break-all",
                    ),
                    Span(" ↗", cls="text-blue-400 text-xs"),
                    cls="flex flex-wrap gap-1 items-center mb-2",
                ),

                (
                    Div(
                        Span("Order ID: ", cls="text-slate-500 text-sm"),
                        Span(order_id, cls="text-sm mono text-slate-300"),
                        cls="flex flex-wrap gap-1 items-center mb-2",
                    )
                    if order_id
                    else None
                ),

                A(
                    f"View contract on {explorer_name} ↗",
                    href=explorer_url,
                    target="_blank",
                    rel="noopener noreferrer",
                    cls="inline-block mt-3 text-sm px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 no-underline transition",
                ),

                cls="mb-8",
            ),

            Div(
                Div(
                    P("Current balance", cls="text-slate-400 text-xs uppercase tracking-wide mb-2"),
                    USDC(balance, "lg"),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800",
                ),
                Div(
                    P("Already withdrawn", cls="text-slate-400 text-xs uppercase tracking-wide mb-2"),
                    USDC(total_released, "lg"),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800",
                ),
                Div(
                    P("Total received", cls="text-slate-400 text-xs uppercase tracking-wide mb-2"),
                    USDC(balance + total_released, "lg"),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800",
                ),
                Div(
                    P("Total shares", cls="text-slate-400 text-xs uppercase tracking-wide mb-2"),
                    P(f"{total_shares / 100:.2f}%", cls="text-2xl font-bold mono text-purple-400"),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800",
                ),
                cls="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10",
            ),

            Div(
                H3("Details", cls="font-semibold mb-4"),
                InfoRow("Token", "USDC"),
                InfoRow("Treasury", treasury),
                InfoRow("Relayer fee", f"{relayer_fee / 1_000_000:.2f} USDC"),
                cls="p-6 rounded-xl bg-slate-900 border border-slate-800 mb-10",
            ),

            share_block,

            Div(
                H2("Deposit USDC", cls="text-xl font-bold mb-4"),
                P(
                    "Anyone can send USDC to the splitter address. "
                    "Funds are distributed according to the fixed shares.",
                    cls="text-slate-400 text-sm mb-6",
                ),
                Div(
                    Div(
                        Div(
                            Div(id="qr-container", cls="bg-white p-2 rounded-lg inline-block"),
                            cls="flex justify-center",
                        ),
                        P("Scan with your wallet",
                          cls="text-xs text-slate-500 text-center mt-3"),
                        cls="flex flex-col items-center",
                    ),
                    Div(
                        Div("Splitter address",
                            cls="text-xs text-slate-500 uppercase tracking-wide mb-2"),
                        Div(
                            Div(
                                Span(address, cls="text-sm text-white mono break-all", id="splitter-address"),
                                cls="flex-1",
                            ),
                            Button(
                                "Copy",
                                type="button",
                                id="copy-btn",
                                cls="ml-3 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition whitespace-nowrap",
                            ),
                            cls="flex items-start justify-between p-4 rounded-lg bg-slate-950 border border-slate-800",
                        ),
                        cls="flex-1",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-[auto_1fr] gap-6 items-start",
                ),
                cls="p-6 rounded-xl bg-slate-900 border border-slate-800 mb-10",
            ),

            Div(
                H3("Are you a beneficiary?", cls="font-semibold mb-3"),
                P(
                    "You can claim your funds yourself from any wallet, "
                    "or let someone do it for you (relayer). Funds always go "
                    "to your wallet.",
                    cls="text-slate-400 text-sm mb-4",
                ),
                A(
                    "Go to claim page →",
                    href=f"/claim/{address}",
                    cls="inline-block px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium no-underline transition",
                ),
                cls="p-6 rounded-xl bg-blue-500/5 border border-blue-500/20 mb-10",
            ),

            cls="max-w-5xl",
        ),

        Script(PAGE_SCRIPT),

        title=f"Splitter {address[:8]}... · Splitter",
    )
