"""
Relayer client.

Signs release(beneficiary) on a deployed Splitter. The contract
charges the relayer fee automatically.

Signs LOCALLY if a private_key is provided (production against Monad).
Otherwise, uses transact() (for EthereumTesterProvider).

Compatible with web3.py 6.x and 7.x.
"""

from web3 import Web3


SPLITTER_ABI = [
    {
        "inputs": [{"name": "_beneficiary", "type": "address"}],
        "name": "release",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "", "type": "address"}],
        "name": "shares",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "", "type": "address"}],
        "name": "released",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "total_shares",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "total_released",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "treasury",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "relayer_fee",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


ERC20_ABI = [
    {
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def _splitter_contract(w3: Web3, splitter_address: str):
    return w3.eth.contract(
        address=w3.to_checksum_address(splitter_address),
        abi=SPLITTER_ABI,
    )


def _extract_raw(signed):
    """
    Compatible with web3.py 6.x (rawTransaction) and 7.x (raw_transaction).
    """
    raw = getattr(signed, "raw_transaction", None)
    if raw is None:
        raw = getattr(signed, "rawTransaction", None)
    if raw is None:
        raise RuntimeError(
            "SignedTransaction has neither raw_transaction nor rawTransaction"
        )
    return raw


# ==================================================================
# Reads
# ==================================================================

def get_share(w3: Web3, splitter_address: str, beneficiary: str) -> int:
    s = _splitter_contract(w3, splitter_address)
    return s.functions.shares(w3.to_checksum_address(beneficiary)).call()


def get_released(w3: Web3, splitter_address: str, beneficiary: str) -> int:
    s = _splitter_contract(w3, splitter_address)
    return s.functions.released(w3.to_checksum_address(beneficiary)).call()


def get_relayer_fee(w3: Web3, splitter_address: str) -> int:
    s = _splitter_contract(w3, splitter_address)
    return s.functions.relayer_fee().call()


def get_pending(w3: Web3, splitter_address: str, beneficiary: str) -> int:
    s = _splitter_contract(w3, splitter_address)
    b = w3.to_checksum_address(beneficiary)

    share = s.functions.shares(b).call()
    if share == 0:
        return 0

    total_shares = s.functions.total_shares().call()
    total_released = s.functions.total_released().call()

    token_address = s.functions.token().call()
    token = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    balance = token.functions.balanceOf(
        w3.to_checksum_address(splitter_address)
    ).call()

    total_available = balance + total_released
    owed = (total_available * share) // total_shares
    already_released = s.functions.released(b).call()
    pending = owed - already_released
    return max(pending, 0)


def is_beneficiary(w3: Web3, splitter_address: str, beneficiary: str) -> bool:
    return get_share(w3, splitter_address, beneficiary) > 0


# ==================================================================
# Write: sign release()
# ==================================================================

def relay_release(
    w3: Web3,
    splitter_address: str,
    beneficiary: str,
    private_key: str | None = None,
    gas: int = 500_000,
) -> tuple[str | None, str | None]:
    """
    Sign release(beneficiary).

    - If private_key: local signing (send_raw_transaction). Production.
    - Otherwise: node transact(). Tester only.

    Returns (tx_hash, error).
    """
    try:
        s = _splitter_contract(w3, splitter_address)
    except Exception as e:
        return None, f"could not instantiate splitter: {e}"

    b = w3.to_checksum_address(beneficiary)

    try:
        fn = s.functions.release(b)

        if private_key:
            sender = w3.eth.account.from_key(private_key).address
            tx = fn.build_transaction({
                "from": sender,
                "nonce": w3.eth.get_transaction_count(sender),
                "chainId": w3.eth.chain_id,
                "gas": gas,
                "gasPrice": w3.eth.gas_price,
            })
            signed = w3.eth.account.sign_transaction(tx, private_key=private_key)
            raw = _extract_raw(signed)
            tx_hash = w3.eth.send_raw_transaction(raw)
        else:
            tx_hash = fn.transact({
                "from": w3.eth.default_account,
                "gas": gas,
            })
    except Exception as e:
        return None, f"transact failed: {e}"

    try:
        rc = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    except Exception as e:
        tx_hex = tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)
        return tx_hex, f"wait_for_receipt failed: {e}"

    if rc.status != 1:
        tx_hex = rc.transactionHash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        return tx_hex, "transaction reverted (status=0)"

    tx_hex = rc.transactionHash.hex()
    if not tx_hex.startswith("0x"):
        tx_hex = "0x" + tx_hex

    return tx_hex, None
