# Contributing

Contributions to `helius-python` are very welcome! This project aims to be the
**complete, typed Python client for [Helius](https://helius.dev)** and there
is a lot of surface area still to cover. Every issue closed, RPC method added,
typo fixed, and example improved moves the library closer to that goal.

## Project Goals

Before contributing, please read the [Goals section of the README](README.md#goals).
Every change should serve at least one of:

1. **Completeness** — 1:1 coverage of the entire Helius API surface.
2. **Type safety** — fully typed parameters and responses.
3. **Pythonic ergonomics** — `snake_case` names, context managers, sensible
   defaults.
4. **Zero magic** — thin, predictable wrappers that map directly to the
   documented Helius API.

If a change doesn't clearly support one of these goals, it probably isn't a
good fit. When in doubt, open an issue first to discuss it.

## Ways to Contribute

There is no shortage of things to do. A few ideas, roughly ordered from
easiest to most involved:

- **Fix a bug.** Reproduce, write the fix, send the PR.
- **Add a missing standard Solana JSON-RPC method.** Check the
  [supported methods table in the README](README.md#supported-methods) — anything
  in the [Solana JSON-RPC spec](https://solana.com/docs/rpc) that isn't listed
  is fair game.
- **Add a Helius-specific RPC extension** — enhanced transactions, DAS
  (Digital Asset Standard) methods, priority fee estimation, etc.
- **Add a Helius REST endpoint** — Enhanced Transactions API, Webhooks API,
  Mint API, token metadata, address lookups, and more.
- **Improve typing.** Tightening a `dict` return into a proper `pydantic`
  model, narrowing a `str` into a `Literal`, or replacing `Any` with a real
  type are all great contributions.
- **Improve error handling.** A consistent exception hierarchy for transport
  errors and Helius/Solana RPC errors is a known gap.
- **Add streaming / websocket support** once the synchronous surface is
  fleshed out.
- **Improve docs and examples.** Clearer docstrings, better README snippets,
  more realistic examples.

If you're not sure where to start, browse the
[open issues](https://github.com/markosnarinian/helius-python/issues).

## Before You Start a Large Change

**Please open an issue before working on anything non-trivial.** This includes:

- Architectural changes or refactors that span multiple files.
- New public APIs that aren't just wrapping an existing Helius/Solana endpoint.
- Changes to the existing public method signatures or behavior.
- Pulling in new runtime dependencies.
- Anything you expect to take more than an afternoon.

A quick conversation up-front saves everyone time and avoids the awkward case
of a large PR that has to be redesigned or rejected. Small, focused PRs — one
new RPC method, one bug fix, one model improvement — usually don't need
prior discussion; just send them.

## Codebase Conventions

Please match the existing style of the codebase. Skim
[`src/helius/client.py`](src/helius/client.py) and
[`src/helius/models.py`](src/helius/models.py) before writing new code. In
particular:

- **Method names** are `snake_case` versions of the upstream RPC method
  (`getAccountInfo` → `get_account_info`).
- **Parameter names** are `snake_case` versions of the upstream JSON field
  names (`minContextSlot` → `min_context_slot`).
- **Use the `RpcRequest` builder** to construct request payloads — `add(...)`
  for positional params, `set(key, value)` for fields inside the config
  object. Don't build the JSON dict by hand.
- **Type everything.** Parameters get explicit types, including `Literal`s
  for fixed string options (`commitment`, `encoding`, etc.). Return types are
  always declared.
- **Model responses with `pydantic`.** Add a model in
  [`src/helius/models.py`](src/helius/models.py) using the existing
  `AliasGenerator(validation_alias=to_camel)` pattern instead of returning a
  raw `dict`.
- **Follow the docs.** When implementing a new RPC method, read both the
  Helius guide and API reference for that method (see
  [`AGENTS.md`](AGENTS.md)) and mirror the documented parameters and response
  shape.
- **Keep wrappers thin.** No surprise retries, caching, or transformations.
  If the upstream API returns `{ context, value }`, return `(context, value)`
  — don't flatten it.

## Format and Lint Before Opening a PR

Run the formatters and type checker before pushing. PRs that aren't formatted
will be asked to reformat before review.

```bash
isort src
black src
basedpyright src
```

Make sure your change at least imports cleanly and the method you added
actually works against a real Helius endpoint.

Run the test suite with the local `src` package on the import path:

```bash
PYTHONPATH=src .venv/bin/pytest
```

## Pull Requests

- Keep PRs focused. One method, one bug fix, or one refactor per PR.
- Write a clear PR description: what changed, why, and a link to the relevant
  Helius/Solana docs for any new endpoint.
- Reference the issue your PR addresses (`Closes #123`).
- Be patient — reviews happen as time allows.

Thanks for contributing!
