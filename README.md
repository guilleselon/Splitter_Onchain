# Splitter

A service for deploying on-chain payment distribution contracts in USDC on Monad.

## Core principles

- **Immutable:** contracts have no owner, no admin, no upgrade. Rules are fixed at deployment.
- **Non-custodial:** the service never touches funds. Funds live in the contract until each beneficiary withdraws.
- **No KYC:** permissionless access. No identities collected.
- **No wallet connection:** the payer sends a plain USDC transfer from any wallet.
- **Pull payment:** beneficiaries withdraw when they want; a relayer can do it for them.
- **Verifiable:** anyone can audit the distribution, balance and history on-chain.

## Architecture

Three independent services, one shared Monad chain.

```
┌──────────────────┐
│  Splitter master │  (implementation, deployed once)
└────────┬─────────┘
         │
┌────────▼─────────┐
│ SplitterFactory  │  (CREATE2 factory, deployed once)
└────────┬─────────┘
         │
         │ creates
         ▼
┌──────────────────┐
│  Splitter clone  │  (one per distribution)
└──────────────────┘

Services:
  deployer (5002)  — detects payments, deploys splitters
  relayer  (5003)  — signs release() on behalf of beneficiaries
  web      (5001)  — user-facing HTML interface
```

## Directory structure

```
.
├── config.py                 Global config (deployer + relayer)
├── deploy_contracts.py       Deploy master + factory to Monad
├── requirements.txt          Runtime dependencies
├── requirements-dev.txt      Development dependencies
├── contracts/
│   └── src/
│       ├── Splitter.vy
│       └── SplitterFactory.vy
├── deployer/
│   ├── api.py                HTTP API (FastHTML)
│   ├── state.py              JSON state (pending + processed)
│   ├── verifier.py           Read USDC balance
│   ├── executor.py           Sign and send Factory.create()
│   ├── watcher.py            Background loop
│   └── main.py               Entry point
├── relayer/
│   ├── client.py             Read state + sign release()
│   ├── api.py                HTTP API
│   └── main.py               Entry point
├── web/
│   ├── app.py                Entry point
│   ├── config.py             Web config
│   ├── clients/              HTTP + chain clients
│   ├── components/           UI components
│   └── routes/               HTML + JSON routes
├── shared/
│   ├── config_hash.py        Canonical hash of a config
│   ├── validation.py         Address and share validation
│   ├── formatting.py         USDC / address formatting
│   ├── constants.py          Chain IDs, USDC addresses
│   └── abis/                 Generated ABIs
└── .env                      Secrets and configuration (gitignored)
```

## Requirements

- Python 3.11+
- An RPC URL for Monad (testnet or mainnet)
- A wallet with MON for gas
- USDC on the target chain (for end-to-end testing)

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in:

```env
MONAD_RPC_URL=https://testnet-rpc.monad.xyz
CHAIN_ID=10143
USDC_ADDRESS=0x534b2f3A21130d7a60830c2Df862319e593943A3
WALLET_PRIVATE_KEY=0x...
TREASURY_ADDRESS=0x...
```

### 3. Deploy contracts

```bash
python deploy_contracts.py --network testnet
```

This deploys:
- `Splitter.vy` (master implementation)
- `SplitterFactory.vy` (CREATE2 factory)

Copy the printed addresses into `.env`:

```env
FACTORY_ADDRESS=0x...
```

### 4. Verify contracts on Monadscan

After deployment, verify the source code so anyone can audit it:

- **Testnet:** https://testnet.monadscan.com/verifyContract
- **Mainnet:** https://monadscan.com/verifyContract

## Running

The three services run as independent processes.

### Deployer (port 5002)

```bash
python -m deployer.main
```

Connects to the RPC, starts the watcher (polls every 60 s for pending payments), and serves the API used by the web.

### Relayer (port 5003)

```bash
python -m relayer.main
```

Signs `release(beneficiary)` transactions on behalf of beneficiaries who cannot or prefer not to sign themselves. Charges a fixed fee (set in the contract).

### Web (port 5001)

```bash
python -m web.app
```

Serves the public interface. Open `http://localhost:5001`.

### In production

Run each service under a process manager (systemd, supervisor, pm2) so they restart on failure. **Do not run all three in a single terminal** — if one crashes, the others should stay up.

## How it works

### Creating a splitter

1. User opens `/create`, defines beneficiaries and shares.
2. The web computes `config_hash` and asks the deployer to predict the
   splitter address (via `Factory.create(...).call()`).
3. The web shows the deterministic address and the required fee (2 USDC).
4. The user sends exactly 2 USDC to that address from any wallet.
5. The deployer's watcher detects the balance on-chain.
6. The deployer calls `Factory.create()`, deploying the splitter at that
   exact address.
7. During `initialize()`, the fee is swept to the treasury.

### Distributing funds

1. Anyone sends USDC to the splitter address.
2. Each beneficiary can:
   - Call `release(beneficiary)` themselves from any wallet (no fee).
   - Ask the relayer to do it (fixed fee, e.g. 0.10 USDC).

### Claiming

Beneficiaries find their splitter through:

- **Direct link:** `{WEB_PUBLIC_URL}/claim/{splitter_address}`
- **Search page:** `/claim` with a paste-address search bar
- **Share link:** the organizer can copy a link and a QR from `/split/{address}`

## Contracts

### `Splitter.vy`

- Immutable: no owner, no admin, no upgrade.
- Receives USDC; distributes according to fixed shares (max 20 beneficiaries).
- `initialize()` runs once, sweeps any pre-existing balance to the treasury.
- `release(beneficiary)` pays the beneficiary minus relayer fee (if caller
  is not the beneficiary).
- `_locked` guard against reentrancy.

### `SplitterFactory.vy`

- Only the deployer can call `create()`.
- Uses CREATE2 with `salt = keccak256(msg.sender, config_hash)`.
- Reverts if a splitter with the same salt already exists.
- Registers addresses in `splitters[salt]`.

## Configuration reference

| Variable | Purpose |
|---|---|
| `MONAD_RPC_URL` | Monad testnet RPC |
| `MONAD_MAINNET_RPC_URL` | Monad mainnet RPC |
| `CHAIN_ID` | `10143` (testnet) or `143` (mainnet) |
| `USDC_ADDRESS` | USDC contract address |
| `FACTORY_ADDRESS` | Deployed SplitterFactory |
| `WALLET_PRIVATE_KEY` | Service wallet (deployer + relayer) |
| `TREASURY_ADDRESS` | Where fees are sent |
| `SERVICE_FEE_USDC` | Fee per deployment (default 2.00) |
| `RELAYER_FEE_USDC` | Fee per claim (default 0.10) |
| `WATCHER_INTERVAL_SECONDS` | Poll interval (default 60) |
| `MAX_DEPLOY_ATTEMPTS` | Retries before marking an order as failed (default 3) |
| `WEB_PUBLIC_URL` | Public base URL for share links |

## Security notes

- `WALLET_PRIVATE_KEY` is never logged. Never commit `.env`.
- The contracts have no admin functions. Nobody can change rules.
- The service wallet is only used by the deployer and relayer, never by
  the web process.
- The web reads the chain but never signs anything.

## License

MIT
