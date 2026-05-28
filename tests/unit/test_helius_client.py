import json

import httpx
import pytest
import respx

from helius.client import HeliusClient
from helius.models import Account

ACCOUNT_VALUE = {
    "lamports": 5_000_000_000,
    "owner": "11111111111111111111111111111111",
    "data": ["", "base64"],
    "executable": False,
    "rentEpoch": 18446744073709551615,
    "space": 0,
}

TOKEN_BALANCE_VALUE = {
    "amount": "9864",
    "decimals": 2,
    "uiAmount": 98.64,
    "uiAmountString": "98.64",
}

VOTING_ACCOUNT_VALUE = {
    "votePubkey": "3ZT31jkAGhUaw8jsy4bTknwBMP8i4Eueh52By4zXcsVw",
    "nodePubkey": "B97CCUW3AEZFGy6uUg6zUdnNYvnVq5VG8PUtb2HayTDD",
    "activatedStake": 42,
    "epochVoteAccount": True,
    "commission": 0,
    "lastVote": 147,
    "rootSlot": 42,
    "epochCredits": [[1, 64, 0], [2, 192, 64]],
}


def jsonrpc_response(result):
    return httpx.Response(
        200,
        json={"jsonrpc": "2.0", "id": 1, "result": result},
    )


def mock_rpc(result):
    return respx.post().mock(return_value=jsonrpc_response(result))


def body(route):
    return json.loads(route.calls.last.request.content)


def assert_api_key(route):
    assert route.calls.last.request.url.params["api-key"] == "test"


# ---------------------------------------------------------------------------
# get_account_info
# ---------------------------------------------------------------------------


@respx.mock
def test_get_account_info():
    route = mock_rpc({"context": {"slot": 341197053}, "value": ACCOUNT_VALUE})
    with HeliusClient(api_key="test") as client:
        context, account = client.get_account_info(
            public_key="Acct",
            encoding="base64",
            data_slice_offset=0,
            data_slice_length=8,
            min_context_slot=10,
        )
    assert context == {"slot": 341197053}
    assert account.lamports == 5_000_000_000
    assert body(route)["method"] == "getAccountInfo"
    assert body(route)["params"] == [
        "Acct",
        {
            "encoding": "base64",
            "dataSlice": {"offset": 0, "length": 8},
            "minContextSlot": 10,
        },
    ]
    assert_api_key(route)


@respx.mock
def test_get_account_info_minimal():
    route = mock_rpc({"context": {"slot": 1}, "value": ACCOUNT_VALUE})
    with HeliusClient(api_key="test") as client:
        context, account = client.get_account_info(public_key="Acct")
    assert context == {"slot": 1}
    assert account is not None
    assert body(route)["params"] == ["Acct"]
    assert_api_key(route)


@respx.mock
def test_get_account_info_null_account():
    route = mock_rpc({"context": {"slot": 1}, "value": None})
    with HeliusClient(api_key="test") as client:
        context, account = client.get_account_info(public_key="Acct")
    assert context == {"slot": 1}
    assert account is None
    assert_api_key(route)


def test_get_account_info_validates_data_slice_pair():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="Set both"):
            client.get_account_info(public_key="Acct", data_slice_offset=0)


# ---------------------------------------------------------------------------
# get_balance
# ---------------------------------------------------------------------------


@respx.mock
def test_get_balance():
    route = mock_rpc({"context": {"slot": 1}, "value": 42})
    with HeliusClient(api_key="test") as client:
        assert client.get_balance(public_key="Acct", commitment="finalized") == ({"slot": 1}, 42)
    assert body(route)["method"] == "getBalance"
    assert body(route)["params"] == ["Acct", {"commitment": "finalized"}]
    assert_api_key(route)


@respx.mock
def test_get_balance_minimal():
    route = mock_rpc({"context": {"slot": 1}, "value": 0})
    with HeliusClient(api_key="test") as client:
        context, value = client.get_balance(public_key="Acct")
    assert context == {"slot": 1}
    assert value == 0
    assert body(route)["params"] == ["Acct"]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_block
# ---------------------------------------------------------------------------


@respx.mock
def test_get_block():
    route = mock_rpc(
        {
            "blockhash": "DUCT8VSgk2BXkMhQfxKVYfikEZCQf4dZ4ioPdGdaVxMN",
            "previousBlockhash": "HA2fJgGqmQezCXJRVNZAWPbRMXCPjUyo7VjRF47JGdYs",
            "parentSlot": 429,
            "transactions": [],
            "blockTime": None,
            "blockHeight": None,
            "rewards": [],
        }
    )
    with HeliusClient(api_key="test") as client:
        block = client.get_block(slot=429, commitment="finalized", rewards=True)
    assert block.blockhash == "DUCT8VSgk2BXkMhQfxKVYfikEZCQf4dZ4ioPdGdaVxMN"
    assert block.rewards == []
    assert body(route)["method"] == "getBlock"
    assert body(route)["params"] == [429, {"commitment": "finalized", "rewards": True}]
    assert_api_key(route)


@respx.mock
def test_get_block_minimal():
    route = mock_rpc(
        {
            "blockhash": "DUCT8VSgk2BXkMhQfxKVYfikEZCQf4dZ4ioPdGdaVxMN",
            "previousBlockhash": "HA2fJgGqmQezCXJRVNZAWPbRMXCPjUyo7VjRF47JGdYs",
            "parentSlot": 429,
            "transactions": [],
            "blockTime": None,
            "blockHeight": None,
        }
    )
    with HeliusClient(api_key="test") as client:
        block = client.get_block(slot=429)
    assert block.blockhash == "DUCT8VSgk2BXkMhQfxKVYfikEZCQf4dZ4ioPdGdaVxMN"
    assert body(route)["params"] == [429]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_block_commitment
# ---------------------------------------------------------------------------


@respx.mock
def test_get_block_commitment():
    route = mock_rpc({"commitment": [0, 0, 0, 0, 0, 10, 32], "totalStake": 384962848972206900})
    with HeliusClient(api_key="test") as client:
        result = client.get_block_commitment(slot=1)
    assert result.commitment == [0, 0, 0, 0, 0, 10, 32]
    assert result.total_stake == 384962848972206900
    assert body(route)["method"] == "getBlockCommitment"
    assert body(route)["params"] == [1]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_block_height
# ---------------------------------------------------------------------------


@respx.mock
def test_get_block_height():
    route = mock_rpc(1233)
    with HeliusClient(api_key="test") as client:
        assert client.get_block_height(commitment="confirmed") == 1233
    assert body(route)["method"] == "getBlockHeight"
    assert body(route)["params"] == [{"commitment": "confirmed"}]
    assert_api_key(route)


@respx.mock
def test_get_block_height_minimal():
    route = mock_rpc(1233)
    with HeliusClient(api_key="test") as client:
        assert client.get_block_height() == 1233
    assert body(route)["method"] == "getBlockHeight"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_block_production
# ---------------------------------------------------------------------------


@respx.mock
def test_get_block_production_with_range():
    route = mock_rpc(
        {
            "context": {"slot": 9887},
            "value": {
                "byIdentity": {
                    "85iYT5RuzRTDgjyRa3cP8SYhM2j21fj7NhfJ3peu1DPr": [9888, 9886]
                },
                "range": {"firstSlot": 1, "lastSlot": 2},
            },
        }
    )
    with HeliusClient(api_key="test") as client:
        context, value = client.get_block_production(first_slot=1, last_slot=2)
    assert context == {"slot": 9887}
    assert "byIdentity" in value
    assert value["range"] == {"firstSlot": 1, "lastSlot": 2}
    assert body(route)["method"] == "getBlockProduction"
    assert body(route)["params"] == [{"range": {"firstSlot": 1, "lastSlot": 2}}]
    assert_api_key(route)


@respx.mock
def test_get_block_production_identity_only():
    route = mock_rpc(
        {
            "context": {"slot": 9887},
            "value": {
                "byIdentity": {
                    "85iYT5RuzRTDgjyRa3cP8SYhM2j21fj7NhfJ3peu1DPr": [9888, 9886]
                },
                "range": {"firstSlot": 0, "lastSlot": 9887},
            },
        }
    )
    with HeliusClient(api_key="test") as client:
        context, value = client.get_block_production(
            identity="85iYT5RuzRTDgjyRa3cP8SYhM2j21fj7NhfJ3peu1DPr"
        )
    assert context == {"slot": 9887}
    assert body(route)["params"] == [
        {"identity": "85iYT5RuzRTDgjyRa3cP8SYhM2j21fj7NhfJ3peu1DPr"}
    ]
    assert_api_key(route)


def test_get_block_production_validates_required_range_inputs():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="At least one"):
            client.get_block_production()
        with pytest.raises(ValueError, match="first_slot"):
            client.get_block_production(identity="id", last_slot=2)


# ---------------------------------------------------------------------------
# get_blocks
# ---------------------------------------------------------------------------


@respx.mock
def test_get_blocks():
    route = mock_rpc([5, 6, 7, 8, 9, 10])
    with HeliusClient(api_key="test") as client:
        assert client.get_blocks(start_slot=5, end_slot=10, commitment="finalized") == [5, 6, 7, 8, 9, 10]
    assert body(route)["method"] == "getBlocks"
    assert body(route)["params"] == [5, 10, {"commitment": "finalized"}]
    assert_api_key(route)


@respx.mock
def test_get_blocks_no_end_slot():
    route = mock_rpc([1, 2])
    with HeliusClient(api_key="test") as client:
        assert client.get_blocks(start_slot=1, end_slot=None) == [1, 2]
    assert body(route)["params"] == [1]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_blocks_with_limit
# ---------------------------------------------------------------------------


@respx.mock
def test_get_blocks_with_limit():
    route = mock_rpc([1, 2])
    with HeliusClient(api_key="test") as client:
        assert client.get_blocks_with_limit(start_slot=1, limit=2) == [1, 2]
    assert body(route)["method"] == "getBlocksWithLimit"
    assert body(route)["params"] == [1, 2]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_block_time
# ---------------------------------------------------------------------------


@respx.mock
def test_get_block_time():
    route = mock_rpc(1574721591)
    with HeliusClient(api_key="test") as client:
        assert client.get_block_time(slot=1) == 1574721591
    assert body(route)["method"] == "getBlockTime"
    assert body(route)["params"] == [1]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_cluster_nodes
# ---------------------------------------------------------------------------


@respx.mock
def test_get_cluster_nodes():
    route = mock_rpc(
        [
            {
                "pubkey": "Node11111111111111111111111111111111111",
                "gossip": None,
                "tpu": None,
                "rpc": None,
                "version": "1.18.0",
                "featureSet": 1,
                "shredVersion": 2,
            }
        ]
    )
    with HeliusClient(api_key="test") as client:
        nodes = client.get_cluster_nodes()
    assert nodes[0].feature_set == 1
    assert nodes[0].shred_version == 2
    assert body(route)["method"] == "getClusterNodes"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_epoch_info
# ---------------------------------------------------------------------------


@respx.mock
def test_get_epoch_info():
    route = mock_rpc(
        {
            "absoluteSlot": 166598,
            "blockHeight": 166500,
            "epoch": 27,
            "slotIndex": 2790,
            "slotsInEpoch": 8192,
            "transactionCount": 22661093,
        }
    )
    with HeliusClient(api_key="test") as client:
        result = client.get_epoch_info(min_context_slot=1)
    assert result.absolute_slot == 166598
    assert result.transaction_count == 22661093
    assert body(route)["method"] == "getEpochInfo"
    assert body(route)["params"] == [{"minContextSlot": 1}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_epoch_schedule
# ---------------------------------------------------------------------------


@respx.mock
def test_get_epoch_schedule():
    route = mock_rpc(
        {
            "slotsPerEpoch": 8192,
            "leaderScheduleSlotOffset": 8192,
            "warmup": True,
            "firstNormalEpoch": 8,
            "firstNormalSlot": 8160,
        }
    )
    with HeliusClient(api_key="test") as client:
        result = client.get_epoch_schedule()
    assert result.slots_per_epoch == 8192
    assert result.leader_schedule_slot_offset == 8192
    assert result.first_normal_slot == 8160
    assert body(route)["method"] == "getEpochSchedule"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_fee_for_message
# ---------------------------------------------------------------------------


@respx.mock
def test_get_fee_for_message():
    route = mock_rpc({"context": {"slot": 5068}, "value": 5000})
    with HeliusClient(api_key="test") as client:
        assert client.get_fee_for_message(message="msg", commitment="processed") == (
            {"slot": 5068},
            5000,
        )
    assert body(route)["method"] == "getFeeForMessage"
    assert body(route)["params"] == ["msg", {"commitment": "processed"}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_first_available_block
# ---------------------------------------------------------------------------


@respx.mock
def test_get_first_available_block():
    route = mock_rpc(250000)
    with HeliusClient(api_key="test") as client:
        assert client.get_first_available_block() == 250000
    assert body(route)["method"] == "getFirstAvailableBlock"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_genesis_hash
# ---------------------------------------------------------------------------


@respx.mock
def test_get_genesis_hash():
    route = mock_rpc("GH7ome3EiwEr7tu9JuTh2dpYWBJK3z69Xm1ZE3MEE6JC")
    with HeliusClient(api_key="test") as client:
        assert client.get_genesis_hash() == "GH7ome3EiwEr7tu9JuTh2dpYWBJK3z69Xm1ZE3MEE6JC"
    assert body(route)["method"] == "getGenesisHash"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_health
# ---------------------------------------------------------------------------


@respx.mock
def test_get_health_ok():
    route = mock_rpc("ok")
    with HeliusClient(api_key="test") as client:
        assert client.get_health() is True
    assert body(route)["method"] == "getHealth"
    assert body(route).get("params") is None
    assert_api_key(route)


@respx.mock
def test_get_health_unhealthy():
    route = mock_rpc("error")
    with HeliusClient(api_key="test") as client:
        assert client.get_health() is False
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_highest_snapshot_slot
# ---------------------------------------------------------------------------


@respx.mock
def test_get_highest_snapshot_slot():
    route = mock_rpc({"full": 100, "incremental": 110})
    with HeliusClient(api_key="test") as client:
        assert client.get_highest_snapshot_slot() == {"full": 100, "incremental": 110}
    assert body(route)["method"] == "getHighestSnapshotSlot"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_identity
# ---------------------------------------------------------------------------


@respx.mock
def test_get_identity():
    route = mock_rpc({"identity": "2r1F4iWqVcb8M1DbAjQuFpebkQHY9hcVU4WuW2DJBppN"})
    with HeliusClient(api_key="test") as client:
        assert client.get_identity() == "2r1F4iWqVcb8M1DbAjQuFpebkQHY9hcVU4WuW2DJBppN"
    assert body(route)["method"] == "getIdentity"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_inflation_governor
# ---------------------------------------------------------------------------


@respx.mock
def test_get_inflation_governor():
    route = mock_rpc(
        {
            "initial": 0.15,
            "terminal": 0.015,
            "taper": 0.15,
            "foundation": 0.05,
            "foundationTerm": 7.0,
        }
    )
    with HeliusClient(api_key="test") as client:
        result = client.get_inflation_governor(commitment="finalized")
    assert result.initial == 0.15
    assert result.foundation_term == 7.0
    assert body(route)["method"] == "getInflationGovernor"
    assert body(route)["params"] == [{"commitment": "finalized"}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_inflation_rate
# ---------------------------------------------------------------------------


@respx.mock
def test_get_inflation_rate():
    # Uses real upstream key "foundation". Exposes InflationRate.foudnation typo in models.py:95.
    route = mock_rpc({"total": 0.149, "validator": 0.148, "foundation": 0.001, "epoch": 100})
    with HeliusClient(api_key="test") as client:
        result = client.get_inflation_rate()
    assert result.total == 0.149
    assert result.epoch == 100
    assert body(route)["method"] == "getInflationRate"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_inflation_reward
# ---------------------------------------------------------------------------


@respx.mock
def test_get_inflation_reward():
    route = mock_rpc(
        [
            {
                "epoch": 2,
                "effectiveSlot": 224,
                "amount": 2500,
                "postBalance": 499999442500,
                "commission": 5,
            },
            None,
        ]
    )
    with HeliusClient(api_key="test") as client:
        result = client.get_inflation_reward(
            addresses=[
                "6dmNQ5jwLeLk5REvio1JcMshcbvkYMwy26sJ8pbkvStu",
                "BGsqMegLpV6n6Ve146sSX2dTjUMj3M92HnU8BbNRMhF2",
            ],
            commitment="confirmed",
            epoch=2,
            min_context_slot=1000,
        )
    assert len(result) == 2
    assert result[0].epoch == 2
    assert result[0].effective_slot == 224
    assert result[0].post_balance == 499999442500
    assert result[0].commission == 5
    assert result[1] is None
    assert body(route)["method"] == "getInflationReward"
    assert body(route)["params"] == [
        [
            "6dmNQ5jwLeLk5REvio1JcMshcbvkYMwy26sJ8pbkvStu",
            "BGsqMegLpV6n6Ve146sSX2dTjUMj3M92HnU8BbNRMhF2",
        ],
        {"commitment": "confirmed", "epoch": 2, "minContextSlot": 1000},
    ]
    assert_api_key(route)


@respx.mock
def test_get_inflation_reward_omits_config_when_not_set():
    route = mock_rpc([None])
    with HeliusClient(api_key="test") as client:
        result = client.get_inflation_reward(addresses=["6dmNQ5jwLeLk5REvio1JcMshcbvkYMwy26sJ8pbkvStu"])
    assert result == [None]
    assert body(route)["params"] == [["6dmNQ5jwLeLk5REvio1JcMshcbvkYMwy26sJ8pbkvStu"]]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_largest_accounts
# ---------------------------------------------------------------------------


@respx.mock
def test_get_largest_accounts():
    route = mock_rpc(
        {
            "context": {"slot": 54},
            "value": [
                {
                    "address": "99P8ZgtJYe1buSK8JXkvpLh8xPsCFuLYhz9hQFNw93WJ",
                    "lamports": 999974,
                }
            ],
        }
    )
    with HeliusClient(api_key="test") as client:
        context, accounts = client.get_largest_accounts(filter="circulating")
    assert context == {"slot": 54}
    assert accounts[0].lamports == 999974
    assert body(route)["method"] == "getLargestAccounts"
    assert body(route)["params"] == [{"filter": "circulating"}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_latest_blockhash
# ---------------------------------------------------------------------------


@respx.mock
def test_get_latest_blockhash():
    route = mock_rpc(
        {
            "context": {"slot": 2792},
            "value": {
                "blockhash": "EkSnNWid2cvwEVnVx9aBqawnmiCNiDgp3gUdkDPTKN1N",
                "lastValidBlockHeight": 3090,
            },
        }
    )
    with HeliusClient(api_key="test") as client:
        assert client.get_latest_blockhash(min_context_slot=1) == (
            {"slot": 2792},
            "EkSnNWid2cvwEVnVx9aBqawnmiCNiDgp3gUdkDPTKN1N",
            3090,
        )
    assert body(route)["method"] == "getLatestBlockhash"
    assert body(route)["params"] == [{"minContextSlot": 1}]
    assert_api_key(route)


@respx.mock
def test_get_latest_blockhash_minimal():
    route = mock_rpc(
        {
            "context": {"slot": 2792},
            "value": {
                "blockhash": "EkSnNWid2cvwEVnVx9aBqawnmiCNiDgp3gUdkDPTKN1N",
                "lastValidBlockHeight": 3090,
            },
        }
    )
    with HeliusClient(api_key="test") as client:
        context, blockhash, height = client.get_latest_blockhash()
    assert blockhash == "EkSnNWid2cvwEVnVx9aBqawnmiCNiDgp3gUdkDPTKN1N"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_leader_schedule
# ---------------------------------------------------------------------------


@respx.mock
def test_get_leader_schedule():
    route = mock_rpc({"4Qkev8aNZcqFNSRhQzwyLMFSsi94jHqE8WNVTJzTP99F": [0, 1, 2, 5]})
    with HeliusClient(api_key="test") as client:
        result = client.get_leader_schedule(
            slot=1, identity="4Qkev8aNZcqFNSRhQzwyLMFSsi94jHqE8WNVTJzTP99F"
        )
    assert result == {"4Qkev8aNZcqFNSRhQzwyLMFSsi94jHqE8WNVTJzTP99F": [0, 1, 2, 5]}
    assert body(route)["method"] == "getLeaderSchedule"
    assert body(route)["params"] == [
        1,
        {"identity": "4Qkev8aNZcqFNSRhQzwyLMFSsi94jHqE8WNVTJzTP99F"},
    ]
    assert_api_key(route)


@respx.mock
def test_get_leader_schedule_no_slot():
    route = mock_rpc({"4Qkev8aNZcqFNSRhQzwyLMFSsi94jHqE8WNVTJzTP99F": [0, 1, 2, 5]})
    with HeliusClient(api_key="test") as client:
        client.get_leader_schedule(identity="4Qkev8aNZcqFNSRhQzwyLMFSsi94jHqE8WNVTJzTP99F")
    assert body(route)["params"] == [
        {"identity": "4Qkev8aNZcqFNSRhQzwyLMFSsi94jHqE8WNVTJzTP99F"}
    ]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_max_retransmit_slot
# ---------------------------------------------------------------------------


@respx.mock
def test_get_max_retransmit_slot():
    route = mock_rpc(1234)
    with HeliusClient(api_key="test") as client:
        assert client.get_max_retransmit_slot() == 1234
    assert body(route)["method"] == "getMaxRetransmitSlot"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_max_shred_insert_slot
# ---------------------------------------------------------------------------


@respx.mock
def test_get_max_shred_insert_slot():
    route = mock_rpc(1234)
    with HeliusClient(api_key="test") as client:
        assert client.get_max_shred_insert_slot() == 1234
    assert body(route)["method"] == "getMaxShredInsertSlot"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_minimum_balance_for_rent_exemption
# ---------------------------------------------------------------------------


@respx.mock
def test_get_minimum_balance_for_rent_exemption():
    route = mock_rpc(500)
    with HeliusClient(api_key="test") as client:
        assert client.get_minimum_balance_for_rent_exemption(data_length=128) == 500
    assert body(route)["method"] == "getMinimumBalanceForRentExemption"
    assert body(route)["params"] == [128]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_multiple_accounts
# ---------------------------------------------------------------------------


@respx.mock
def test_get_multiple_accounts():
    # Asserts correct upstream API shape {"dataSlice": {...}}.
    # Will FAIL until client.py:449-450 is fixed to send dataSlice as a nested object.
    route = mock_rpc({"context": {"slot": 341197247}, "value": [ACCOUNT_VALUE]})
    with HeliusClient(api_key="test") as client:
        context, accounts = client.get_multiple_accounts(pubkeys=["Acct"], encoding="base64", data_slice_offset=0, data_slice_length=8)
    assert context == {"slot": 341197247}
    assert accounts[0].rent_epoch == 18446744073709551615
    assert body(route)["method"] == "getMultipleAccounts"
    assert body(route)["params"] == [
        ["Acct"],
        {"encoding": "base64", "dataSlice": {"offset": 0, "length": 8}},
    ]
    assert_api_key(route)


@respx.mock
def test_get_multiple_accounts_null_entry():
    route = mock_rpc({"context": {"slot": 1}, "value": [ACCOUNT_VALUE, None]})
    with HeliusClient(api_key="test") as client:
        context, accounts = client.get_multiple_accounts(pubkeys=["Acct1", "Acct2"])
    assert context == {"slot": 1}
    assert isinstance(accounts[0], Account)
    assert accounts[1] is None
    assert_api_key(route)


def test_get_multiple_accounts_validates_data_slice():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="Set both"):
            client.get_multiple_accounts(pubkeys=["Acct"], data_slice_offset=0)
        with pytest.raises(ValueError, match="Data slice"):
            client.get_multiple_accounts(
                pubkeys=["Acct"],
                encoding="jsonParsed",
                data_slice_offset=0,
                data_slice_length=8,
            )


# ---------------------------------------------------------------------------
# get_program_accounts
# ---------------------------------------------------------------------------


@respx.mock
def test_get_program_accounts():
    route = mock_rpc(
        [
            {
                "pubkey": "CxELquR1gPP8wHe33gZ4QxqGB3sZ9RSwsJ2KshVewkFY",
                "account": ACCOUNT_VALUE,
            }
        ]
    )
    with HeliusClient(api_key="test") as client:
        accounts = client.get_program_accounts(program_id="Program", encoding="base64", data_slice_offset=0, data_slice_length=8)
    assert accounts[0][0] == "CxELquR1gPP8wHe33gZ4QxqGB3sZ9RSwsJ2KshVewkFY"
    assert body(route)["method"] == "getProgramAccounts"
    assert body(route)["params"] == [
        "Program",
        {"encoding": "base64", "dataSlice": {"offset": 0, "length": 8}},
    ]
    assert_api_key(route)


def test_get_program_accounts_validates_data_slice_pair():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="Set both"):
            client.get_program_accounts(program_id="Program", data_slice_offset=0)


# ---------------------------------------------------------------------------
# get_recent_performance_samples
# ---------------------------------------------------------------------------


@respx.mock
def test_get_recent_performance_samples():
    route = mock_rpc(
        [
            {
                "slot": 348125,
                "numTransactions": 126,
                "numNonVoteTransactions": 1,
                "samplePeriodSecs": 60,
                "numSlots": 126,
            }
        ]
    )
    with HeliusClient(api_key="test") as client:
        samples = client.get_recent_performance_samples(limit=1)
    assert samples[0].num_transactions == 126
    assert samples[0].sample_period_secs == 60
    assert body(route)["method"] == "getRecentPerformanceSamples"
    assert body(route)["params"] == [1]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_recent_prioritization_fees
# ---------------------------------------------------------------------------


@respx.mock
def test_get_recent_prioritization_fees():
    route = mock_rpc([{"slot": 348125, "prioritizationFee": 1234}])
    with HeliusClient(api_key="test") as client:
        assert client.get_recent_prioritization_fees(locked_writable_accounts=["Acct"]) == [(348125, 1234)]
    assert body(route)["method"] == "getRecentPrioritizationFees"
    assert body(route)["params"] == [["Acct"]]
    assert_api_key(route)


@respx.mock
def test_get_recent_prioritization_fees_no_accounts():
    route = mock_rpc([{"slot": 348125, "prioritizationFee": 1234}])
    with HeliusClient(api_key="test") as client:
        client.get_recent_prioritization_fees()
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_signatures_for_address
# ---------------------------------------------------------------------------


@respx.mock
def test_get_signatures_for_address():
    route = mock_rpc(
        [
            {
                "signature": "5h6xBEauJ3PK6SWCZ1PGCzN3gAPdAHWyRqQqdDMNLdSQQRuHFpktzq1nzCvL7pxDqRan",
                "slot": 114,
                "err": None,
                "memo": None,
                "blockTime": None,
                "confirmationStatus": "finalized",
            }
        ]
    )
    with HeliusClient(api_key="test") as client:
        signatures = client.get_signatures_for_address(address="Addr", limit=1, before="before")
    assert signatures[0].signature.startswith("5h6x")
    assert signatures[0].confirmation_status == "finalized"
    assert body(route)["method"] == "getSignaturesForAddress"
    assert body(route)["params"] == ["Addr", {"limit": 1, "before": "before"}]
    assert_api_key(route)


@respx.mock
def test_get_signatures_for_address_sends_default_limit():
    route = mock_rpc([])
    with HeliusClient(api_key="test") as client:
        client.get_signatures_for_address(address="Addr")
    assert body(route)["params"] == ["Addr", {"limit": 1000}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_signature_statuses
# ---------------------------------------------------------------------------


@respx.mock
def test_get_signature_statuses():
    route = mock_rpc(
        {
            "context": {"slot": 82},
            "value": [
                {
                    "slot": 48,
                    "confirmations": 48,
                    "err": None,
                    "confirmationStatus": "finalized",
                },
                None,
            ],
        }
    )
    with HeliusClient(api_key="test") as client:
        context, statuses = client.get_signature_statuses(signatures=["sig"], search_transaction_history=True)
    assert context == {"slot": 82}
    assert statuses[0].confirmation_status == "finalized"
    assert statuses[0].confirmations == 48
    assert statuses[1] is None
    assert body(route)["method"] == "getSignatureStatuses"
    assert body(route)["params"] == [["sig"], {"searchTransactionHistory": True}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_slot
# ---------------------------------------------------------------------------


@respx.mock
def test_get_slot():
    route = mock_rpc(1234)
    with HeliusClient(api_key="test") as client:
        assert client.get_slot(commitment="processed") == 1234
    assert body(route)["method"] == "getSlot"
    assert body(route)["params"] == [{"commitment": "processed"}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_slot_leader
# ---------------------------------------------------------------------------


@respx.mock
def test_get_slot_leader():
    route = mock_rpc("ENvAW7JScgYq6o4zKZwewtkzzJgDzuJAFxYasvmEQdpS")
    with HeliusClient(api_key="test") as client:
        assert (
            client.get_slot_leader(min_context_slot=1)
            == "ENvAW7JScgYq6o4zKZwewtkzzJgDzuJAFxYasvmEQdpS"
        )
    assert body(route)["method"] == "getSlotLeader"
    assert body(route)["params"] == [{"minContextSlot": 1}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_slot_leaders
# ---------------------------------------------------------------------------


@respx.mock
def test_get_slot_leaders():
    route = mock_rpc(["ChorusmmK7i1AxXeiTtQgQZhQNiXYU84ULeaYF1EH15n"])
    with HeliusClient(api_key="test") as client:
        assert client.get_slot_leaders(start_slot=1, limit=2) == [
            "ChorusmmK7i1AxXeiTtQgQZhQNiXYU84ULeaYF1EH15n"
        ]
    assert body(route)["method"] == "getSlotLeaders"
    assert body(route)["params"] == [1, 2]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_stake_minimum_delegation
# ---------------------------------------------------------------------------


@respx.mock
def test_get_stake_minimum_delegation():
    route = mock_rpc({"context": {"slot": 501}, "value": 1000000000})
    with HeliusClient(api_key="test") as client:
        assert client.get_stake_minimum_delegation(commitment="confirmed") == (
            {"slot": 501},
            1000000000,
        )
    assert body(route)["method"] == "getStakeMinimumDelegation"
    assert body(route)["params"] == [{"commitment": "confirmed"}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_supply
# ---------------------------------------------------------------------------


@respx.mock
def test_get_supply():
    route = mock_rpc(
        {
            "context": {"slot": 1114},
            "value": {
                "total": 1016000,
                "circulating": 16000,
                "nonCirculating": 1000000,
                "nonCirculatingAccounts": [
                    "FEy8pTbP5fEoqMV1GdTz83byuA8EKByqYat1PKDgVAq5"
                ],
            },
        }
    )
    with HeliusClient(api_key="test") as client:
        context, supply = client.get_supply(
            commitment="confirmed",
            exclude_non_circulating_accounts_list=True,
        )
    assert context == {"slot": 1114}
    assert supply.non_circulating == 1000000
    assert body(route)["method"] == "getSupply"
    assert body(route)["params"] == [
        {"commitment": "confirmed", "excludeNonCirculatingAccountsList": True}
    ]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_token_account_balance
# ---------------------------------------------------------------------------


@respx.mock
def test_get_token_account_balance():
    route = mock_rpc({"context": {"slot": 1114}, "value": TOKEN_BALANCE_VALUE})
    with HeliusClient(api_key="test") as client:
        context, balance = client.get_token_account_balance(token_account="TokenAcct")
    assert context == {"slot": 1114}
    assert balance.ui_amount == 98.64
    assert balance.amount == "9864"
    assert body(route)["method"] == "getTokenAccountBalance"
    assert body(route)["params"] == ["TokenAcct"]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_token_accounts_by_delegate
# ---------------------------------------------------------------------------


@respx.mock
def test_get_token_accounts_by_delegate():
    route = mock_rpc(
        {
            "context": {"slot": 1114},
            "value": [{"pubkey": "TokenAcct", "account": ACCOUNT_VALUE}],
        }
    )
    with HeliusClient(api_key="test") as client:
        context, accounts = client.get_token_accounts_by_delegate(delegate_pub_key="Delegate", program_id="Program")
    assert context == {"slot": 1114}
    assert accounts[0][0] == "TokenAcct"
    assert body(route)["method"] == "getTokenAccountsByDelegate"
    assert body(route)["params"] == ["Delegate", {"programId": "Program"}]
    assert_api_key(route)


def test_get_token_accounts_by_delegate_validates_filters_and_data_slice():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="exactly one"):
            client.get_token_accounts_by_delegate(delegate_pub_key="Delegate")
        with pytest.raises(ValueError, match="exactly one"):
            client.get_token_accounts_by_delegate(delegate_pub_key="Delegate", mint="Mint", program_id="Program")
        with pytest.raises(ValueError, match="Set both"):
            client.get_token_accounts_by_delegate(delegate_pub_key="Delegate", mint="Mint", data_slice_offset=0)
        with pytest.raises(ValueError, match="dataSlice"):
            client.get_token_accounts_by_delegate(
                delegate_pub_key="Delegate",
                mint="Mint",
                encoding="jsonParsed",
                data_slice_offset=0,
                data_slice_length=8,
            )


# ---------------------------------------------------------------------------
# get_token_accounts_by_owner
# ---------------------------------------------------------------------------


@respx.mock
def test_get_token_accounts_by_owner():
    route = mock_rpc(
        {
            "context": {"slot": 1114},
            "value": [{"pubkey": "TokenAcct", "account": ACCOUNT_VALUE}],
        }
    )
    with HeliusClient(api_key="test") as client:
        context, accounts = client.get_token_accounts_by_owner(
            owner_pub_key="Owner",
            mint="Mint",
            encoding="jsonParsed",
        )
    assert context == {"slot": 1114}
    assert accounts[0][0] == "TokenAcct"
    assert accounts[0][1].rent_epoch == 18446744073709551615
    assert body(route)["method"] == "getTokenAccountsByOwner"
    assert body(route)["params"] == [
        "Owner",
        {"mint": "Mint"},
        {"encoding": "jsonParsed"},
    ]
    assert_api_key(route)


def test_get_token_accounts_by_owner_validates_filters_and_data_slice():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="exactly one"):
            client.get_token_accounts_by_owner(owner_pub_key="Owner")
        with pytest.raises(ValueError, match="exactly one"):
            client.get_token_accounts_by_owner(owner_pub_key="Owner", mint="Mint", program_id="Program")
        with pytest.raises(ValueError, match="Set both"):
            client.get_token_accounts_by_owner(owner_pub_key="Owner", mint="Mint", data_slice_offset=0)
        with pytest.raises(ValueError, match="dataSlice"):
            client.get_token_accounts_by_owner(
                owner_pub_key="Owner",
                mint="Mint",
                encoding="jsonParsed",
                data_slice_offset=0,
                data_slice_length=8,
            )


# ---------------------------------------------------------------------------
# get_token_largest_accounts
# ---------------------------------------------------------------------------


@respx.mock
def test_get_token_largest_accounts():
    route = mock_rpc(
        {
            "context": {"slot": 1114},
            "value": [
                {
                    "address": "FYjHNoFtSQ5uijKrZFyYAxvEr87hsKXkXcxkcmkBAf4r",
                    "amount": "771",
                    "decimals": 2,
                    "uiAmount": 7.71,
                    "uiAmountString": "7.71",
                }
            ],
        }
    )
    with HeliusClient(api_key="test") as client:
        context, accounts = client.get_token_largest_accounts(mint="Mint", commitment="finalized")
    assert context == {"slot": 1114}
    assert accounts[0].address == "FYjHNoFtSQ5uijKrZFyYAxvEr87hsKXkXcxkcmkBAf4r"
    assert accounts[0].ui_amount == 7.71
    assert body(route)["method"] == "getTokenLargestAccounts"
    assert body(route)["params"] == ["Mint", {"commitment": "finalized"}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_token_supply
# ---------------------------------------------------------------------------


@respx.mock
def test_get_token_supply():
    route = mock_rpc({"context": {"slot": 1114}, "value": TOKEN_BALANCE_VALUE})
    with HeliusClient(api_key="test") as client:
        context, supply = client.get_token_supply(mint_address="Mint")
    assert context == {"slot": 1114}
    assert supply.amount == "9864"
    assert body(route)["method"] == "getTokenSupply"
    assert body(route)["params"] == ["Mint"]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_transaction
# ---------------------------------------------------------------------------


@respx.mock
def test_get_transaction():
    route = mock_rpc(
        {
            "slot": 430,
            "blockTime": 1574721591,
            "meta": {
                "err": None,
                "fee": 5000,
                "preBalances": [1],
                "postBalances": [2],
                "preTokenBalances": None,
                "postTokenBalances": None,
                "innerInstructions": None,
                "logMessages": None,
            },
            "transaction": {
                "signatures": [
                    "2nBhEBYYvfaAe16UMNqRHre4YNSskvuYgx3M6E4JP1oDYvZEJHvoPzyUidNgNX5r9sTyN1"
                ],
                "message": {
                    "accountKeys": ["3UVYmECPPMZSCqWKfENfuoTv51fTDTWicX9xmBD2euKe"],
                    "recentBlockhash": "mfcyqEXB3DnHXki6KjjmZck6YjmZLvpAByy2fj4nh6B",
                },
            },
            "version": "legacy",
        }
    )
    with HeliusClient(api_key="test") as client:
        transaction = client.get_transaction(transaction_signature="sig", encoding="json")
    assert transaction.slot == 430
    assert transaction.block_time == 1574721591
    assert transaction.meta.fee == 5000
    assert body(route)["method"] == "getTransaction"
    assert body(route)["params"] == ["sig", {"encoding": "json"}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_transaction_count
# ---------------------------------------------------------------------------


@respx.mock
def test_get_transaction_count():
    route = mock_rpc(268)
    with HeliusClient(api_key="test") as client:
        assert client.get_transaction_count(min_context_slot=1) == 268
    assert body(route)["method"] == "getTransactionCount"
    assert body(route)["params"] == [{"minContextSlot": 1}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_version
# ---------------------------------------------------------------------------


@respx.mock
def test_get_version():
    route = mock_rpc({"solana-core": "1.16.7", "feature-set": 2891131721})
    with HeliusClient(api_key="test") as client:
        assert client.get_version() == ("1.16.7", 2891131721)
    assert body(route)["method"] == "getVersion"
    assert body(route).get("params") is None
    assert_api_key(route)


# ---------------------------------------------------------------------------
# get_vote_accounts
# ---------------------------------------------------------------------------


@respx.mock
def test_get_vote_accounts():
    route = mock_rpc({"current": [VOTING_ACCOUNT_VALUE], "delinquent": []})
    with HeliusClient(api_key="test") as client:
        current, delinquent = client.get_vote_accounts(vote_pubkey="Vote")
    assert current[0].vote_pubkey == "3ZT31jkAGhUaw8jsy4bTknwBMP8i4Eueh52By4zXcsVw"
    assert current[0].epoch_credits == [[1, 64, 0], [2, 192, 64]]
    assert delinquent == []
    assert body(route)["method"] == "getVoteAccounts"
    assert body(route)["params"] == [{"votePubkey": "Vote"}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# is_blockhash_valid
# ---------------------------------------------------------------------------


@respx.mock
def test_is_blockhash_valid():
    route = mock_rpc({"context": {"slot": 2483}, "value": False})
    with HeliusClient(api_key="test") as client:
        assert client.is_blockhash_valid(blockhash="hash") == ({"slot": 2483}, False)
    assert body(route)["method"] == "isBlockhashValid"
    assert body(route)["params"] == ["hash"]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# request_airdrop
# ---------------------------------------------------------------------------


@respx.mock
def test_request_airdrop():
    route = mock_rpc(
        "5VERv8NMvzbJMEkV8xnrLkEaWRtSz9CosKDYjCJjBRnbJLgp8uirBgmQpjKhoR4tjF3ZpRzrFmBV6UjKdiSZkQUW"
    )
    with HeliusClient(api_key="test") as client:
        result = client.request_airdrop(public_key="Pubkey", lamports=1, commitment="confirmed")
    assert result.startswith("5VERv8")
    assert body(route)["method"] == "requestAirdrop"
    assert body(route)["params"] == ["Pubkey", 1, {"commitment": "confirmed"}]
    assert_api_key(route)


# ---------------------------------------------------------------------------
# minimum_ledger_slot
# ---------------------------------------------------------------------------


@respx.mock
def test_minimum_ledger_slot():
    route = mock_rpc(1234)
    with HeliusClient(api_key="test") as client:
        assert client.minimum_ledger_slot() == 1234
    assert body(route)["method"] == "minimumLedgerSlot"
    assert body(route).get("params") is None
    assert_api_key(route)
