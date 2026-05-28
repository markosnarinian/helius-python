
## Conventions

- Use **double-quoted triple strings** (`"""..."""`).
- Wrap docstring lines at 88 columns.
- Refer to parameters in backticks: `` `commitment` ``, `` `min_context_slot` ``.
- Refer to other client methods with their snake_case name in backticks: `` `get_balance` ``.
- Do NOT include the upstream JSON-RPC method name in the summary — that's already in the See Also URLs.
- Do NOT copy-paste large chunks from the Helius docs. Summarize and link.
- Examples (`Example:` section) are encouraged for methods with non-trivial argument combinations (e.g. `get_block_production`, `get_token_accounts_by_owner`), optional for everything else.

## Implementation conventions

- **If the RPC returns an `RpcResponse` wrapper (`{context, value}`), the Python method MUST return `(context, value)`** — never silently drop `context`. For methods whose `value` is itself a small composite, flatten the tuple (e.g. `get_latest_blockhash` returns `tuple[dict, str, int]`, not `tuple[dict, tuple[str, int]]`). Check the upstream Helius API reference page to see whether the response is wrapped.
- Type-annotate the return shape exactly. `tuple[dict, X]`, not bare `tuple`, and not the unwrapped `X`. Mismatches between annotation and runtime shape break the docstring contract.
- `value` can be `null` for some wrapped methods (e.g. `getAccountInfo` when the account doesn't exist, `getMultipleAccounts` entries for closed accounts). Reflect that in the return type with `| None` and handle it before calling `Model.model_validate(...)`.

## Checklist for adding a new client method

1. Read the docs for the specific RPC method. For example, for the get_supply function (getSupply RPC method) you should read https://www.helius.dev/docs/rpc/guides/getsupply and https://www.helius.dev/docs/api-reference/rpc/http/getsupply.
2. Implement the method, following the **Implementation conventions** above — in particular, return `(context, value)` if the upstream response is wrapped.
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
    test_solana_rpc.py       # one test (or small group) per client method
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

**Fixture keys must come from the Helius docs, not from the model.** If you write the fixture by reading the Python field names and camelCasing them, the test only proves the model agrees with itself — typos like `loaderScheduleSlotOffset` (should be `leaderScheduleSlotOffset`) will pass. Always copy the JSON keys verbatim from the upstream Helius example response.

### 3. Client methods — `respx`-mocked tests

For each method on `SolanaRpcClient`, write at least one test that asserts **both** sides of the wire:

- **Outgoing request:** the JSON body sent to Helius matches the JSON-RPC payload you expect — correct `method`, correct positional `params`, correct config object with snake → camel mapping, and optional arguments omitted when `None`.
- **Return value:** the method correctly parses a canned response into the documented return shape (model, tuple, primitive, etc.).

Also assert that the `api-key` query parameter is present on the request URL.

**The mocked response body must mirror the real upstream shape.** Copy the `result` payload from the Helius docs' example response — do not invent a flatter shape by reading what the Python method indexes into. In particular, if the upstream method returns an `RpcResponse` wrapper (`{"context": {...}, "value": ...}`), the mock must include that wrapper, even if the client method only returns `value`. Otherwise a bug that reads `result["foo"]` instead of `result["value"]["foo"]` will pass the test and fail in production.

Skeleton:

```python
import json
import httpx
import respx
from helius.solana_rpc import SolanaRpcClient

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
    with SolanaRpcClient(api_key="test") as c:
        assert c.get_balance("So11...112", commitment="finalized") == 42

    sent = route.calls.last.request
    assert sent.url.params["api-key"] == "test"
    body = json.loads(sent.content)
    assert body["method"] == "getBalance"
    assert body["params"] == ["So11...112", {"commitment": "finalized"}]
```

For methods with branching logic (e.g. `get_block_production`, `get_token_accounts_by_owner`'s `mint` vs `program_id` validation, `get_account_info`'s `data_slice` pairing), add tests for each branch — including the `ValueError`s on invalid input combinations.

## Conventions

- Construct `SolanaRpcClient` in tests with an explicit `api_key="test"` (or similar). Never rely on a real `.env` file.
- Use the context-manager form (`with SolanaRpcClient(...) as c:`) in tests so the `httpx.Client` is closed cleanly.
- Group tests in `tests/unit/test_solana_rpc.py` by method, but a single file is fine until it grows unwieldy.
- Test names should describe the behavior, not the implementation: `test_get_balance_includes_commitment_in_config`, not `test_get_balance_calls_set`.
- When adding a new client method, the PR must include: (a) a `respx` test asserting the request payload, and (b) a fixture-based model test if the method introduces or uses a model. This is enforced in `CONTRIBUTING.md`.

## Running

```bash
pytest
```

All tests must pass and there must be no real network traffic. If a test fails because it tried to hit the network, that's a bug in the test — add the missing `@respx.mock` or `respx` route.
