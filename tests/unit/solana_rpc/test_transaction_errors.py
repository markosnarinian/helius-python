"""Offline transaction-error regression tests using documented response shapes.

The fixture values are synthetic; no real transaction or signature is verified.
Response schemas:
https://solana.com/docs/rpc/http/getsignaturestatuses
https://solana.com/docs/rpc/http/getsignaturesforaddress
https://solana.com/docs/rpc/http/gettransaction
https://www.helius.dev/docs/api-reference/rpc/http/gettransactionsforaddress
Error values: https://solana.com/docs/rpc/json-structures#transaction-errors
"""

import json
from pathlib import Path

import httpx
import pytest
import respx
from pydantic import ValidationError

from helius.rpc import SolanaRpcClient
from helius.rpc.models import (
    SignatureStatus,
    TransactionMetadata,
    TransactionSignature,
    TransactionSignaturesDetail,
)

SIGNATURE = "5h6xBEauJ3PK6SWCZ1PGjBvj8vDdWG3KpwATGy1ARAXFSDwt8GFXM7W5Ncn16wmqokgpiKRLuS83KUxyZyv2sUYv"
MISSING_SIGNATURE = "1" * 64
ADDRESS = "Vote111111111111111111111111111111111111111"
CASES = [
    pytest.param(
        "getSignatureStatuses", SignatureStatus, ("result", "value", 0), id="status"
    ),
    pytest.param(
        "getSignaturesForAddress", TransactionSignature, ("result", 0), id="signature"
    ),
    pytest.param(
        "getTransaction", TransactionMetadata, ("result", "meta"), id="metadata"
    ),
    pytest.param(
        "getTransactionsForAddress",
        TransactionSignaturesDetail,
        ("result", "data", 0),
        id="address-signatures",
    ),
]
ERRORS = [
    pytest.param(None, id="success"),
    pytest.param("BlockhashNotFound", id="simple-error"),
    pytest.param({"InstructionError": [0, {"Custom": 1}]}, id="instruction-error"),
]


@pytest.fixture
def responses():
    path = Path(__file__).resolve().parents[2] / "fixtures" / "transaction_errors.json"
    return json.loads(path.read_text(encoding="utf-8"))


def error_response(responses, method, path, error):
    response = responses[method]
    payload = response
    for key in path:
        payload = payload[key]
    payload["err"] = error
    # Keep the deprecated status field consistent with the chosen error.
    if "status" in payload:
        payload["status"] = {"Ok": None} if error is None else {"Err": error}
    return response, payload


@pytest.mark.parametrize("method, model, path", CASES)
@pytest.mark.parametrize("error", ERRORS)
def test_models_preserve_documented_transaction_errors(
    responses, method, model, path, error
):
    _, payload = error_response(responses, method, path, error)
    parsed = model.model_validate(payload)
    assert parsed.err == error


@pytest.mark.parametrize("method, model, path", CASES)
@pytest.mark.parametrize("error", ERRORS)
@respx.mock
def test_rpc_methods_preserve_transaction_errors(responses, method, model, path, error):
    response, _ = error_response(responses, method, path, error)
    route = respx.post("https://rpc.example.invalid/").mock(
        return_value=httpx.Response(200, json=response)
    )
    with SolanaRpcClient(
        base_url="https://rpc.example.invalid", api_key="test"
    ) as client:
        if method == "getSignatureStatuses":
            context, values = client.get_signature_statuses(
                signatures=[SIGNATURE, MISSING_SIGNATURE]
            )
            assert context == {"apiVersion": "3.1.8", "slot": 82}
            assert values[1] is None
            actual = values[0]
            params = [[SIGNATURE, MISSING_SIGNATURE]]
        elif method == "getSignaturesForAddress":
            actual = client.get_signatures_for_address(address=ADDRESS, limit=1)[0]
            params = [ADDRESS, {"limit": 1}]
        elif method == "getTransaction":
            actual = client.get_transaction(transaction_signature=SIGNATURE).meta
            params = [SIGNATURE]
        else:
            values, pagination = client.get_transactions_for_address(
                address=ADDRESS, transaction_details="signatures", limit=1
            )
            assert pagination == "1055:5"
            actual = values[0]
            params = [ADDRESS, {"transactionDetails": "signatures", "limit": 1}]
    assert isinstance(actual, model)
    assert actual.err == error
    request = route.calls.last.request
    assert request.url.params["api-key"] == "test"
    body = json.loads(request.content)
    assert body["method"] == method
    assert body["params"] == params


@pytest.mark.parametrize("method, model, path", CASES)
@pytest.mark.parametrize("error", [False, 7, []], ids=["boolean", "number", "array"])
def test_models_reject_invalid_error_types(responses, method, model, path, error):
    _, payload = error_response(responses, method, path, error)
    with pytest.raises(ValidationError) as exc:
        model.model_validate(payload)
    assert all(error["loc"][0] == "err" for error in exc.value.errors())


@pytest.mark.parametrize("method, model, path", CASES)
def test_error_field_remains_required(responses, method, model, path):
    _, payload = error_response(responses, method, path, None)
    del payload["err"]
    with pytest.raises(ValidationError) as exc:
        model.model_validate(payload)
    assert exc.value.errors()[0]["loc"] == ("err",)
    assert exc.value.errors()[0]["type"] == "missing"
