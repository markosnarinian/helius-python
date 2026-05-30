from helius.solana_rpc import JsonRpcRequest


def test_add_skips_none_unless_allowed():
    assert JsonRpcRequest(method="test").add(None).add("x").build()["params"] == ["x"]
    assert JsonRpcRequest(method="test").add(None, can_be_none=True).build()["params"] == [
        None
    ]


def test_set_skips_none_unless_allowed():
    assert JsonRpcRequest(method="test").set("commitment", None).build()["params"] is None
    assert JsonRpcRequest(method="test").set("commitment", None, can_be_none=True).build()[
        "params"
    ] == [{"commitment": None}]


def test_positional_params_precede_config_dict():
    payload = (
        JsonRpcRequest(method="test")
        .add("account")
        .add(5)
        .set("commitment", "finalized")
        .build()
    )

    assert payload["params"] == ["account", 5, {"commitment": "finalized"}]


def test_config_dict_only_appended_when_non_empty():
    assert JsonRpcRequest(method="test").add("account").build()["params"] == ["account"]
    assert JsonRpcRequest(method="test").set("commitment", "finalized").build()[
        "params"
    ] == [{"commitment": "finalized"}]


def test_params_omitted_when_no_positional_or_config_values():
    payload = JsonRpcRequest(method="test").build()

    assert payload["params"] is None


def test_method_id_and_jsonrpc_are_included():
    payload = JsonRpcRequest(method="test", id="abc", jsonrpc="2.0").build()

    assert payload["method"] == "test"
    assert payload["id"] == "abc"
    assert payload["jsonrpc"] == "2.0"
