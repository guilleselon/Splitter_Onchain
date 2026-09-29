"""
Payment verification by balance.

The user sends USDC to the deterministic splitter address (which does
not exist yet as a contract). Instead of scanning Transfer events
(expensive and fragile with public RPCs), we simply read the balance
of that address in the USDC contract.

If balance >= fee_wei, payment is considered received.
"""

from web3 import Web3


ERC20_BALANCE_ABI = [
    {
        "inputs": [{"name": "", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def check_balance(
    w3: Web3,
    usdc_address: str,
    target_address: str,
    expected_wei: int,
) -> tuple[bool, int]:
    """
    Read the USDC balance of `target_address`.

    Returns:
        (paid, balance_wei)

    - paid: True if balance >= expected_wei
    - balance_wei: current balance in wei
    """
    try:
        usdc = w3.eth.contract(
            address=w3.to_checksum_address(usdc_address),
            abi=ERC20_BALANCE_ABI,
        )
        balance = usdc.functions.balanceOf(
            w3.to_checksum_address(target_address)
        ).call()
    except Exception as e:
        raise RuntimeError(f"balanceOf failed: {e}") from e

    return balance >= expected_wei, balance


def current_block(w3: Web3) -> int:
    return w3.eth.block_number

