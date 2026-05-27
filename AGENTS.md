When implementing a function for a RPC method in the HeliusClient class, read the docs for the specific RPC method. For example, for the get_supply function (getSupply RPC method) you should read https://www.helius.dev/docs/rpc/guides/getsupply and https://www.helius.dev/docs/api-reference/rpc/http/getsupply.

# API Reference

The API reference is generated from **Google-style docstrings** on every public symbol in `src/helius/`. Whenever you add or modify a public method, model, or class, you MUST write or update its docstring following the rules below. The README's "Supported methods" table is a quick index only — the docstring is the source of truth.

## Where docstrings live

- **Client methods** (`HeliusClient.get_*`, `is_*`, `request_*`, etc.) — every public method gets a docstring. Private methods (`_send`, dunders) do not need one.
- **Models** (`src/helius/models.py`) — every public model class gets a docstring describing what it represents. Individual fields don't need per-field docstrings if their names and types are self-explanatory; only document fields where the meaning, units, or nullability isn't obvious from the type alone.
- **Builders / helpers** (`RpcRequest`) — class docstring describing purpose, plus one-line docstrings on each public method.

## Client method docstring format

Use Google-style sections. Order matters; omit any section that doesn't apply.

```python
def method_name(self, ...) -> ReturnType:
    """One-line summary in the imperative mood, ending with a period.

    Optional longer description: a paragraph or two on what the method does,
    when to use it, and any non-obvious behavior. Keep this short — link to
    the upstream Helius docs rather than restating them.

    Args:
        param_one: Description of the first parameter, including units
            (lamports vs. SOL, slot vs. block height) when relevant. Mention
            the upstream JSON field name only if it differs in a non-obvious
            way from the snake_case Python name.
        param_two: Description. Note constraints like "must be base-58
            encoded" or "max 500_000 slots from `start_slot`".
        commitment: Optional commitment level. Defaults to the node's default
            when omitted.

    Returns:
        Describe the return shape. For tuples, describe each element in
        order. For models, name the model and what it represents. For
        primitives, name the unit (e.g. "Balance in lamports.").

    Raises:
        ValueError: When the arguments violate the documented constraints
            (e.g. mutually exclusive params, mismatched pairs).

    Note:
        Only available on Devnet and Testnet, not Mainnet Beta.

    See Also:
        - Helius guide: https://www.helius.dev/docs/rpc/guides/<method>
        - Helius API reference: https://www.helius.dev/docs/api-reference/rpc/http/<method>
    """
```

Rules:

- **Summary line** is one sentence, imperative mood, ≤ 88 chars, ends with a period. Example: `"Return the SOL balance of an account in lamports."`
- **`Args:`** documents every parameter, even `commitment` and `min_context_slot`. One entry per param. Don't re-state the type — basedpyright already shows it.
- **`Returns:`** is mandatory unless the method returns `None`.
- **`Raises:`** is required if the method calls `raise` directly. Don't document exceptions that bubble up from `httpx` — those are covered by the library-wide error-handling docs.
- **`Note:`** for network restrictions, version requirements, pagination limits, deprecation warnings, etc. One section per concern.
- **`See Also:`** ALWAYS includes the Helius guide and API reference URLs for the underlying RPC method. This is the contract for an RPC wrapper — the docstring tells you what we do, the upstream docs tell you what the network does.
- Keep prose tight. The docstring should be readable in `help(client.method)` without scrolling forever.

## Model docstring format

```python
class Supply(BaseModel):
    """Total, circulating, and non-circulating SOL supply, in lamports.

    Returned as the `value` field of `getSupply`. All amounts are in
    lamports (1 SOL = 1_000_000_000 lamports).

    See Also:
        - Helius API reference: https://www.helius.dev/docs/api-reference/rpc/http/getsupply
    """
    ...
```

Rules:

- One-line summary + optional paragraph + `See Also:` linking the upstream docs that define the shape.
- If a field has surprising semantics (e.g. `ui_amount` can be `None` when the mint has too many decimals, `non_circulating_accounts` is only populated when not excluded), document it inline with `Field(..., description="...")` or in the class docstring.

## Conventions

- Use **double-quoted triple strings** (`"""..."""`).
- Wrap docstring lines at 88 columns.
- Refer to parameters in backticks: `` `commitment` ``, `` `min_context_slot` ``.
- Refer to other client methods with their snake_case name in backticks: `` `get_balance` ``.
- Do NOT include the upstream JSON-RPC method name in the summary — that's already in the See Also URLs.
- Do NOT copy-paste large chunks from the Helius docs. Summarize and link.
- Examples (`Example:` section) are encouraged for methods with non-trivial argument combinations (e.g. `get_block_production`, `get_token_accounts_by_owner`), optional for everything else.

## Checklist for adding a new client method

1. Read both Helius doc URLs for the RPC method (see the top of this file).
2. Implement the method.
3. Add a docstring with `Args`, `Returns`, `Raises` (if any), `Note` (if any), and `See Also` with both Helius URLs.
4. Add the method to the "Supported methods" table in `README.md`.
5. Add tests per the Testing section.

# Testing

## Stack

- `pytest` as the test runner.
- `respx` for mocking the `httpx` transport. Do NOT use `unittest.mock` to patch `httpx` — always mock at the HTTP layer with `respx`.
- No live network calls. Do NOT make real requests to `mainnet.helius-rpc.com`, `devnet.helius-rpc.com`, or any other Helius endpoint in tests. Devnet integration tests are explicitly out of scope for now.

Add `pytest` and `respx` to a `[project.optional-dependencies] dev` table in `pyproject.toml` if not already present.

## Layout

```
tests/
  conftest.py            # shared fixtures (client factory, sample responses)
  fixtures/              # captured JSON-RPC response bodies, one file per shape
  unit/
    test_rpc_request.py  # RpcRequest builder
    test_models.py       # pydantic model validation against fixtures
    test_client.py       # one test (or small group) per client method
```

## Three Layers

### 1. `RpcRequest` builder — pure unit tests

`RpcRequest` is pure logic with no I/O. Cover:

- `add(value)` skips `None` unless `can_be_none=True`.
- `set(key, value)` skips `None` unless `can_be_none=True`.
- Positional params come before the config dict.
- The config dict is appended as the last element of `params` only when it's non-empty.
- `params` is omitted entirely from the payload when there are no positional or config values.
- `method`, `id`, and `jsonrpc` are passed through correctly.

These tests would have caught the current bug where `jsonrpc` is never added to the built payload. Fix bugs you find this way as separate commits, not as part of the test PR.

### 2. Pydantic models — fixture-based unit tests

For each model in `src/helius/models.py`:

- Capture a real JSON-RPC `result` body once (manually, from the Helius docs' example responses or a one-off live call) and save it under `tests/fixtures/`.
- Write a test that loads the fixture and calls `Model.model_validate(...)`. Assert a couple of representative fields parsed correctly (especially camelCase → snake_case via the alias generator).

One fixture per model is enough. The goal is to catch schema mismatches (missing fields, wrong optionality, typos like `foudnation`), not to exhaustively assert every field.

### 3. Client methods — `respx`-mocked tests

For each method on `HeliusClient`, write at least one test that asserts **both** sides of the wire:

- **Outgoing request:** the JSON body sent to Helius matches the JSON-RPC payload you expect — correct `method`, correct positional `params`, correct config object with snake → camel mapping, and optional arguments omitted when `None`.
- **Return value:** the method correctly parses a canned response into the documented return shape (model, tuple, primitive, etc.).

Also assert that the `api-key` query parameter is present on the request URL.

Skeleton:

```python
import json
import httpx
import respx
from helius import HeliusClient

@respx.mock
def test_get_balance():
    route = respx.post("https://mainnet.helius-rpc.com/").mock(
        return_value=httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"context": {"slot": 1}, "value": 42},
            },
        )
    )
    with HeliusClient(api_key="test") as c:
        assert c.get_balance("So11...112", commitment="finalized") == 42

    sent = route.calls.last.request
    assert sent.url.params["api-key"] == "test"
    body = json.loads(sent.content)
    assert body["method"] == "getBalance"
    assert body["params"] == ["So11...112", {"commitment": "finalized"}]
```

For methods with branching logic (e.g. `get_block_production`, `get_token_accounts_by_owner`'s `mint` vs `program_id` validation, `get_account_info`'s `data_slice` pairing), add tests for each branch — including the `ValueError`s on invalid input combinations.

## Conventions

- Construct `HeliusClient` in tests with an explicit `api_key="test"` (or similar). Never rely on a real `.env` file.
- Use the context-manager form (`with HeliusClient(...) as c:`) in tests so the `httpx.Client` is closed cleanly.
- Group tests in `tests/unit/test_client.py` by method, but a single file is fine until it grows unwieldy.
- Test names should describe the behavior, not the implementation: `test_get_balance_includes_commitment_in_config`, not `test_get_balance_calls_set`.
- When adding a new client method, the PR must include: (a) a `respx` test asserting the request payload, and (b) a fixture-based model test if the method introduces or uses a model. This is enforced in `CONTRIBUTING.md`.

## Running

```bash
pytest
```

All tests must pass and there must be no real network traffic. If a test fails because it tried to hit the network, that's a bug in the test — add the missing `@respx.mock` or `respx` route.
