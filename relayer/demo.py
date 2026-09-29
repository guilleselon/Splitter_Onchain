"""
Relayer entry point in demo mode (EthereumTesterProvider).

Deploys a test splitter on the fly, funds it, and starts the API so
you can test POST /relay without touching Monad.

NOT for production use. Only for local testing.

Run from the project root:
    python -m relayer.demo
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from vyper import compile_code
from web3 import Web3, EthereumTesterProvider

from relayer.api import create_app


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("relayer-demo")


SRC = Path(__file__).parent.parent / "contracts" / "src"

MOCK_USDC_SRC = """
# @version ^0.4.3

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

balanceOf: public(HashMap[address, uint256])

@external
def mint(_to: address, _amount: uint256):
    self.balanceOf[_to] = self.balanceOf[_to] + _amount
    log Transfer(sender=empty(address), receiver=_to, value=_amount)

@external
def transfer(_to: address, _amount: uint256) -> bool:
    self.balanceOf[msg.sender] = self.balanceOf[msg.sender] - _amount
    self.balanceOf[_to] = self.balanceOf[_to] + _amount
    log Transfer(sender=msg.sender, receiver=_to, value=_amount)
    return True
"""


def _compile(path: Path):
    r = compile_code(path.read_text(), output_formats=["abi", "bytecode"])
    return r["abi"], r["bytecode"]


def _compile_str(src: str):
    r = compile_code(src, output_formats=["abi", "bytecode"])
    return r["abi"], r["bytecode"]


def _deploy(w3, abi, bc, sender, *args):
    c = w3.eth.contract(abi=abi, bytecode=bc)
    rc = w3.eth.wait_for_transaction_receipt(
        c.constructor(*args).transact({"from": sender, "gas": 6_000_000})
    )
    return w3.eth.contract(address=rc.contractAddress, abi=abi)


ONE_USDC = 1_000_000
RELAYER_FEE = 100_000


def main():
    print("=" * 70)
    print("  Splitter Relayer — DEMO MODE (EthereumTesterProvider)")
    print("=" * 70)

    w3 = Web3(EthereumTesterProvider())
    accounts = list(w3.eth.accounts)
    deployer = accounts[0]
    relayer_acc = accounts[1]
    alice = accounts[2]
    bob = accounts[3]
    treasury = accounts[4]

    w3.eth.default_account = relayer_acc

    log.info("deployer: %s", deployer)
    log.info("relayer:  %s", relayer_acc)
    log.info("alice:    %s", alice)
    log.info("bob:      %s", bob)
    log.info("treasury: %s", treasury)

    # Compile
    log.info("compiling contracts...")
    splitter_abi, splitter_bc = _compile(SRC / "Splitter.vy")
    usdc_abi, usdc_bc = _compile_str(MOCK_USDC_SRC)

    # Deploy USDC + splitter
    log.info("deploying mock USDC and test splitter...")
    usdc = _deploy(w3, usdc_abi, usdc_bc, deployer)

    splitter = _deploy(w3, splitter_abi, splitter_bc, deployer)
    w3.eth.wait_for_transaction_receipt(
        splitter.functions.initialize(
            usdc.address,
            [alice, bob],
            [5000, 5000],
            treasury,
            RELAYER_FEE,
        ).transact({"from": deployer})
    )

    # Fund splitter with 100 USDC so there's something to claim
    tx = usdc.functions.mint(splitter.address, 100 * ONE_USDC)
    w3.eth.wait_for_transaction_receipt(tx.transact({"from": deployer}))

    log.info("  usdc:     %s", usdc.address)
    log.info("  splitter: %s", splitter.address)
    log.info("  splitter funded with 100 USDC")
    log.info("  alice and bob: 50 USDC pending each")

    # API
    app, rt = create_app(
        w3=w3,
        relayer_address=relayer_acc,
        min_pending_wei=0,
    )

    # Demo endpoints
    @rt("/demo/accounts")
    def demo_accounts():
        return {
            "deployer": deployer,
            "relayer": relayer_acc,
            "alice": alice,
            "bob": bob,
            "treasury": treasury,
        }

    @rt("/demo/balances")
    def demo_balances():
        return {
            "splitter": usdc.functions.balanceOf(splitter.address).call(),
            "alice": usdc.functions.balanceOf(alice).call(),
            "bob": usdc.functions.balanceOf(bob).call(),
            "treasury": usdc.functions.balanceOf(treasury).call(),
        }

    @rt("/demo/splitter")
    def demo_splitter():
        return {
            "splitter": splitter.address,
            "usdc": usdc.address,
            "treasury": treasury,
            "relayer": relayer_acc,
            "alice": alice,
            "bob": bob,
        }

    print(f"\n  http://0.0.0.0:5003")
    print("  Relayer endpoints:")
    print("    GET  /health")
    print("    GET  /splitter/{address}/pending/{beneficiary}")
    print("    POST /relay")
    print("\n  Demo endpoints:")
    print("    GET  /demo/accounts")
    print("    GET  /demo/balances")
    print("    GET  /demo/splitter")
    print("\n  Ctrl+C to stop.\n")

    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=5003, log_level="info")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
