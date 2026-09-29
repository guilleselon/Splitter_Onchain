"""
Direct contract reads.

The web reads balances, shares, and released amounts without going
through the deployer or relayer. This powers the public splitter page.
"""

from web3 import Web3


SPLITTER_ABI = [
    {"inputs": [{"name": "", "type": "address"}], "name": "shares",
     "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "", "type": "address"}], "name": "released",
     "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "total_shares",
     "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "total_released",
     "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token",
     "outputs": [{"name": "", "type": "address"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "treasury",
     "outputs": [{"name": "", "type": "address"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "relayer_fee",
     "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "initialized",
     "outputs": [{"name": "", "type": "bool"}],
     "stateMutability": "view", "type": "function"},
]


ERC20_ABI = [
    {"inputs": [{"name": "", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals",
     "outputs": [{"name": "", "type": "uint8"}],
     "stateMutability": "view", "type": "function"},
]


class ChainReader:
    def __init__(self, w3: Web3, usdc_address: str):
        self.w3 = w3
        self.usdc_address = w3.to_checksum_address(usdc_address)

    # ------------------------------------------------------------------
    # Splitter
    # ------------------------------------------------------------------

    def _splitter(self, address: str):
        return self.w3.eth.contract(
            address=self.w3.to_checksum_address(address),
            abi=SPLITTER_ABI,
        )

    def is_initialized(self, splitter_address: str) -> bool:
        try:
            s = self._splitter(splitter_address)
            return s.functions.initialized().call()
        except Exception:
            return False

    def get_total_shares(self, splitter_address: str) -> int:
        return self._splitter(splitter_address).functions.total_shares().call()

    def get_total_released(self, splitter_address: str) -> int:
        return self._splitter(splitter_address).functions.total_released().call()

    def get_share(self, splitter_address: str, beneficiary: str) -> int:
        return self._splitter(splitter_address).functions.shares(
            self.w3.to_checksum_address(beneficiary)
        ).call()

    def get_released(self, splitter_address: str, beneficiary: str) -> int:
        return self._splitter(splitter_address).functions.released(
            self.w3.to_checksum_address(beneficiary)
        ).call()

    def get_token(self, splitter_address: str) -> str:
        return self._splitter(splitter_address).functions.token().call()

    def get_treasury(self, splitter_address: str) -> str:
        return self._splitter(splitter_address).functions.treasury().call()

    def get_relayer_fee(self, splitter_address: str) -> int:
        return self._splitter(splitter_address).functions.relayer_fee().call()

    # ------------------------------------------------------------------
    # USDC
    # ------------------------------------------------------------------

    def _usdc(self):
        return self.w3.eth.contract(address=self.usdc_address, abi=ERC20_ABI)

    def usdc_balance(self, address: str) -> int:
        return self._usdc().functions.balanceOf(
            self.w3.to_checksum_address(address)
        ).call()

    def usdc_decimals(self) -> int:
        return self._usdc().functions.decimals().call()

    # ------------------------------------------------------------------
    # Aggregated snapshots
    # ------------------------------------------------------------------

    def splitter_snapshot(self, splitter_address: str) -> dict:
        """
        Return a dict with the splitter state:
            - initialized
            - total_shares
            - total_released
            - balance_wei (current USDC held by the splitter)
            - token
            - treasury
            - relayer_fee
        """
        if not self.is_initialized(splitter_address):
            return {
                "initialized": False,
                "splitter_address": splitter_address,
            }

        s = self._splitter(splitter_address)
        return {
            "initialized": True,
            "splitter_address": self.w3.to_checksum_address(splitter_address),
            "total_shares": s.functions.total_shares().call(),
            "total_released": s.functions.total_released().call(),
            "balance_wei": self.usdc_balance(splitter_address),
            "token": s.functions.token().call(),
            "treasury": s.functions.treasury().call(),
            "relayer_fee": s.functions.relayer_fee().call(),
        }

    def beneficiary_snapshot(
        self, splitter_address: str, beneficiary: str
    ) -> dict:
        """
        State of a specific beneficiary in a specific splitter.
        """
        snap = self.splitter_snapshot(splitter_address)
        if not snap["initialized"]:
            return {
                "initialized": False,
                "is_beneficiary": False,
                "pending_wei": 0,
                "released_wei": 0,
                "share_bps": 0,
            }

        b = self.w3.to_checksum_address(beneficiary)
        s = self._splitter(splitter_address)
        share = s.functions.shares(b).call()
        released = s.functions.released(b).call()

        if share == 0:
            return {
                "initialized": True,
                "is_beneficiary": False,
                "pending_wei": 0,
                "released_wei": 0,
                "share_bps": 0,
            }

        total_available = snap["balance_wei"] + snap["total_released"]
        owed = (total_available * share) // snap["total_shares"]
        pending = max(owed - released, 0)

        return {
            "initialized": True,
            "is_beneficiary": True,
            "beneficiary": b,
            "share_bps": share,
            "released_wei": released,
            "pending_wei": pending,
        }
