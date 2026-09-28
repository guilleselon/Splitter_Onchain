
# @version ^0.4.3

interface ISplitter:
    def initialize(
        _token: address,
        _beneficiaries: DynArray[address, 20],
        _shares: DynArray[uint256, 20],
        _treasury: address,
        _relayer_fee: uint256,
    ): nonpayable

event SplitterCreated:
    splitter: indexed(address)
    config_hash: indexed(bytes32)
    actual_salt: bytes32
    creator: indexed(address)

master: public(address)
deployer: public(address)

splitters: public(HashMap[bytes32, address])

@deploy
def __init__(_master: address, _deployer: address):
    assert _master != empty(address), "zero master"
    assert _deployer != empty(address), "zero deployer"
    self.master = _master
    self.deployer = _deployer

@external
def create(
    _token: address,
    _beneficiaries: DynArray[address, 20],
    _shares: DynArray[uint256, 20],
    _treasury: address,
    _relayer_fee: uint256,
    _config_hash: bytes32,
) -> address:
    assert msg.sender == self.deployer, "only deployer"

    actual_salt: bytes32 = keccak256(abi_encode(msg.sender, _config_hash))
    assert self.splitters[actual_salt] == empty(address), "already deployed"

    proxy: address = create_minimal_proxy_to(self.master, salt=actual_salt)
    extcall ISplitter(proxy).initialize(
        _token,
        _beneficiaries,
        _shares,
        _treasury,
        _relayer_fee,
    )
    self.splitters[actual_salt] = proxy

    log SplitterCreated(
        splitter=proxy,
        config_hash=_config_hash,
        actual_salt=actual_salt,
        creator=msg.sender,
    )
    return proxy
