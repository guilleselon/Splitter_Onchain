"""Reusable forms and input fields."""

from fasthtml.common import (
    A,
    Button,
    Div,
    Input,
    Label,
    P,
    Span,
    Textarea,
)


def Field(label: str, input_el, hint: str | None = None):
    children = [
        Label(label, cls="block text-sm font-medium mb-2 text-slate-200"),
        input_el,
    ]
    if hint:
        children.append(P(hint, cls="text-xs text-slate-500 mt-1"))
    return Div(*children, cls="mb-6")


def TextInput(name: str, placeholder: str = "", value: str = "",
              input_id: str | None = None):
    return Input(
        type="text",
        name=name,
        id=input_id or name,
        placeholder=placeholder,
        value=value,
        cls="w-full px-4 py-3 rounded-lg bg-slate-900 border border-slate-700 text-white focus:border-blue-500 focus:outline-none transition",
    )


def TextArea(name: str, placeholder: str = "", value: str = "", rows: int = 3):
    return Textarea(
        value,
        name=name,
        id=name,
        placeholder=placeholder,
        rows=rows,
        cls="w-full px-4 py-3 rounded-lg bg-slate-900 border border-slate-700 text-white focus:border-blue-500 focus:outline-none transition",
    )


def BeneficiaryRow(index: int, address: str = "", percent: float = 0.0):
    """
    Row in the creation form.
    One input for the address and one for the percentage.
    """
    return Div(
        Input(
            type="text",
            name=f"beneficiaries[{index}][address]",
            value=address,
            placeholder="0x...",
            cls="flex-[3] px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm mono",
        ),
        Div(
            Input(
                type="number",
                name=f"beneficiaries[{index}][percent]",
                value=percent,
                min="0",
                max="100",
                step="0.01",
                cls="w-24 px-2 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm text-right mono",
            ),
            Span("%", cls="text-slate-400 text-sm ml-1"),
            cls="flex items-center",
        ),
        Button(
            "×",
            type="button",
            cls="w-8 h-8 rounded-lg bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition",
        ),
        cls="flex gap-2 mb-2 items-center beneficiary-row",
    )


def SubmitRow(cancel_href: str = "/", submit_label: str = "Continue →"):
    return Div(
        A(
            "Cancel",
            href=cancel_href,
            cls="px-6 py-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-white no-underline transition",
        ),
        Button(
            submit_label,
            type="submit",
            cls="px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition",
        ),
        cls="flex gap-3 justify-end",
    )
