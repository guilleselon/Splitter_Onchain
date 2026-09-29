"""Route /request: receives the config, calls the deployer and shows
payment instructions."""

import logging
from decimal import Decimal

from fasthtml.common import (
    A,
    Button,
    Div,
    H1,
    H3,
    P,
    Script,
    Section,
    Span,
    Table,
    Tbody,
    Td,
    Th,
    Thead,
    Tr,
)

from web.clients.deployer import DeployerClient, DeployerError
from web.components.badges import Badge, ShortAddr
from web.components.cards import CopyBox, InfoRow
from web.components.layout import Layout


log = logging.getLogger(__name__)


def register(rt, deployer_client: DeployerClient, relayer_fee_wei: int,
             treasury_address: str, known_orders: dict):

    @rt("/request", methods=["POST"])
    async def post(request):
        form = await request.form()

        beneficiaries = []
        shares_bps = []
        i = 0
        while True:
            addr_key = f"beneficiaries[{i}][address]"
            pct_key = f"beneficiaries[{i}][percent]"
            if addr_key not in form:
                break
            addr = (form.get(addr_key) or "").strip()
            pct = (form.get(pct_key) or "").strip()
            if addr:
                try:
                    pct_float = Decimal(pct) if pct else Decimal("0")
                except Exception:
                    pct_float = Decimal("0")
                beneficiaries.append(addr)
                shares_bps.append(int(pct_float * 100))
            i += 1

        if not beneficiaries:
            return _error_page("At least one beneficiary is required")

        if sum(shares_bps) != 10_000:
            total = sum(shares_bps) / 100
            return _error_page(
                f"Percentages must sum to 100.00%. Currently they sum to {total:.2f}%"
            )

        try:
            order = deployer_client.create_order(
                beneficiaries=beneficiaries,
                shares=shares_bps,
                treasury=treasury_address,
                relayer_fee=relayer_fee_wei,
            )
        except DeployerError as e:
            log.error("Deployer rejected the order: %s", e)
            return _error_page(f"Error creating the order: {e}")

        known_orders[order["predicted_splitter_address"].lower()] = {
            "order_id": order["order_id"],
            "beneficiaries": beneficiaries,
            "shares": shares_bps,
        }

        return _request_page(order, beneficiaries, shares_bps)


def _request_page(order: dict, beneficiaries: list[str], shares_bps: list[int]):
    order_id = order["order_id"]
    payment_address = order["payment_address"]
    fee_usdc = order["fee_usdc"]

    rows = [
        Tr(
            Td(ShortAddr(b), cls="py-3 text-sm mono text-slate-300"),
            Td(f"{s/100:.2f}%", cls="py-3 text-sm text-right mono"),
            cls="border-t border-slate-800",
        )
        for b, s in zip(beneficiaries, shares_bps)
    ]

    page_script = f"""
    const orderId = "{order_id}";
    const splitterAddr = "{payment_address}";
    let checks = 0;
    const MAX_CHECKS = 60;
    let intervalId = null;

    function copyAddress() {{
        const addr = document.getElementById('payment-address').innerText.trim();
        navigator.clipboard.writeText(addr).then(() => {{
            const btn = document.getElementById('copy-btn');
            const original = btn.innerText;
            btn.innerText = '✓ Copied';
            btn.classList.add('text-emerald-400');
            setTimeout(() => {{
                btn.innerText = original;
                btn.classList.remove('text-emerald-400');
            }}, 1500);
        }}).catch(err => console.error('Copy error:', err));
    }}

    function initQR() {{
        const container = document.getElementById('qr-container');
        if (!container) return;
        new QRCode(container, {{
            text: splitterAddr,
            width: 180,
            height: 180,
            colorDark: '#020617',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.M,
        }});
    }}

    async function checkStatus() {{
        try {{
            const r = await fetch('/api/order/' + orderId);
            const data = await r.json();
            const el = document.getElementById('status-text');
            if (data.status === 'deployed') {{
                el.innerHTML = '<span class="text-emerald-400">●</span> Splitter deployed successfully';
                if (intervalId) clearInterval(intervalId);
                setTimeout(() => window.location.href = '/split/' + splitterAddr, 1500);
            }} else if (data.status === 'failed') {{
                el.innerHTML = '<span class="text-red-400">●</span> Deployment failed. Contact support.';
                if (intervalId) clearInterval(intervalId);
            }} else {{
                checks++;
                el.innerHTML = '<span class="text-amber-400">●</span> Waiting for payment... (checked ' + checks + ' times)';
            }}
        }} catch (e) {{
            console.error('Error querying status', e);
        }}
    }}

    function startPolling() {{
        setTimeout(() => {{
            checkStatus();
            intervalId = setInterval(() => {{
                if (checks >= MAX_CHECKS) {{
                    clearInterval(intervalId);
                    return;
                }}
                checkStatus();
            }}, 60000);
        }}, 60000);
    }}

    document.addEventListener('DOMContentLoaded', () => {{
        document.getElementById('copy-btn').addEventListener('click', copyAddress);
        document.getElementById('check-now').addEventListener('click', (e) => {{
            e.preventDefault();
            checkStatus();
        }});
        initQR();
        startPolling();
    }});
    """

    return Layout(
        # qrcodejs CDN
        Script(src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"),

        Section(
            Div(
                Badge("Payment pending", "amber"),
                H1("Payment instructions", cls="text-3xl font-bold mt-4 mb-2"),
                P(
                    "Send the fee from your usual wallet. No connection needed. "
                    "Once we detect it, we deploy the contract.",
                    cls="text-slate-400 mb-8",
                ),

                # Step 1: pay
                Div(
                    H3("1. Send the fee", cls="font-semibold mb-4"),
                    Div(
                        # QR
                        Div(
                            Div(
                                Div(id="qr-container", cls="bg-white p-2 rounded-lg inline-block"),
                                cls="flex justify-center",
                            ),
                            P("Scan with your wallet",
                              cls="text-xs text-slate-500 text-center mt-3"),
                            cls="flex flex-col items-center",
                        ),
                        # Address + copy + info
                        Div(
                            Div(
                                Div("Payment address",
                                    cls="text-xs text-slate-500 uppercase tracking-wide mb-2"),
                                Div(
                                    Div(
                                        Span(payment_address,
                                             cls="text-sm text-white mono break-all",
                                             id="payment-address"),
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
                                cls="mb-4",
                            ),
                            InfoRow("Exact amount", f"{fee_usdc:.2f} USDC"),
                            InfoRow("Chain", "Monad"),
                            InfoRow("Order ID", order_id),
                            cls="flex-1",
                        ),
                        cls="grid grid-cols-1 md:grid-cols-[auto_1fr] gap-6 items-start",
                    ),
                    P(
                        "⚠️ Important: do not change the amount. If you send a "
                        "different one, the deployer will not recognize the payment.",
                        cls="text-xs text-amber-400 mt-4",
                    ),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800 mb-6",
                ),

                # Step 2: where it will appear
                Div(
                    H3("2. Your splitter will appear at", cls="font-semibold mb-4"),
                    CopyBox("Deterministic address", order["predicted_splitter_address"]),
                    P(
                        "It is the same address you send the fee to.",
                        cls="text-xs text-slate-500 mt-2",
                    ),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800 mb-6",
                ),

                # Step 3: config
                Div(
                    H3("3. Configuration to be deployed", cls="font-semibold mb-4"),
                    Table(
                        Thead(
                            Tr(
                                Th("Address", cls="text-left text-xs text-slate-400 font-medium pb-2"),
                                Th("Share", cls="text-right text-xs text-slate-400 font-medium pb-2"),
                            )
                        ),
                        Tbody(*rows),
                        cls="w-full",
                    ),
                    cls="p-6 rounded-xl bg-slate-900 border border-slate-800 mb-6",
                ),

                # Status / polling
                Div(
                    H3("Status", cls="font-semibold mb-4"),
                    Div(
                        Span("● ", cls="text-amber-400"),
                        Span("Waiting for payment...", cls="text-sm", id="status-text"),
                        cls="flex items-center gap-2 mb-4",
                    ),
                    Div(
                        A(
                            "I already paid →",
                            href="#",
                            id="check-now",
                            cls="inline-block px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm no-underline transition",
                        ),
                        A(
                            "View contract",
                            href=f"/split/{payment_address}",
                            cls="inline-block ml-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-sm no-underline transition",
                        ),
                        cls="flex flex-wrap gap-2",
                    ),
                    cls="p-6 rounded-xl bg-blue-500/5 border border-blue-500/20 mb-6",
                ),

                Script(page_script),

                cls="max-w-3xl",
            ),
            cls="max-w-7xl mx-auto px-6 py-12",
        ),
        title="Payment instructions · Splitter",
    )


def _error_page(message: str):
    return Layout(
        Section(
            Div(
                Badge("Error", "red"),
                H1("Something went wrong", cls="text-3xl font-bold mt-4 mb-4"),
                P(message, cls="text-slate-400 mb-6"),
                A(
                    "← Back to edit",
                    href="/create",
                    cls="inline-block px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white no-underline transition",
                ),
                cls="max-w-2xl",
            ),
            cls="max-w-7xl mx-auto px-6 py-16",
        ),
        title="Error · Splitter",
    )
