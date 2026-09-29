"""Route /create: splitter configuration form."""

from fasthtml.common import (
    Button,
    Div,
    Form,
    H1,
    Label,
    P,
    Script,
    Section,
    Span,
)

from web.components.badges import Badge
from web.components.forms import BeneficiaryRow, SubmitRow
from web.components.layout import Layout


PAGE_SCRIPT = """
(function() {
    const container = document.getElementById('beneficiaries-container');
    const addBtn = document.getElementById('add-beneficiary');
    const totalDisplay = document.getElementById('total-display');

    const MAX_BENEFICIARIES = 20;

    function rowCount() {
        return container.querySelectorAll('.beneficiary-row').length;
    }

    function updateAddButton() {
        const count = rowCount();
        if (count >= MAX_BENEFICIARIES) {
            addBtn.disabled = true;
            addBtn.innerText = 'Maximum ' + MAX_BENEFICIARIES + ' beneficiaries reached';
            addBtn.className = 'w-full mt-3 py-3 rounded-lg border border-slate-800 text-slate-600 text-sm cursor-not-allowed';
        } else {
            addBtn.disabled = false;
            addBtn.innerText = '+ Add beneficiary (' + count + '/' + MAX_BENEFICIARIES + ')';
            addBtn.className = 'w-full mt-3 py-3 rounded-lg border border-dashed border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 text-sm transition';
        }
    }

    function updateTotal() {
        const inputs = container.querySelectorAll('input[name$="[percent]"]');
        let sum = 0;
        inputs.forEach(inp => {
            const v = parseFloat(inp.value) || 0;
            sum += v;
        });
        const rounded = sum.toFixed(2);
        totalDisplay.textContent = 'Sum: ' + rounded + '%';
        if (Math.abs(sum - 100) < 0.005) {
            totalDisplay.className = 'text-sm text-emerald-400 mono';
        } else if (sum > 100) {
            totalDisplay.className = 'text-sm text-red-400 mono';
        } else {
            totalDisplay.className = 'text-sm text-amber-400 mono';
        }
    }

    function recalcIndexes() {
        const rows = container.querySelectorAll('.beneficiary-row');
        rows.forEach((row, i) => {
            const addrInput = row.querySelector('input[name$="[address]"]');
            const pctInput = row.querySelector('input[name$="[percent]"]');
            if (addrInput) addrInput.name = 'beneficiaries[' + i + '][address]';
            if (pctInput) pctInput.name = 'beneficiaries[' + i + '][percent]';
        });
    }

    function createRow() {
        const div = document.createElement('div');
        div.className = 'flex gap-2 mb-2 items-center beneficiary-row';

        const addrInput = document.createElement('input');
        addrInput.type = 'text';
        addrInput.placeholder = '0x...';
        addrInput.className = 'flex-[3] px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm mono';
        addrInput.name = 'beneficiaries[0][address]';

        const pctWrap = document.createElement('div');
        pctWrap.className = 'flex items-center';

        const pctInput = document.createElement('input');
        pctInput.type = 'number';
        pctInput.value = '0';
        pctInput.min = '0';
        pctInput.max = '100';
        pctInput.step = '0.01';
        pctInput.className = 'w-24 px-2 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm text-right mono';
        pctInput.name = 'beneficiaries[0][percent]';

        const pctLabel = document.createElement('span');
        pctLabel.textContent = '%';
        pctLabel.className = 'text-slate-400 text-sm ml-1';

        pctWrap.appendChild(pctInput);
        pctWrap.appendChild(pctLabel);

        const delBtn = document.createElement('button');
        delBtn.type = 'button';
        delBtn.textContent = '×';
        delBtn.className = 'w-8 h-8 rounded-lg bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition';
        delBtn.addEventListener('click', () => {
            div.remove();
            recalcIndexes();
            updateTotal();
            updateAddButton();
        });

        div.appendChild(addrInput);
        div.appendChild(pctWrap);
        div.appendChild(delBtn);

        pctInput.addEventListener('input', updateTotal);

        return div;
    }

    addBtn.addEventListener('click', () => {
        if (rowCount() >= MAX_BENEFICIARIES) return;
        const row = createRow();
        container.appendChild(row);
        recalcIndexes();
        updateTotal();
        updateAddButton();
    });

    container.querySelectorAll('.beneficiary-row').forEach(row => {
        const delBtn = row.querySelector('button');
        if (delBtn) {
            delBtn.addEventListener('click', () => {
                row.remove();
                recalcIndexes();
                updateTotal();
                updateAddButton();
            });
        }
        const pctInput = row.querySelector('input[name$="[percent]"]');
        if (pctInput) {
            pctInput.addEventListener('input', updateTotal);
        }
    });

    updateTotal();
    updateAddButton();
})();
"""


def register(rt):
    @rt("/create")
    def get():
        return Layout(
            Section(
                Div(
                    H1("Create splitter", cls="text-3xl font-bold mb-2"),
                    P(
                        "Define addresses and percentages. The sum must be exactly 100%. "
                        "Maximum 20 beneficiaries per splitter.",
                        cls="text-slate-400 mb-8",
                    ),

                    Form(
                        # Chain + token (fixed)
                        Div(
                            Div(
                                Label("Chain", cls="block text-sm font-medium mb-2 text-slate-200"),
                                Div(
                                    Span("⬢ ", cls="text-blue-400"),
                                    "Monad",
                                    Badge("fixed", "slate"),
                                    cls="flex items-center gap-3 px-4 py-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300",
                                ),
                                cls="flex-1",
                            ),
                            Div(
                                Label("Token", cls="block text-sm font-medium mb-2 text-slate-200"),
                                Div(
                                    Span("💵 ", cls=""),
                                    "USDC",
                                    Badge("fixed", "slate"),
                                    cls="flex items-center gap-3 px-4 py-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300",
                                ),
                                cls="flex-1",
                            ),
                            cls="grid grid-cols-2 gap-4 mb-6",
                        ),

                        # Beneficiaries
                        Div(
                            Div(
                                Label("Beneficiaries", cls="text-sm font-medium text-slate-200"),
                                Span("Sum: 100.00%", cls="text-sm text-emerald-400 mono", id="total-display"),
                                cls="flex justify-between mb-3",
                            ),
                            Div(
                                BeneficiaryRow(0, "", 50.00),
                                BeneficiaryRow(1, "", 50.00),
                                id="beneficiaries-container",
                            ),
                            Button(
                                "+ Add beneficiary (2/20)",
                                type="button",
                                id="add-beneficiary",
                                cls="w-full mt-3 py-3 rounded-lg border border-dashed border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 text-sm transition",
                            ),
                            cls="mb-6",
                        ),

                        # Fee + warning
                        Div(
                            Div(
                                Span("Deployment fee", cls="text-sm text-slate-400"),
                                Span("2.00 USDC", cls="text-sm font-medium mono text-white"),
                                cls="flex justify-between mb-2",
                            ),
                            Div(
                                Span("Once deployed, it cannot be modified",
                                     cls="text-sm text-amber-400"),
                                cls="flex justify-between",
                            ),
                            cls="p-4 rounded-lg bg-slate-900 border border-slate-800 mb-6",
                        ),

                        SubmitRow(cancel_href="/", submit_label="Continue to payment →"),

                        method="post",
                        action="/request",
                        id="create-form",
                    ),

                    cls="max-w-3xl",
                ),
                cls="max-w-7xl mx-auto px-6 py-12",
            ),
            Script(PAGE_SCRIPT),
            title="Create splitter · Splitter",
        )
