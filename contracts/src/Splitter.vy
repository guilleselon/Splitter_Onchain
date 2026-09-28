# @version ^0.4.3

from ethereum.ercs import IERC20

event PayeeAdded:
    beneficiary: indexed(address)
    shares: uint256

event PaymentReleased:
    beneficiary: indexed(address)
    amount: uint256
    relayer: indexed(address)

event RelayerFeePaid:
    treasury: indexed(address)
    amount: uint256

MAX_BENEFICIARIES: constant(uint256) = 20
TOTAL_BPS: constant(uint256) = 10_000

token: public(address)
treasury: public(address)
relayer_fee: public(uint256)
total_shares: public(uint256)
total_released: public(uint256)
initialized: public(bool)
_locked: public(bool)

shares: public(HashMap[address, uint256])
released: public(HashMap[address, uint256])

@external
def initialize(
    _token: address,
    _beneficiaries: DynArray[address, MAX_BENEFICIARIES],
    _shares: DynArray[uint256, MAX_BENEFICIARIES],
    _treasury: address,
    _relayer_fee: uint256,
):
    assert not self.initialized, "already initialized"
    assert _token != empty(address), "zero token"
    assert _treasury != empty(address), "zero treasury"
    assert len(_beneficiaries) == len(_shares), "length mismatch"
    assert len(_beneficiaries) > 0, "no beneficiaries"

    total: uint256 = 0
    for n: uint256 in range(MAX_BENEFICIARIES):
        if n >= len(_beneficiaries):
            break
        b: address = _beneficiaries[n]
        s: uint256 = _shares[n]
        assert b != empty(address), "zero address"
        assert s > 0, "zero share"
        assert self.shares[b] == 0, "duplicate"
        self.shares[b] = s
        total += s
        log PayeeAdded(beneficiary=b, shares=s)

    assert total == TOTAL_BPS, "shares must sum to 10000"

    # Sweep del fee inicial: si el splitter ya tiene USDC antes de
    # inicializarse (porque el usuario pagó el fee a esta dirección
    # determinista antes de que existiera el contrato), se barre a treasury.
    initial: uint256 = staticcall IERC20(_token).balanceOf(self)
    if initial > 0:
        success_sweep: bool = extcall IERC20(_token).transfer(_treasury, initial)
        assert success_sweep, "sweep failed"

    self.token = _token
    self.treasury = _treasury
    self.relayer_fee = _relayer_fee
    self.total_shares = total
    self.initialized = True

@external
def release(_beneficiary: address):
    assert self.initialized, "not initialized"
    assert not self._locked, "reentrant"
    self._locked = True

    share: uint256 = self.shares[_beneficiary]
    assert share > 0, "not a beneficiary"

    balance: uint256 = staticcall IERC20(self.token).balanceOf(self)
    total_available: uint256 = balance + self.total_released
    owed: uint256 = (total_available * share) // self.total_shares
    payment: uint256 = owed - self.released[_beneficiary]
    assert payment > 0, "nothing to release"

    self.released[_beneficiary] = self.released[_beneficiary] + payment
    self.total_released = self.total_released + payment

    fee: uint256 = 0
    if msg.sender != _beneficiary and self.relayer_fee > 0:
        fee = self.relayer_fee
        if fee > payment:
            fee = payment
        success_fee: bool = extcall IERC20(self.token).transfer(self.treasury, fee)
        assert success_fee, "fee transfer failed"
        log RelayerFeePaid(treasury=self.treasury, amount=fee)

    net: uint256 = payment - fee
    success: bool = extcall IERC20(self.token).transfer(_beneficiary, net)
    assert success, "transfer failed"
    log PaymentReleased(beneficiary=_beneficiary, amount=payment, relayer=msg.sender)

    self._locked = False

