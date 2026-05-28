# helius-python

**A complete, typed Python client for [Helius](https://helius.dev) — the Solana developer platform.** Every JSON-RPC method, typed end-to-end with `pydantic`, no boilerplate.

```bash
pip install helius-python
```

```python
# export HELIUS_API_KEY=your_key   (or put it in .env)
from helius.client import HeliusClient

with HeliusClient() as helius:
    _ctx, lamports = helius.get_balance("7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU")
    print(f"{lamports / 1_000_000_000:.4f} SOL")

    for sig in helius.get_signatures_for_address(
        "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU", limit=5
    ):
        print(sig.slot, "ERR" if sig.err else "OK ", sig.signature)
```

`HELIUS_API_KEY` is read from the environment (or `.env`), the
client is a context manager, and every return value is fully typed.

## Why this over `solana-py` / `solders`?

`solders` is for building and signing transactions. `solana-py` is a generic Solana RPC client. Use them for that.

This library is for talking to **Helius** specifically — typed `pydantic` responses, snake_case, and (eventually) the Helius-only endpoints (DAS, Enhanced Transactions, Webhooks, priority fees) the others don't cover. Plays nicely alongside `solders`: sign with `solders`, read with `helius-python`.

## Example: wallet tracker

See [`examples/wallet_tracker.py`](examples/wallet_tracker.py) for a
runnable script that takes a wallet address and prints:

- SOL balance
- All non-empty SPL token accounts (mint, balance, account)
- The last N transactions (timestamp, slot, success/error, signature)

```bash
export HELIUS_API_KEY=your_helius_api_key
python examples/wallet_tracker.py 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU --limit 20
```

It uses `get_balance`, `get_token_accounts_by_owner` (with
`encoding="jsonParsed"`), and `get_signatures_for_address` — pure
stdlib plus this library, no `solana-py` or `solders` needed.

## Coverage

The goal of this library is **support every function, method, endpoint,
and feature that Helius exposes.** If Helius ships it, this client
wraps it.

- ✅ **The full Solana JSON-RPC surface** proxied by Helius —
  `getAccountInfo`, `getBalance`, `getBlock`, `getTransaction`,
  `getProgramAccounts`, `getTokenAccountsByOwner`,
  `getSignaturesForAddress`, and every other standard RPC method.
  **(supported today)**
- 🚧 **All Helius-specific RPC extensions** — enhanced transactions, DAS
  (Digital Asset Standard) methods, priority fee estimation, and the
  rest of the Helius-only RPC namespace. **(in progress)**
- 🚧 **Every Helius REST endpoint** — Enhanced Transactions API,
  Webhooks API, Mint API, token metadata, address lookups, and beyond.
  **(in progress)**
- 🚧 **Platform features** — streaming, websockets, and any new
  capability Helius adds to its API. **(in progress)**

> **Current status:** only the standard Solana JSON-RPC surface is
> implemented today. Support for Helius RPC extensions, REST endpoints,
> and platform features is actively being worked on.

## Goals

1. **Completeness** — 1:1 coverage of the entire Helius API surface.
2. **Type safety** — fully typed responses.
3. **Pythonic ergonomics** — `get_account_info(...)` instead of
   `getAccountInfo(...)`, context managers.
4. **Zero magic** — thin, predictable wrappers that map directly to the
   documented Helius API.

## Authentication

Pass your Helius API key explicitly:

```python
from helius.client import HeliusClient

client = HeliusClient(api_key="YOUR_HELIUS_API_KEY")
```

or set `HELIUS_API_KEY` as an environment variable:

```bash
export HELIUS_API_KEY=your_helius_api_key
```

You can also set it in a `.env` file at the project root and let the
client pick it up automatically:

```env
HELIUS_API_KEY=your_helius_api_key
```

```python
from helius.client import HeliusClient

client = HeliusClient()  # reads HELIUS_API_KEY from the environment or .env
```

## Usage

### As a context manager (recommended)

```python
from helius.client import HeliusClient

with HeliusClient(api_key="YOUR_HELIUS_API_KEY") as client:
    _ctx, balance = client.get_balance("So11111111111111111111111111111111111111112")
    _ctx, supply  = client.get_supply()
    nodes         = client.get_cluster_nodes()
    block         = client.get_block(slot=250_000_000)
    tx            = client.get_transaction("5j7s...signature...")
```

`HeliusClient` implements the context-manager protocol via `__enter__` /
`__exit__`, so the underlying `httpx.Client` is closed cleanly when the
`with` block exits.

### With an explicit `close()` call

If a `with` block doesn't fit your code structure (e.g. the client lives
on a long-lived object), call `close()` yourself when you're done:

```python
from helius.client import HeliusClient

client = HeliusClient(api_key="YOUR_HELIUS_API_KEY")
try:
    _ctx, balance = client.get_balance("So11111111111111111111111111111111111111112")
    _ctx, supply  = client.get_supply()
finally:
    client.close()
```

Client classes also implement `__del__` as a safety net — if you forget
to `close()` or use `with`, the underlying HTTP client is still closed
when the instance is garbage-collected. Prefer `with` or `close()`
regardless.

> 🚧 **Exception & error handling is a work in progress.** Today,
> transport errors surface as raw `httpx` exceptions and Helius/Solana
> RPC errors are not yet wrapped in typed exception classes. A
> consistent error hierarchy is being worked on.

### Defaults

| Argument   | Default                                                                   | Notes                                                              |
| ---------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `base_url` | `"https://mainnet.helius-rpc.com"`                                        | Override to point at devnet, staging, or a custom Helius endpoint. |
| `api_key`  | `None` → falls back to `HELIUS_API_KEY` from the environment, then `.env` | If none is provided, the constructor raises `ValueError`.          |

Per-method RPC parameters (`commitment`, `encoding`, `min_context_slot`,
etc.) are left unset by default — the Helius/Solana server defaults
apply unless you pass them explicitly.

### Reference

For parameters, semantics, and return shapes, see the official Helius docs:
[RPC guide](https://www.helius.dev/docs/rpc) and
[API reference](https://www.helius.dev/docs/api-reference).

If you hit a bug, a missing parameter, or surprising behavior, please
[open an issue](https://github.com/markosnarinian/helius-python/issues).

### Supported methods

The method names map 1:1 to the Solana JSON-RPC spec, just converted to
`snake_case`. If you know the RPC method name, you know the Python function.

## Status

Actively expanding toward full coverage of the Helius API. See
[`src/helius/client.py`](src/helius/client.py) for the current list of
implemented methods; missing endpoints are tracked as issues and added
continuously.

| Solana JSON-RPC method              | Python method                                        | Helius docs                                                                                                                                                                     |
| ----------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `getAccountInfo`                    | `client.get_account_info(...)`                       | [guide](https://www.helius.dev/docs/rpc/guides/getaccountinfo) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getaccountinfo)                                       |
| `getBalance`                        | `client.get_balance(...)`                            | [guide](https://www.helius.dev/docs/rpc/guides/getbalance) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getbalance)                                               |
| `getBlock`                          | `client.get_block(...)`                              | [guide](https://www.helius.dev/docs/rpc/guides/getblock) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getblock)                                                   |
| `getBlockCommitment`                | `client.get_block_commitment(...)`                   | [guide](https://www.helius.dev/docs/rpc/guides/getblockcommitment) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getblockcommitment)                               |
| `getBlockHeight`                    | `client.get_block_height(...)`                       | [guide](https://www.helius.dev/docs/rpc/guides/getblockheight) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getblockheight)                                       |
| `getBlockProduction`                | `client.get_block_production(...)`                   | [guide](https://www.helius.dev/docs/rpc/guides/getblockproduction) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getblockproduction)                               |
| `getBlocks`                         | `client.get_blocks(...)`                             | [guide](https://www.helius.dev/docs/rpc/guides/getblocks) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getblocks)                                                 |
| `getBlocksWithLimit`                | `client.get_blocks_with_limit(...)`                  | [guide](https://www.helius.dev/docs/rpc/guides/getblockswithlimit) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getblockswithlimit)                               |
| `getBlockTime`                      | `client.get_block_time(...)`                         | [guide](https://www.helius.dev/docs/rpc/guides/getblocktime) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getblocktime)                                           |
| `getClusterNodes`                   | `client.get_cluster_nodes()`                         | [guide](https://www.helius.dev/docs/rpc/guides/getclusternodes) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getclusternodes)                                     |
| `getEpochInfo`                      | `client.get_epoch_info(...)`                         | [guide](https://www.helius.dev/docs/rpc/guides/getepochinfo) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getepochinfo)                                           |
| `getEpochSchedule`                  | `client.get_epoch_schedule()`                        | [guide](https://www.helius.dev/docs/rpc/guides/getepochschedule) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getepochschedule)                                   |
| `getFeeForMessage`                  | `client.get_fee_for_message(...)`                    | [guide](https://www.helius.dev/docs/rpc/guides/getfeeformessage) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getfeeformessage)                                   |
| `getFirstAvailableBlock`            | `client.get_first_available_block()`                 | [guide](https://www.helius.dev/docs/rpc/guides/getfirstavailableblock) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getfirstavailableblock)                       |
| `getGenesisHash`                    | `client.get_genesis_hash()`                          | [guide](https://www.helius.dev/docs/rpc/guides/getgenesishash) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getgenesishash)                                       |
| `getHealth`                         | `client.get_health()`                                | [guide](https://www.helius.dev/docs/rpc/guides/gethealth) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/gethealth)                                                 |
| `getHighestSnapshotSlot`            | `client.get_highest_snapshot_slot()`                 | [guide](https://www.helius.dev/docs/rpc/guides/gethighestsnapshotslot) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/gethighestsnapshotslot)                       |
| `getIdentity`                       | `client.get_identity()`                              | [guide](https://www.helius.dev/docs/rpc/guides/getidentity) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getidentity)                                             |
| `getInflationGovernor`              | `client.get_inflation_governor(...)`                 | [guide](https://www.helius.dev/docs/rpc/guides/getinflationgovernor) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getinflationgovernor)                           |
| `getInflationRate`                  | `client.get_inflation_rate()`                        | [guide](https://www.helius.dev/docs/rpc/guides/getinflationrate) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getinflationrate)                                   |
| `getLargestAccounts`                | `client.get_largest_accounts(...)`                   | [guide](https://www.helius.dev/docs/rpc/guides/getlargestaccounts) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getlargestaccounts)                               |
| `getLatestBlockhash`                | `client.get_latest_blockhash(...)`                   | [guide](https://www.helius.dev/docs/rpc/guides/getlatestblockhash) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getlatestblockhash)                               |
| `getLeaderSchedule`                 | `client.get_leader_schedule(...)`                    | [guide](https://www.helius.dev/docs/rpc/guides/getleaderschedule) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getleaderschedule)                                 |
| `getMaxRetransmitSlot`              | `client.get_max_retransmit_slot()`                   | [guide](https://www.helius.dev/docs/rpc/guides/getmaxretransmitslot) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getmaxretransmitslot)                           |
| `getMaxShredInsertSlot`             | `client.get_max_shred_insert_slot()`                 | [guide](https://www.helius.dev/docs/rpc/guides/getmaxshredinsertslot) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getmaxshredinsertslot)                         |
| `getMinimumBalanceForRentExemption` | `client.get_minimum_balance_for_rent_exemption(...)` | [guide](https://www.helius.dev/docs/rpc/guides/getminimumbalanceforrentexemption) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getminimumbalanceforrentexemption) |
| `getMultipleAccounts`               | `client.get_multiple_accounts(...)`                  | [guide](https://www.helius.dev/docs/rpc/guides/getmultipleaccounts) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getmultipleaccounts)                             |
| `getProgramAccounts`                | `client.get_program_accounts(...)`                   | [guide](https://www.helius.dev/docs/rpc/guides/getprogramaccounts) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getprogramaccounts)                               |
| `getRecentPerformanceSamples`       | `client.get_recent_performance_samples(...)`         | [guide](https://www.helius.dev/docs/rpc/guides/getrecentperformancesamples) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getrecentperformancesamples)             |
| `getRecentPrioritizationFees`       | `client.get_recent_prioritization_fees(...)`         | [guide](https://www.helius.dev/docs/rpc/guides/getrecentprioritizationfees) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getrecentprioritizationfees)             |
| `getSignaturesForAddress`           | `client.get_signatures_for_address(...)`             | [guide](https://www.helius.dev/docs/rpc/guides/getsignaturesforaddress) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getsignaturesforaddress)                     |
| `getSignatureStatuses`              | `client.get_signature_statuses(...)`                 | [guide](https://www.helius.dev/docs/rpc/guides/getsignaturestatuses) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getsignaturestatuses)                           |
| `getSlot`                           | `client.get_slot(...)`                               | [guide](https://www.helius.dev/docs/rpc/guides/getslot) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getslot)                                                     |
| `getSlotLeader`                     | `client.get_slot_leader(...)`                        | [guide](https://www.helius.dev/docs/rpc/guides/getslotleader) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getslotleader)                                         |
| `getSlotLeaders`                    | `client.get_slot_leaders(...)`                       | [guide](https://www.helius.dev/docs/rpc/guides/getslotleaders) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getslotleaders)                                       |
| `getStakeMinimumDelegation`         | `client.get_stake_minimum_delegation(...)`           | [guide](https://www.helius.dev/docs/rpc/guides/getstakeminimumdelegation) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getstakeminimumdelegation)                 |
| `getSupply`                         | `client.get_supply(...)`                             | [guide](https://www.helius.dev/docs/rpc/guides/getsupply) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getsupply)                                                 |
| `getTokenAccountBalance`            | `client.get_token_account_balance(...)`              | [guide](https://www.helius.dev/docs/rpc/guides/gettokenaccountbalance) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/gettokenaccountbalance)                       |
| `getTokenAccountsByDelegate`        | `client.get_token_accounts_by_delegate(...)`         | [guide](https://www.helius.dev/docs/rpc/guides/gettokenaccountsbydelegate) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/gettokenaccountsbydelegate)               |
| `getTokenAccountsByOwner`           | `client.get_token_accounts_by_owner(...)`            | [guide](https://www.helius.dev/docs/rpc/guides/gettokenaccountsbyowner) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/gettokenaccountsbyowner)                     |
| `getTokenLargestAccounts`           | `client.get_token_largest_accounts(...)`             | [guide](https://www.helius.dev/docs/rpc/guides/gettokenlargestaccounts) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/gettokenlargestaccounts)                     |
| `getTokenSupply`                    | `client.get_token_supply(...)`                       | [guide](https://www.helius.dev/docs/rpc/guides/gettokensupply) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/gettokensupply)                                       |
| `getTransaction`                    | `client.get_transaction(...)`                        | [guide](https://www.helius.dev/docs/rpc/guides/gettransaction) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/gettransaction)                                       |
| `getTransactionCount`               | `client.get_transaction_count(...)`                  | [guide](https://www.helius.dev/docs/rpc/guides/gettransactioncount) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/gettransactioncount)                             |
| `getVersion`                        | `client.get_version()`                               | [guide](https://www.helius.dev/docs/rpc/guides/getversion) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getversion)                                               |
| `getVoteAccounts`                   | `client.get_vote_accounts(...)`                      | [guide](https://www.helius.dev/docs/rpc/guides/getvoteaccounts) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/getvoteaccounts)                                     |
| `isBlockhashValid`                  | `client.is_blockhash_valid(...)`                     | [guide](https://www.helius.dev/docs/rpc/guides/isblockhashvalid) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/isblockhashvalid)                                   |
| `minimumLedgerSlot`                 | `client.minimum_ledger_slot()`                       | [guide](https://www.helius.dev/docs/rpc/guides/minimumledgerslot) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/minimumledgerslot)                                 |
| `requestAirdrop`                    | `client.request_airdrop(...)`                        | [guide](https://www.helius.dev/docs/rpc/guides/requestairdrop) · [ref](https://www.helius.dev/docs/api-reference/rpc/http/requestairdrop)                                       |

## License

[MIT](LICENSE)
