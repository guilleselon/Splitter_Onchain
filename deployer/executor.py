"""
Deployer executor.

Given an order with verified payment, calls Factory.create() to deploy
the splitter. Signs the transaction LOCALLY if a private_key is
provided (production), or lets the node sign if not (for
EthereumTesterProvider in demo mode).

Compatible with web3.py 6.x and 7.x.
"""

from web3 import Web3


FACTORY_ABI = [
    {
        "inputs": [
            {"name": "_token", "type": "address"},
            {"name": "_beneficiaries", "type": "address[]"},
            {"name": "_shares", "type": "uint256[]"},
            {"name": "_treasury", "type": "address"},
            {"name": "_relayer_fee", "type": "uint256"},
            {"name": "_config_hash", "type": "bytes32"},
        ],
        "name": "create",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "splitter", "type": "address"},
            {"indexed": True, "name": "config_hash", "type": "bytes32"},
            {"indexed": False, "name": "actual_salt", "type": "bytes32"},
            {"indexed": True, "name": "creator", "type": "address"},
        ],
        "name": "SplitterCreated",
        "type": "event",
    },
]


def _extract_raw(signed):
    raw = getattr(signed, "raw_transaction", None)
    if raw is None:
        raw = getattr(signed, "rawTransaction", None)
    if raw is None:
        raise RuntimeError(
            "SignedTransaction has neither raw_transaction nor rawTransaction"
        )
    return raw


def execute_order(
    w3: Web3,
    factory_address: str,
    usdc_address: str,
    order: dict,
    private_key: str | None = None,
    gas: int = 1_500_000,
) -> tuple[str | None, str | None, str | None]:
    """
    Execute the splitter deployment for `order`.

    Returns:
        (tx_hash, splitter_address, error)
    """
    try:
        factory = w3.eth.contract(
            address=w3.to_checksum_address(factory_address),
            abi=FACTORY_ABI,
        )
    except Exception as e:
        return None, None, f"could not instantiate factory: {e}"

    config_hash_bytes = bytes.fromhex(order["config_hash"].replace("0x", ""))

    try:
        fn = factory.functions.create(
            w3.to_checksum_address(usdc_address),
            order["beneficiaries"],
            order["shares"],
            order["treasury"],
            order["relayer_fee"],
            config_hash_bytes,
        )

        if private_key:
            sender = w3.eth.account.from_key(private_key).address
            tx = fn.build_transaction({
                "from": sender,
                "nonce": w3.eth.get_transaction_count(sender),
                "chainId": w3.eth.chain_id,
                "gas": gas,
                "gasPrice": w3.eth.gas_price,
            })
            signed = w3.eth.account.sign_transaction(
                tx, private_key=private_key
            )
            raw = _extract_raw(signed)
            tx_hash = w3.eth.send_raw_transaction(raw)
        else:
            tx_hash = fn.transact({
                "from": w3.eth.default_account,
                "gas": gas,
            })
    except Exception as e:
        return None, None, f"transact failed: {e}"

    try:
        rc = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    except Exception as e:
        tx_hex = tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)
        return tx_hex, None, f"wait_for_receipt failed: {e}"

    if rc.status != 1:
        tx_hex = rc.transactionHash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        return tx_hex, None, "transaction reverted (status=0)"

    try:
        evs = factory.events.SplitterCreated().process_receipt(rc)
    except Exception as e:
        tx_hex = rc.transactionHash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        return tx_hex, None, f"could not parse event: {e}"

    if not evs:
        tx_hex = rc.transactionHash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        return tx_hex, None, "SplitterCreated not emitted"

    splitter = evs[0]["args"]["splitter"]

    predicted = order.get("predicted_splitter_address")
    if predicted and splitter.lower() != predicted.lower():
        tx_hex = rc.transactionHash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        return tx_hex, splitter, (
            f"deployed address {splitter} does not match "
            f"predicted {predicted}"
        )

    tx_hex = rc.transactionHash.hex()
    if not tx_hex.startswith("0x"):
        tx_hex = "0x" + tx_hex

    return tx_hex, splitter, None

