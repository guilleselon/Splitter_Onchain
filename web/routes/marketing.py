"""Marketing routes: / and /how-it-works."""

from fasthtml.common import (
    A,
    Div,
    H1,
    H2,
    H3,
    Li,
    P,
    Section,
    Span,
    Ul,
)

from web.components.badges import Badge
from web.components.layout import Layout


def register(rt):
    @rt("/")
    def get():
        return Layout(
            # Hero
            Section(
                Div(
                    Badge("Immutable contracts on Monad", "blue"),
                    H1(
                        Span("Distribute hackathon prizes ", cls="text-white"),
                        Span("in USDC", cls="gradient-text"),
                        Span(", without custody.", cls="text-white"),
                        cls="text-5xl md:text-6xl font-extrabold tracking-tight mt-6 mb-6 leading-tight",
                    ),
                    P(
                        "Deploy a splitter contract in one click. Once deployed, "
                        "nobody can change the rules. Not you, not us. "
                        "Winners withdraw whenever they want.",
                        cls="text-xl text-slate-400 max-w-2xl mb-8",
                    ),
                    Div(
                        A(
                            "Create splitter →",
                            href="/create",
                            cls="px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium no-underline transition",
                        ),
                        A(
                            "Claim funds",
                            href="/claim",
                            cls="px-6 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium no-underline transition",
                        ),
                        A(
                            "How it works",
                            href="/how-it-works",
                            cls="px-6 py-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium no-underline transition border border-slate-700",
                        ),
                        cls="flex flex-wrap gap-3",
                    ),
                    cls="max-w-3xl",
                ),
                cls="max-w-7xl mx-auto px-6 py-24",
            ),

            # Features
            Section(
                Div(
                    H2("Why Splitter", cls="text-3xl font-bold text-center mb-3"),
                    P(
                        "Everything you need to distribute on-chain payments without surprises.",
                        cls="text-slate-400 text-center mb-16 max-w-2xl mx-auto",
                    ),
                    Div(
                        _FeatureCard("🔒", "Immutable",
                            "Once deployed, the contract cannot be modified. No owner, no admin, no upgrade."),
                        _FeatureCard("🚫", "Non-custodial",
                            "We never touch the funds. The contract holds them until each beneficiary withdraws their share."),
                        _FeatureCard("🆔", "No KYC",
                            "Permissionless access. We do not collect identities. Deploy with your wallet and go."),
                        _FeatureCard("💵", "USDC only on Monad",
                            "No volatility, no multi-token. Ridiculous fees. One clear flow."),
                        _FeatureCard("⛓️", "Pull payment",
                            "The organizer deposits once. Each beneficiary withdraws whenever they want with one click."),
                        _FeatureCard("🔍", "Public page",
                            "Anyone can verify the distribution, the balance and the history at a URL."),
                        cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                    ),
                    cls="max-w-7xl mx-auto px-6 py-16",
                ),
            ),

            # Steps
            Section(
                Div(
                    H2("How it works", cls="text-3xl font-bold text-center mb-16"),
                    Div(
                        _Step("1", "Configure",
                              "Define beneficiary addresses and their percentages."),
                        _Step("2", "Pay 2 USDC",
                              "Send the fee to the address we give you. No wallet connection needed."),
                        _Step("3", "We deploy",
                              "As soon as we detect the payment, we deploy the contract."),
                        _Step("4", "Distribute",
                              "Anyone can send USDC. Beneficiaries claim whenever they want."),
                        cls="grid grid-cols-1 md:grid-cols-4 gap-8",
                    ),
                    cls="max-w-7xl mx-auto px-6 py-16",
                ),
                cls="bg-slate-900/50 border-y border-slate-800",
            ),

            # Beneficiary section
            Section(
                Div(
                    Div(
                        Badge("Beneficiaries", "green"),
                        H2("Are you a beneficiary of a distribution?",
                           cls="text-3xl md:text-4xl font-bold text-center mt-4 mb-3"),
                        P(
                            "If someone told you that you have funds waiting for you "
                            "in a splitter, come here to claim them. You only need "
                            "the contract address or the link the organizer sent you.",
                            cls="text-slate-400 text-center mb-8 max-w-2xl mx-auto",
                        ),
                        Div(
                            A(
                                "Claim my funds →",
                                href="/claim",
                                cls="px-8 py-4 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium no-underline text-lg transition",
                            ),
                            cls="text-center",
                        ),
                        cls="max-w-3xl mx-auto",
                    ),
                    cls="max-w-7xl mx-auto px-6 py-16",
                ),
                cls="bg-emerald-500/5 border-y border-emerald-500/20",
            ),

            # Final CTA
            Section(
                Div(
                    H2("Ready to distribute without spreadsheets?",
                       cls="text-4xl font-bold mb-6"),
                    P("Create your first splitter in less than 2 minutes.",
                      cls="text-slate-400 text-lg mb-8"),
                    A(
                        "Start now →",
                        href="/create",
                        cls="px-8 py-4 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium no-underline text-lg transition",
                    ),
                    cls="text-center max-w-3xl mx-auto",
                ),
                cls="max-w-7xl mx-auto px-6 py-24",
            ),
        )

    @rt("/how-it-works")
    def get():
        return Layout(
            Section(
                Div(
                    H1("How it works", cls="text-4xl font-bold mb-6"),
                    P(
                        "Splitter is a tool to deploy payment distribution contracts "
                        "in USDC on Monad. Non-custodial, no KYC, no admin keys.",
                        cls="text-slate-400 text-lg mb-12 max-w-3xl",
                    ),

                    H2("The problem", cls="text-2xl font-bold mb-4 mt-12"),
                    P(
                        "Today, distributing hackathon prizes among 10 teams means: "
                        "a spreadsheet + 10 manual transfers + gas + errors. "
                        "And with no on-chain proof that the distribution was as agreed.",
                        cls="text-slate-400 mb-8",
                    ),

                    H2("The solution", cls="text-2xl font-bold mb-4 mt-12"),
                    P("Splitter deploys a contract that:",
                      cls="text-slate-400 mb-4"),
                    Ul(
                        Li("Receives USDC at a unique address.", cls="text-slate-300 mb-2"),
                        Li("Distributes proportionally according to shares fixed at deployment.",
                           cls="text-slate-300 mb-2"),
                        Li("Lets each beneficiary withdraw their share whenever they want.",
                           cls="text-slate-300 mb-2"),
                        Li("Is immutable: nobody can change the rules, add or remove beneficiaries.",
                           cls="text-slate-300 mb-2"),
                        Li("Is verifiable: anyone can check the distribution and the history.",
                           cls="text-slate-300"),
                        cls="list-disc pl-6 mb-8",
                    ),

                    H2("What it does NOT do", cls="text-2xl font-bold mb-4 mt-12"),
                    Ul(
                        Li("It does not custody funds (no privileged keys).",
                           cls="text-slate-300 mb-2"),
                        Li("It does not do KYC or collect identities.",
                           cls="text-slate-300 mb-2"),
                        Li("It does not allow modifying the contract after deployment.",
                           cls="text-slate-300 mb-2"),
                        Li("It does not support other chains or other tokens (Monad + USDC only).",
                           cls="text-slate-300"),
                        cls="list-disc pl-6",
                    ),

                    cls="max-w-3xl",
                ),
                cls="max-w-7xl mx-auto px-6 py-16",
            ),
            title="How it works · Splitter",
        )


def _FeatureCard(icon: str, title: str, desc: str):
    return Div(
        Div(icon, cls="text-3xl mb-4"),
        H3(title, cls="text-lg font-semibold mb-2"),
        P(desc, cls="text-slate-400 text-sm leading-relaxed"),
        cls="p-6 rounded-xl bg-slate-900 border border-slate-800 card-hover",
    )


def _Step(num: str, title: str, desc: str):
    return Div(
        Div(num, cls="w-12 h-12 rounded-full bg-blue-600 text-white font-bold text-lg flex items-center justify-center mb-4"),
        H3(title, cls="font-semibold mb-2"),
        P(desc, cls="text-slate-400 text-sm"),
        cls="text-center",
    )
