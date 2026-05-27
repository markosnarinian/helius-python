# helius-python

A **complete, typed Python client for [Helius](https://helius.dev)** — the
Solana developer platform.

The goal of this library is simple: **support every function, method,
endpoint, and feature that Helius exposes.** If Helius ships it, this client
wraps it.

That includes:

- **The full Solana JSON-RPC surface** proxied by Helius — `getAccountInfo`,
  `getBalance`, `getBlock`, `getTransaction`, `getProgramAccounts`,
  `getTokenAccountsByOwner`, `getSignaturesForAddress`, and every other
  standard RPC method.
- **All Helius-specific RPC extensions** — enhanced transactions, DAS
  (Digital Asset Standard) methods, priority fee estimation, and the rest of
  the Helius-only RPC namespace.
- **Every Helius REST endpoint** — Enhanced Transactions API, Webhooks API,
  Mint API, token metadata, address lookups, and beyond.
- **Platform features** — streaming, websockets, and any new capability
  Helius adds to its API.

Every method has typed parameters, typed return values, and dedicated model
classes built on `pydantic`, so you get full editor autocomplete and static
type checking.

## Goals

1. **Completeness** — 1:1 coverage of the entire Helius API surface.
2. **Type safety** — fully typed responses, no `dict[str, Any]` escape
   hatches.
3. **Pythonic ergonomics** — `get_account_info(...)` instead of
   `getAccountInfo(...)`, context managers, sensible defaults.
4. **Zero magic** — thin, predictable wrappers that map directly to the
   documented Helius API.

## Installation

```bash
pip install helius-python
```

Requires Python 3.9 or newer.

## Authentication

Pass your Helius API key explicitly:

```python
from helius import HeliusClient

client = HeliusClient(api_key="YOUR_HELIUS_API_KEY")
```

…or set it in a `.env` file at the project root and let the client pick it up
automatically:

```env
HELIUS_API_KEY=your_helius_api_key
```

```python
from helius import HeliusClient

client = HeliusClient()  # reads HELIUS_API_KEY from .env
```

## Usage

```python
from helius import HeliusClient

with HeliusClient(api_key="YOUR_HELIUS_API_KEY") as client:
    balance = client.get_balance("So11111111111111111111111111111111111111112")
    supply  = client.get_supply()
    nodes   = client.get_cluster_nodes()
    block   = client.get_block(slot=250_000_000)
    tx      = client.get_transaction("5j7s...signature...")
```

Because the client implements the context-manager protocol, the underlying
HTTP connection is closed cleanly when the `with` block exits.

## Status

Actively expanding toward full coverage of the Helius API. See
[`src/helius/client.py`](src/helius/client.py) for the current list of
implemented methods; missing endpoints are tracked as issues and added
continuously.

## License

[MIT](LICENSE)
