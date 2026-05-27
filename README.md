# helius-python

A **complete, typed Python client for [Helius](https://helius.dev)** — the
Solana developer platform.

The goal of this library is simple: **support every function, method,
endpoint, and feature that Helius exposes.** If Helius ships it, this client
wraps it.

That includes:

- ✅ **The full Solana JSON-RPC surface** proxied by Helius — `getAccountInfo`,
  `getBalance`, `getBlock`, `getTransaction`, `getProgramAccounts`,
  `getTokenAccountsByOwner`, `getSignaturesForAddress`, and every other
  standard RPC method. **(supported today)**
- 🚧 **All Helius-specific RPC extensions** — enhanced transactions, DAS
  (Digital Asset Standard) methods, priority fee estimation, and the rest of
  the Helius-only RPC namespace. **(in progress)**
- 🚧 **Every Helius REST endpoint** — Enhanced Transactions API, Webhooks API,
  Mint API, token metadata, address lookups, and beyond. **(in progress)**
- 🚧 **Platform features** — streaming, websockets, and any new capability
  Helius adds to its API. **(in progress)**

> **Current status:** only the standard Solana JSON-RPC surface is implemented
> today. Support for Helius RPC extensions, REST endpoints, and platform
> features is actively being worked on.

Every method has typed parameters, typed return values, and dedicated model
classes built on `pydantic`, so you get full editor autocomplete and static
type checking.

## Goals

1. **Completeness** — 1:1 coverage of the entire Helius API surface.
2. **Type safety** — fully typed responses.
3. **Pythonic ergonomics** — `get_account_info(...)` instead of
   `getAccountInfo(...)`, context managers.
4. **Zero magic** — thin, predictable wrappers that map directly to the
   documented Helius API.

## Installation

```bash
pip install helius-python
```

## Authentication

Pass your Helius API key explicitly:

```python
from helius import HeliusClient

client = HeliusClient(api_key="YOUR_HELIUS_API_KEY")
```

or set it in a `.env` file at the project root and let the client pick it up
automatically:

```env
HELIUS_API_KEY=your_helius_api_key
```

```python
from helius import HeliusClient

client = HeliusClient()  # reads HELIUS_API_KEY from .env
```

## Usage

### As a context manager (recommended)

```python
from helius import HeliusClient

with HeliusClient(api_key="YOUR_HELIUS_API_KEY") as client:
    balance = client.get_balance("So11111111111111111111111111111111111111112")
    supply  = client.get_supply()
    nodes   = client.get_cluster_nodes()
    block   = client.get_block(slot=250_000_000)
    tx      = client.get_transaction("5j7s...signature...")
```

`HeliusClient` implements the context-manager protocol via `__enter__` /
`__exit__`, so the underlying `httpx.Client` is closed cleanly when the
`with` block exits.

### With an explicit `close()` call

If a `with` block doesn't fit your code structure (e.g. the client lives on
a long-lived object), call `close()` yourself when you're done:

```python
from helius import HeliusClient

client = HeliusClient(api_key="YOUR_HELIUS_API_KEY")
try:
    balance = client.get_balance("So11111111111111111111111111111111111111112")
    supply  = client.get_supply()
finally:
    client.close()
```

Client classes also implement `__del__` as a safety net — if you forget to
`close()` or use `with`, the underlying HTTP client is still closed when the
instance is garbage-collected. Prefer `with` or `close()` regardless.

> 🚧 **Exception & error handling is a work in progress.** Today, transport
> errors surface as raw `httpx` exceptions and Helius/Solana RPC errors are
> not yet wrapped in typed exception classes. A consistent error hierarchy is
> being worked on.

### Defaults

| Argument  | Default                              | Notes                                                                                         |
| --------- | ------------------------------------ | --------------------------------------------------------------------------------------------- |
| `base_url`| `"https://mainnet.helius-rpc.com"`   | Override to point at devnet, staging, or a custom Helius endpoint.                            |
| `api_key` | `None` → falls back to `HELIUS_API_KEY` in a `.env` file | If neither is provided, the constructor raises `ValueError`.   |

Per-method RPC parameters (`commitment`, `encoding`, `min_context_slot`, etc.)
are left unset by default — the Helius/Solana server defaults apply unless you
pass them explicitly.

### Supported methods

The method names map 1:1 to the Solana JSON-RPC spec, just converted to
`snake_case`. If you know the RPC method name, you know the Python function.

| Solana JSON-RPC method            | Python method                              |
| --------------------------------- | ------------------------------------------ |
| `getAccountInfo`                  | `client.get_account_info(...)`             |
| `getBalance`                      | `client.get_balance(...)`                  |
| `getBlock`                        | `client.get_block(...)`                    |
| `getBlockCommitment`              | `client.get_block_commitment(...)`         |
| `getBlockHeight`                  | `client.get_block_height(...)`             |
| `getBlockProduction`              | `client.get_block_production(...)`         |
| `getBlocks`                       | `client.get_blocks(...)`                   |
| `getBlocksWithLimit`              | `client.get_blocks_with_limit(...)`        |
| `getBlockTime`                    | `client.get_block_time(...)`               |
| `getClusterNodes`                 | `client.get_cluster_nodes()`               |
| `getEpochInfo`                    | `client.get_epoch_info(...)`               |
| `getEpochSchedule`                | `client.get_epoch_schedule()`              |
| `getFeeForMessage`                | `client.get_fee_for_message(...)`          |
| `getFirstAvailableBlock`          | `client.get_first_available_block()`       |
| `getGenesisHash`                  | `client.get_genesis_hash()`                |
| `getHealth`                       | `client.get_health()`                      |
| `getHighestSnapshotSlot`          | `client.get_highest_snapshot_slot()`       |
| `getIdentity`                     | `client.get_identity()`                    |
| `getInflationGovernor`            | `client.get_inflation_governor(...)`       |
| `getInflationRate`                | `client.get_inflation_rate()`              |
| `getLargestAccounts`              | `client.get_largest_accounts(...)`         |
| `getLatestBlockhash`              | `client.get_latest_blockhash(...)`         |
| `getLeaderSchedule`               | `client.get_leader_schedule(...)`          |
| `getMaxRetransmitSlot`            | `client.get_max_retransmit_slot()`         |
| `getMaxShredInsertSlot`           | `client.get_max_shred_insert_slot()`       |
| `getMinimumBalanceForRentExemption` | `client.get_minimum_balance_for_rent_exemption(...)` |
| `getMultipleAccounts`             | `client.get_multiple_accounts(...)`        |
| `getProgramAccounts`              | `client.get_program_accounts(...)`         |
| `getRecentPerformanceSamples`     | `client.get_recent_performance_samples(...)` |
| `getRecentPrioritizationFees`     | `client.get_recent_prioritization_fees(...)` |
| `getSignaturesForAddress`         | `client.get_signatures_for_address(...)`   |
| `getSignatureStatuses`            | `client.get_signature_statuses(...)`       |
| `getSlot`                         | `client.get_slot(...)`                     |
| `getSlotLeader`                   | `client.get_slot_leader(...)`              |
| `getSlotLeaders`                  | `client.get_slot_leaders(...)`             |
| `getStakeMinimumDelegation`       | `client.get_stake_minimum_delegation(...)` |
| `getSupply`                       | `client.get_supply(...)`                   |
| `getTokenAccountBalance`          | `client.get_token_account_balance(...)`    |
| `getTokenAccountsByDelegate`      | `client.get_token_accounts_by_delegate(...)` |
| `getTokenAccountsByOwner`         | `client.get_token_accounts_by_owner(...)`  |
| `getTokenLargestAccounts`         | `client.get_token_largest_accounts(...)`   |
| `getTokenSupply`                  | `client.get_token_supply(...)`             |
| `getTransaction`                  | `client.get_transaction(...)`              |
| `getTransactionCount`             | `client.get_transaction_count(...)`        |
| `getVersion`                      | `client.get_version()`                     |

### Reference

The functions are intentionally thin and intuitive — for a full description
of each method's parameters, semantics, and response shape, refer to the
[Helius RPC docs](https://www.helius.dev/docs/rpc) and the
[Solana JSON-RPC docs](https://solana.com/docs/rpc). Anywhere this client
deviates from upstream, the behavior is documented in the method's docstring.

If you hit a bug, a missing parameter, or surprising behavior, please
[open an issue](https://github.com/markosnarinian/helius-python/issues).

## Status

Actively expanding toward full coverage of the Helius API. See
[`src/helius/client.py`](src/helius/client.py) for the current list of
implemented methods; missing endpoints are tracked as issues and added
continuously.

## License

[MIT](LICENSE)
