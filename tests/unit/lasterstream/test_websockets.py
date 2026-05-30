"""Unit tests for `helius.laserstream.websockets`.

Coverage:
- Each notification model (`Notification` subclasses).
- `WebSocketClient` construction, `close`, context-manager protocol.
- Every `*_subscribe` and `*_unsubscribe` method (request payload + return value).
- `_send`, `_recv`, `_unsubscribe` plumbing.
- `receive()` for every notification type and `listen()` generator.

The websocket transport is faked with `FakeWebSocket`; no real network traffic.
Mocked response bodies mirror the upstream Helius docs example payloads.
"""

import json

import pytest

from helius.laserstream import websockets as ws_module
from helius.laserstream.websockets import (
    AccountNotification,
    BlockNotification,
    LogsNotification,
    Notification,
    ProgramNotification,
    RootNotification,
    SignatureNotification,
    SlotNotification,
    SlotsUpdatesNotification,
    TransactionNotification,
    VoteNotification,
    WebSocketClient,
)


# ---------------------------------------------------------------------------
# Fake websocket + fixtures
# ---------------------------------------------------------------------------


class FakeWebSocket:
    """Minimal stand-in for `websockets.sync.client.ClientConnection`."""

    def __init__(self):
        self.sent: list[str] = []
        self.outgoing: list[str] = []
        self.closed = False
        self.uri: str | None = None
        self.proxy: str | None = None

    def send(self, payload: str) -> None:
        self.sent.append(payload)

    def recv(self) -> str:
        if not self.outgoing:
            raise AssertionError("FakeWebSocket.recv() called with no queued response")
        return self.outgoing.pop(0)

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_ws(monkeypatch):
    """Patch `connect` so `WebSocketClient.__init__` returns a FakeWebSocket."""
    fake = FakeWebSocket()

    def fake_connect(uri, proxy=None):
        fake.uri = uri
        fake.proxy = proxy
        return fake

    monkeypatch.setattr(ws_module, "connect", fake_connect)
    # Make sure environment-based API-key lookups don't leak into tests that
    # specifically assert the "no API key" failure mode.
    monkeypatch.delenv("HELIUS_API_KEY", raising=False)
    return fake


@pytest.fixture
def client(fake_ws):
    return WebSocketClient(api_key="test")


def queue(fake_ws: FakeWebSocket, *responses) -> None:
    for r in responses:
        fake_ws.outgoing.append(json.dumps(r))


def last_sent(fake_ws: FakeWebSocket) -> dict:
    return json.loads(fake_ws.sent[-1])


def sub_response(sub_id: int = 1, id_: int = 1) -> dict:
    return {"jsonrpc": "2.0", "result": sub_id, "id": id_}


# ---------------------------------------------------------------------------
# Notification models
# ---------------------------------------------------------------------------


def test_transaction_notification_validates_upstream_value():
    notification = TransactionNotification.model_validate(
        {
            "transaction": {
                "transaction": ["...", "base64"],
                "meta": {"err": None, "fee": 5000},
            },
            "signature": "5moMXe6VW7L7aQZskcAkKGQ1y19qqUT1teQKB",
            "slot": 224341380,
        }
    )
    assert notification.signature.startswith("5moMXe")
    assert notification.slot == 224341380
    assert notification.transaction["meta"]["fee"] == 5000


def test_account_notification_validates_rent_epoch_alias():
    account = AccountNotification.model_validate(
        {
            "lamports": 33594,
            "owner": "11111111111111111111111111111111",
            "data": ["...", "base58"],
            "executable": False,
            "rentEpoch": 635,
            "space": 80,
        }
    )
    assert account.lamports == 33594
    assert account.rent_epoch == 635
    assert account.space == 80
    assert account.data == ["...", "base58"]


def test_account_notification_space_is_optional():
    account = AccountNotification.model_validate(
        {
            "lamports": 1,
            "owner": "11111111111111111111111111111111",
            "data": ["", "base64"],
            "executable": False,
            "rentEpoch": 18_446_744_073_709_551_615,
        }
    )
    assert account.space is None


def test_block_notification_validates_full_block_shape():
    notification = BlockNotification.model_validate(
        {
            "slot": 112301554,
            "err": None,
            "block": {
                "blockhash": "6ojMHjctdqfB55JDpEpqfHnP96fiaHEcvzEQ2NNcxzHP",
                "previousBlockhash": "GJp125YAN4ufCSUvZJVdCyWQJ7RPWMmwxoyUQySydZA",
                "parentSlot": 112301553,
                "transactions": [],
                "blockTime": 1639926816,
                "blockHeight": 101210751,
            },
        }
    )
    assert notification.slot == 112301554
    assert notification.err is None
    assert notification.block["blockhash"].startswith("6ojMHj")


def test_block_notification_allows_null_block_and_err():
    notification = BlockNotification.model_validate(
        {"slot": 1, "err": {"InstructionError": [0, "Custom"]}, "block": None}
    )
    assert notification.block is None
    assert notification.err == {"InstructionError": [0, "Custom"]}


def test_logs_notification_validates_upstream_value():
    notification = LogsNotification.model_validate(
        {
            "signature": "5h6xBEauJ3PK6SWCZ1PGjBvj8vDdWG3KpwATGy1ARAXFSDwt8GFXM7W5Ncn16wmqokgpiKRLuS83KUxyZyv2sUYv",
            "err": {"InstructionError": [0, "Custom"]},
            "logs": ["Program 1111 invoke [1]", "Program 1111 success"],
        }
    )
    assert notification.signature.startswith("5h6xBE")
    assert notification.err == {"InstructionError": [0, "Custom"]}
    assert notification.logs == ["Program 1111 invoke [1]", "Program 1111 success"]


def test_program_notification_validates_nested_account():
    notification = ProgramNotification.model_validate(
        {
            "pubkey": "H4vnBqifaSACnKa7acsxstsY1iV1bvJNxsCY7enrd1hq",
            "account": {
                "lamports": 33594,
                "owner": "11111111111111111111111111111111",
                "data": ["...", "base58"],
                "executable": False,
                "rentEpoch": 636,
                "space": 80,
            },
        }
    )
    assert notification.pubkey == "H4vnBqifaSACnKa7acsxstsY1iV1bvJNxsCY7enrd1hq"
    assert isinstance(notification.account, AccountNotification)
    assert notification.account.rent_epoch == 636


def test_root_notification_wraps_scalar():
    notification = RootNotification.model_validate(42)
    assert notification.root == 42


def test_root_notification_accepts_dict_form():
    notification = RootNotification.model_validate({"root": 7})
    assert notification.root == 7


def test_signature_notification_wraps_processed_value():
    notification = SignatureNotification.model_validate({"err": None})
    assert notification.value == {"err": None}


def test_slot_notification_validates_fields():
    notification = SlotNotification.model_validate({"parent": 75, "root": 44, "slot": 76})
    assert notification.parent == 75
    assert notification.root == 44
    assert notification.slot == 76


def test_slots_updates_notification_validates_type_literal():
    notification = SlotsUpdatesNotification.model_validate(
        {
            "parent": 75,
            "slot": 76,
            "timestamp": 1625081266243,
            "type": "optimisticConfirmation",
        }
    )
    assert notification.type == "optimisticConfirmation"
    assert notification.parent == 75
    assert notification.err is None
    assert notification.stats is None


def test_slots_updates_notification_rejects_unknown_type():
    with pytest.raises(Exception):
        SlotsUpdatesNotification.model_validate(
            {"slot": 1, "timestamp": 0, "type": "not-a-type"}
        )


def test_vote_notification_validates_aliases():
    notification = VoteNotification.model_validate(
        {
            "hash": "8Rshv2oMkPu5E4opXTRyuyBeZBqQ4S477VG26wUTFxUM",
            "slots": [1, 2],
            "timestamp": None,
            "signature": "sig",
            "votePubkey": "Vote111",
        }
    )
    assert notification.hash.startswith("8Rshv2")
    assert notification.slots == [1, 2]
    assert notification.timestamp is None
    assert notification.vote_pubkey == "Vote111"


# ---------------------------------------------------------------------------
# WebSocketClient construction
# ---------------------------------------------------------------------------


def test_init_requires_api_key(monkeypatch):
    monkeypatch.delenv("HELIUS_API_KEY", raising=False)
    monkeypatch.setattr(ws_module, "dotenv_values", lambda: {})
    monkeypatch.setattr(ws_module, "connect", lambda *a, **k: FakeWebSocket())
    with pytest.raises(ValueError, match="No API key"):
        WebSocketClient(api_key=None)


def test_init_picks_up_api_key_from_env(monkeypatch):
    fake = FakeWebSocket()
    monkeypatch.setenv("HELIUS_API_KEY", "from-env")
    monkeypatch.setattr(ws_module, "dotenv_values", lambda: {})

    def fake_connect(uri, proxy=None):
        fake.uri = uri
        return fake

    monkeypatch.setattr(ws_module, "connect", fake_connect)
    client = WebSocketClient()
    assert "api-key=from-env" in fake.uri
    assert client._websocket is fake


def test_init_builds_uri_with_api_key_and_passes_proxy(monkeypatch):
    fake = FakeWebSocket()
    captured = {}

    def fake_connect(uri, proxy=None):
        captured["uri"] = uri
        captured["proxy"] = proxy
        return fake

    monkeypatch.setattr(ws_module, "connect", fake_connect)
    WebSocketClient(api_key="test", proxy="http://proxy:8080")
    assert "api-key=test" in captured["uri"]
    assert captured["uri"].startswith("wss://mainnet.helius-rpc.com")
    assert captured["proxy"] == "http://proxy:8080"


def test_init_uses_custom_base_url(monkeypatch):
    fake = FakeWebSocket()
    captured = {}

    def fake_connect(uri, proxy=None):
        captured["uri"] = uri
        return fake

    monkeypatch.setattr(ws_module, "connect", fake_connect)
    WebSocketClient(api_key="test", base_url="wss://devnet.helius-rpc.com")
    assert captured["uri"].startswith("wss://devnet.helius-rpc.com")


def test_close_delegates_to_websocket(client, fake_ws):
    client.close()
    assert fake_ws.closed is True


def test_enter_returns_self(client):
    assert client.__enter__() is client


def test_exit_closes_websocket(client, fake_ws):
    # Standard CM protocol passes exc_type/value/tb. The current __exit__ does
    # not accept them, which is a bug in the source.
    client.__exit__(None, None, None)
    assert fake_ws.closed is True


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def test_send_round_trips_json(client, fake_ws):
    queue(fake_ws, {"jsonrpc": "2.0", "result": 99, "id": 1})
    response = client._send({"method": "ping"})
    assert response == {"jsonrpc": "2.0", "result": 99, "id": 1}
    assert json.loads(fake_ws.sent[-1]) == {"method": "ping"}


def test_recv_parses_json(client, fake_ws):
    queue(fake_ws, {"foo": "bar"})
    assert client._recv() == {"foo": "bar"}


# ---------------------------------------------------------------------------
# Subscribe methods
# ---------------------------------------------------------------------------


def test_transaction_subscribe_full_payload(client, fake_ws):
    queue(fake_ws, sub_response(4743323479349712))
    sub_id = client.transaction_subscribe(
        vote=False,
        failed=False,
        account_include=["675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"],
        commitment="processed",
        encoding="jsonParsed",
        transaction_details="full",
        show_rewards=True,
        max_supported_transaction_version=0,
    )
    assert sub_id == 4743323479349712
    body = last_sent(fake_ws)
    assert body["method"] == "transactionSubscribe"
    assert body["params"] == [
        {
            "vote": False,
            "failed": False,
            "accountInclude": ["675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"],
        },
        {
            "commitment": "processed",
            "encoding": "jsonParsed",
            "transactionDetails": "full",
            "showRewards": True,
            "maxSupportedTransactionVersion": 0,
        },
    ]


def test_transaction_subscribe_omits_empty_filter(client, fake_ws):
    queue(fake_ws, sub_response(1))
    client.transaction_subscribe(commitment="confirmed")
    body = last_sent(fake_ws)
    assert body["method"] == "transactionSubscribe"
    assert body["params"] == [{"commitment": "confirmed"}]


def test_transaction_subscribe_requires_max_supported_version_for_full(client):
    with pytest.raises(ValueError, match="max_supported_transaction_version"):
        client.transaction_subscribe(transaction_details="full")


def test_transaction_subscribe_requires_max_supported_version_for_accounts(client):
    with pytest.raises(ValueError, match="max_supported_transaction_version"):
        client.transaction_subscribe(transaction_details="accounts")


def test_account_subscribe(client, fake_ws):
    queue(fake_ws, sub_response(23784))
    sub_id = client.account_subscribe(
        pubkey="CM78CPUeXjn8o3yroDHxUtKsZZgoy4GPkPPXfouKNH12",
        encoding="jsonParsed",
        commitment="finalized",
    )
    assert sub_id == 23784
    body = last_sent(fake_ws)
    assert body["method"] == "accountSubscribe"
    assert body["params"] == [
        "CM78CPUeXjn8o3yroDHxUtKsZZgoy4GPkPPXfouKNH12",
        {"commitment": "finalized", "encoding": "jsonParsed"},
    ]


def test_account_subscribe_minimal(client, fake_ws):
    queue(fake_ws, sub_response(1))
    client.account_subscribe(pubkey="Acct")
    body = last_sent(fake_ws)
    assert body["params"] == ["Acct"]


def test_block_subscribe_with_mentions_filter(client, fake_ws):
    queue(fake_ws, sub_response(14))
    sub_id = client.block_subscribe(
        filter={"mentionsAccountOrProgram": "LieKvPRE8XeX3Y2xVNHjKlpAScD12lYySBVQ4HqoJ5op"},
        commitment="confirmed",
        encoding="base64",
        transaction_details="full",
        show_rewards=True,
        max_supported_transaction_version=0,
    )
    assert sub_id == 14
    body = last_sent(fake_ws)
    assert body["method"] == "blockSubscribe"
    assert body["params"] == [
        {"mentionsAccountOrProgram": "LieKvPRE8XeX3Y2xVNHjKlpAScD12lYySBVQ4HqoJ5op"},
        {
            "commitment": "confirmed",
            "encoding": "base64",
            "transactionDetails": "full",
            "maxSupportedTransactionVersion": 0,
            "showRewards": True,
        },
    ]


def test_block_subscribe_filter_all(client, fake_ws):
    queue(fake_ws, sub_response(1))
    client.block_subscribe(filter="all")
    body = last_sent(fake_ws)
    assert body["params"] == ["all"]


def test_logs_subscribe_with_mentions_filter(client, fake_ws):
    queue(fake_ws, sub_response(24040))
    sub_id = client.logs_subscribe(
        filter={"mentions": ["11111111111111111111111111111111"]},
        commitment="finalized",
    )
    assert sub_id == 24040
    body = last_sent(fake_ws)
    assert body["method"] == "logsSubscribe"
    assert body["params"] == [
        {"mentions": ["11111111111111111111111111111111"]},
        {"commitment": "finalized"},
    ]


def test_logs_subscribe_sends_request_once(client, fake_ws):
    # `logs_subscribe` must issue exactly one JSON-RPC subscribe call. The
    # current implementation calls `_send` twice.
    queue(fake_ws, sub_response(1))
    client.logs_subscribe(filter="all")
    assert len(fake_ws.sent) == 1


def test_logs_subscribe_filter_all_with_votes(client, fake_ws):
    queue(fake_ws, sub_response(1))
    client.logs_subscribe(filter="allWithVotes")
    body = last_sent(fake_ws)
    assert body["params"] == ["allWithVotes"]


def test_program_subscribe_with_filters(client, fake_ws):
    queue(fake_ws, sub_response(24040))
    sub_id = client.program_subscribe(
        program_id="11111111111111111111111111111111",
        encoding="base64",
        filters=[{"dataSize": 80}],
    )
    assert sub_id == 24040
    body = last_sent(fake_ws)
    assert body["method"] == "programSubscribe"
    assert body["params"] == [
        "11111111111111111111111111111111",
        {"encoding": "base64", "filters": [{"dataSize": 80}]},
    ]


def test_program_subscribe_minimal(client, fake_ws):
    queue(fake_ws, sub_response(1))
    client.program_subscribe(program_id="Program")
    body = last_sent(fake_ws)
    assert body["params"] == ["Program"]


def test_root_subscribe(client, fake_ws):
    queue(fake_ws, sub_response(0))
    sub_id = client.root_subscribe()
    assert sub_id == 0
    body = last_sent(fake_ws)
    assert body["method"] == "rootSubscribe"
    assert body.get("params") is None


def test_signature_subscribe(client, fake_ws):
    queue(fake_ws, sub_response(0))
    sub_id = client.signature_subscribe(
        signature="2EBVM6cB8vAAD93Ktr6Vd8p67XPbQzCJX47MpReuiCXJAtcjaxpvWpcg9Ege1Nr5Tk3a2GFrByT7WPBjdsTycY9b",
        commitment="finalized",
        enable_received_notification=False,
    )
    assert sub_id == 0
    body = last_sent(fake_ws)
    assert body["method"] == "signatureSubscribe"
    assert body["params"] == [
        "2EBVM6cB8vAAD93Ktr6Vd8p67XPbQzCJX47MpReuiCXJAtcjaxpvWpcg9Ege1Nr5Tk3a2GFrByT7WPBjdsTycY9b",
        {"commitment": "finalized", "enableReceivedNotification": False},
    ]


def test_signature_subscribe_minimal(client, fake_ws):
    queue(fake_ws, sub_response(1))
    client.signature_subscribe(signature="sig")
    body = last_sent(fake_ws)
    assert body["params"] == ["sig"]


def test_slot_subscribe(client, fake_ws):
    queue(fake_ws, sub_response(0))
    sub_id = client.slot_subscribe()
    assert sub_id == 0
    body = last_sent(fake_ws)
    assert body["method"] == "slotSubscribe"
    assert body.get("params") is None


def test_slots_updates_subscribe(client, fake_ws):
    queue(fake_ws, sub_response(0))
    sub_id = client.slots_updates_subscribe()
    assert sub_id == 0
    body = last_sent(fake_ws)
    assert body["method"] == "slotsUpdatesSubscribe"
    assert body.get("params") is None


def test_vote_subscribe(client, fake_ws):
    queue(fake_ws, sub_response(0))
    sub_id = client.vote_subscribe()
    assert sub_id == 0
    body = last_sent(fake_ws)
    assert body["method"] == "voteSubscribe"
    assert body.get("params") is None


# ---------------------------------------------------------------------------
# Unsubscribe methods
# ---------------------------------------------------------------------------


UNSUBSCRIBE_CASES = [
    ("transaction_unsubscribe", "transactionUnsubscribe"),
    ("account_unsubscribe", "accountUnsubscribe"),
    ("block_unsubscribe", "blockUnsubscribe"),
    ("logs_unsubscribe", "logsUnsubscribe"),
    ("program_unsubscribe", "programUnsubscribe"),
    ("root_unsubscribe", "rootUnsubscribe"),
    ("signature_unsubscribe", "signatureUnsubscribe"),
    ("slot_unsubscribe", "slotUnsubscribe"),
    ("slots_updates_unsubscribe", "slotsUpdatesUnsubscribe"),
    ("vote_unsubscribe", "voteUnsubscribe"),
]


@pytest.mark.parametrize("method_name,upstream_method", UNSUBSCRIBE_CASES)
def test_unsubscribe_sends_correct_method_and_subscription(
    client, fake_ws, method_name, upstream_method
):
    queue(fake_ws, {"jsonrpc": "2.0", "result": True, "id": 1})
    method = getattr(client, method_name)
    assert method(4743323479349712) is True
    body = last_sent(fake_ws)
    assert body["method"] == upstream_method
    assert body["params"] == [4743323479349712]


# ---------------------------------------------------------------------------
# receive() — per-notification-type integration tests
# ---------------------------------------------------------------------------


def notification(method: str, result, subscription: int) -> dict:
    """Build the upstream Helius WebSocket notification envelope."""
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": {"result": result, "subscription": subscription},
    }


def test_receive_transaction_notification(client, fake_ws):
    queue(
        fake_ws,
        notification(
            "transactionNotification",
            {
                "transaction": {"transaction": ["...", "base64"], "meta": {"fee": 5000}},
                "signature": "5moMXe6VW7L7aQZskcAkKGQ1y19qqUT1teQKB",
                "slot": 224341380,
            },
            4743323479349712,
        ),
    )
    context, note, subscription = client.receive()
    assert context is None  # transactionNotification result is unwrapped
    assert isinstance(note, TransactionNotification)
    assert note.signature.startswith("5moMXe")
    assert note.slot == 224341380
    assert subscription == 4743323479349712


def test_receive_account_notification_unwraps_context_and_value(client, fake_ws):
    queue(
        fake_ws,
        notification(
            "accountNotification",
            {
                "context": {"slot": 5199307},
                "value": {
                    "data": ["payload", "base58"],
                    "executable": False,
                    "lamports": 33594,
                    "owner": "11111111111111111111111111111111",
                    "rentEpoch": 635,
                    "space": 80,
                },
            },
            23784,
        ),
    )
    context, note, subscription = client.receive()
    assert context == {"slot": 5199307}
    assert isinstance(note, AccountNotification)
    assert note.rent_epoch == 635
    assert subscription == 23784


def test_receive_block_notification(client, fake_ws):
    queue(
        fake_ws,
        notification(
            "blockNotification",
            {
                "context": {"slot": 112301554},
                "value": {
                    "slot": 112301554,
                    "err": None,
                    "block": {
                        "blockhash": "6ojMHj",
                        "previousBlockhash": "GJp125",
                        "parentSlot": 112301553,
                        "transactions": [],
                        "blockTime": 1639926816,
                        "blockHeight": 101210751,
                    },
                },
            },
            14,
        ),
    )
    context, note, subscription = client.receive()
    assert context == {"slot": 112301554}
    assert isinstance(note, BlockNotification)
    assert note.slot == 112301554
    assert subscription == 14


def test_receive_logs_notification(client, fake_ws):
    queue(
        fake_ws,
        notification(
            "logsNotification",
            {
                "context": {"slot": 5208469},
                "value": {
                    "signature": "5h6xBE",
                    "err": None,
                    "logs": ["Program 1111 success"],
                },
            },
            24040,
        ),
    )
    context, note, subscription = client.receive()
    assert context == {"slot": 5208469}
    assert isinstance(note, LogsNotification)
    assert note.err is None
    assert note.logs == ["Program 1111 success"]
    assert subscription == 24040


def test_receive_program_notification(client, fake_ws):
    queue(
        fake_ws,
        notification(
            "programNotification",
            {
                "context": {"slot": 5208469},
                "value": {
                    "pubkey": "H4vnBqifaSACnKa7acsxstsY1iV1bvJNxsCY7enrd1hq",
                    "account": {
                        "data": ["payload", "base58"],
                        "executable": False,
                        "lamports": 33594,
                        "owner": "11111111111111111111111111111111",
                        "rentEpoch": 636,
                        "space": 80,
                    },
                },
            },
            24040,
        ),
    )
    context, note, subscription = client.receive()
    assert context == {"slot": 5208469}
    assert isinstance(note, ProgramNotification)
    assert note.pubkey.startswith("H4vnBq")
    assert note.account.rent_epoch == 636


def test_receive_root_notification(client, fake_ws):
    queue(fake_ws, notification("rootNotification", 42, 0))
    context, note, subscription = client.receive()
    assert context is None
    assert isinstance(note, RootNotification)
    assert note.root == 42
    assert subscription == 0


def test_receive_signature_notification_processed(client, fake_ws):
    queue(
        fake_ws,
        notification(
            "signatureNotification",
            {"context": {"slot": 5207624}, "value": {"err": None}},
            24006,
        ),
    )
    context, note, subscription = client.receive()
    assert context == {"slot": 5207624}
    assert isinstance(note, SignatureNotification)
    assert note.value == {"err": None}
    assert subscription == 24006


def test_receive_slot_notification(client, fake_ws):
    queue(
        fake_ws,
        notification(
            "slotNotification", {"parent": 75, "root": 44, "slot": 76}, 0
        ),
    )
    context, note, subscription = client.receive()
    assert context is None
    assert isinstance(note, SlotNotification)
    assert note.slot == 76


def test_receive_slots_updates_notification(client, fake_ws):
    queue(
        fake_ws,
        notification(
            "slotsUpdatesNotification",
            {
                "parent": 75,
                "slot": 76,
                "timestamp": 1625081266243,
                "type": "optimisticConfirmation",
            },
            0,
        ),
    )
    context, note, subscription = client.receive()
    assert context is None
    assert isinstance(note, SlotsUpdatesNotification)
    assert note.type == "optimisticConfirmation"


def test_receive_vote_notification(client, fake_ws):
    queue(
        fake_ws,
        notification(
            "voteNotification",
            {
                "hash": "8Rshv2oMkPu5E4opXTRyuyBeZBqQ4S477VG26wUTFxUM",
                "slots": [1, 2],
                "timestamp": None,
                "signature": "sig",
                "votePubkey": "Vote111",
            },
            0,
        ),
    )
    context, note, subscription = client.receive()
    assert context is None
    assert isinstance(note, VoteNotification)
    assert note.vote_pubkey == "Vote111"


# ---------------------------------------------------------------------------
# listen()
# ---------------------------------------------------------------------------


def test_listen_yields_each_notification(client, fake_ws):
    queue(
        fake_ws,
        notification("rootNotification", 1, 0),
        notification("rootNotification", 2, 0),
    )
    gen = client.listen()
    first = next(gen)
    second = next(gen)
    assert first[1].root == 1
    assert second[1].root == 2


# ---------------------------------------------------------------------------
# Notification base class sanity
# ---------------------------------------------------------------------------


def test_notification_subclasses_share_alias_generator():
    # Every concrete notification model derives from `Notification` so the
    # camelCase alias generator (`to_camel`) applies to all of them.
    for cls in [
        TransactionNotification,
        AccountNotification,
        BlockNotification,
        LogsNotification,
        ProgramNotification,
        RootNotification,
        SignatureNotification,
        SlotNotification,
        SlotsUpdatesNotification,
        VoteNotification,
    ]:
        assert issubclass(cls, Notification)
