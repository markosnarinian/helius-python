import json

import httpx
import pytest
import respx

from helius.client import HeliusClient

ACCOUNT_VALUE = {
    "lamports": 42,
    "owner": "11111111111111111111111111111111",
    "data": ["", "base64"],
    "executable": False,
    "rentEpoch": 123,
    "space": 0,
}

TOKEN_BALANCE_VALUE = {
    "amount": "100",
    "decimals": 2,
    "uiAmount": 1.0,
    "uiAmountString": "1",
}

VOTING_ACCOUNT_VALUE = {
    "votePubkey": "Vote11111111111111111111111111111111111",
    "nodePubkey": "Node11111111111111111111111111111111111",
    "activatedStake": 100,
    "epochVoteAccount": True,
    "commission": 5,
    "lastVote": 10,
    "rootSlot": 9,
    "epochCredits": [[1, 2, 3]],
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


@respx.mock
def test_get_account_info():
    route = mock_rpc({"context": {"slot": 1}, "value": ACCOUNT_VALUE})
    with HeliusClient(api_key="test") as client:
        context, account = client.get_account_info(
            "Acct",
            encoding="base64",
            data_slice_offset=0,
            data_slice_length=8,
            min_context_slot=10,
        )
    assert context == {"slot": 1}
    assert account.lamports == 42
    assert body(route)["method"] == "getAccountInfo"
    assert body(route)["params"] == [
        "Acct",
        {
            "encoding": "base64",
            "dataSlice": {"offset": 0, "length": 8},
            "minContextSlot": 10,
        },
    ]


def test_get_account_info_validates_data_slice_pair():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="Set both"):
            client.get_account_info("Acct", data_slice_offset=0)


@respx.mock
def test_get_balance():
    route = mock_rpc({"context": {"slot": 1}, "value": 42})
    with HeliusClient(api_key="test") as client:
        assert client.get_balance("Acct", commitment="finalized") == ({"slot": 1}, 42)
    assert body(route)["method"] == "getBalance"
    assert body(route)["params"] == ["Acct", {"commitment": "finalized"}]
    assert_api_key(route)


@respx.mock
def test_get_block():
    route = mock_rpc(
        {
            "blockhash": "hash",
            "previousBlockhash": "prev",
            "parentSlot": 1,
            "transactions": [],
            "blockTime": 123,
            "blockHeight": 456,
            "rewards": [],
        }
    )
    with HeliusClient(api_key="test") as client:
        block = client.get_block(1, commitment="finalized", rewards=True)
    assert block.blockhash == "hash"
    assert body(route)["method"] == "getBlock"
    assert body(route)["params"] == [1, {"commitment": "finalized", "rewards": True}]
    assert_api_key(route)


@respx.mock
def test_get_block_commitment():
    route = mock_rpc({"commitment": [1], "totalStake": 1})
    with HeliusClient(api_key="test") as client:
        result = client.get_block_commitment(1)
    assert result.total_stake == 1
    assert body(route)["method"] == "getBlockCommitment"
    assert body(route)["params"] == [1]


@respx.mock
def test_get_block_height():
    route = mock_rpc(99)
    with HeliusClient(api_key="test") as client:
        assert client.get_block_height(commitment="confirmed") == 99
    assert body(route)["method"] == "getBlockHeight"
    assert body(route)["params"] == [{"commitment": "confirmed"}]


@respx.mock
def test_get_block_production_with_range():
    route = mock_rpc({"context": {"slot": 1}, "value": {"byIdentity": {}}})
    with HeliusClient(api_key="test") as client:
        context, value = client.get_block_production(first_slot=1, last_slot=2)
    assert context == {"slot": 1}
    assert value == {"byIdentity": {}}
    assert body(route)["method"] == "getBlockProduction"
    assert body(route)["params"] == [{"range": {"firstSlot": 1, "lastSlot": 2}}]


def test_get_block_production_validates_required_range_inputs():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="At least one"):
            client.get_block_production()
        with pytest.raises(ValueError, match="first_slot"):
            client.get_block_production(identity="id", last_slot=2)


@respx.mock
def test_get_blocks():
    route = mock_rpc([1, 2])
    with HeliusClient(api_key="test") as client:
        assert client.get_blocks(1, 2, commitment="finalized") == [1, 2]
    assert body(route)["method"] == "getBlocks"
    assert body(route)["params"] == [1, 2, {"commitment": "finalized"}]


@respx.mock
def test_get_blocks_with_limit():
    route = mock_rpc([1, 2])
    with HeliusClient(api_key="test") as client:
        assert client.get_blocks_with_limit(1, 2) == [1, 2]
    assert body(route)["method"] == "getBlocksWithLimit"
    assert body(route)["params"] == [1, 2]


@respx.mock
def test_get_block_time():
    route = mock_rpc(123)
    with HeliusClient(api_key="test") as client:
        assert client.get_block_time(1) == 123
    assert body(route)["method"] == "getBlockTime"
    assert body(route)["params"] == [1]


@respx.mock
def test_get_cluster_nodes():
    route = mock_rpc(
        [
            {
                "pubkey": "Node",
                "gossip": None,
                "tpu": None,
                "rpc": None,
                "version": "1.0",
                "featureSet": 1,
                "shredVersion": 2,
            }
        ]
    )
    with HeliusClient(api_key="test") as client:
        nodes = client.get_cluster_nodes()
    assert nodes[0].feature_set == 1
    assert body(route)["method"] == "getClusterNodes"


@respx.mock
def test_get_epoch_info():
    route = mock_rpc(
        {
            "absoluteSlot": 10,
            "blockHeight": 9,
            "epoch": 1,
            "slotIndex": 2,
            "slotsInEpoch": 32,
            "transactionCount": 100,
        }
    )
    with HeliusClient(api_key="test") as client:
        result = client.get_epoch_info(min_context_slot=1)
    assert result.absolute_slot == 10
    assert body(route)["method"] == "getEpochInfo"
    assert body(route)["params"] == [{"minContextSlot": 1}]


@respx.mock
def test_get_epoch_schedule():
    route = mock_rpc(
        {
            "slotsPerEpoch": 32,
            "leaderScheduleSlotOffset": 8,
            "warmup": True,
            "firstNormalEpoch": 1,
            "firstNormalSlot": 32,
        }
    )
    with HeliusClient(api_key="test") as client:
        result = client.get_epoch_schedule()
    assert result.first_normal_slot == 32
    assert body(route)["method"] == "getEpochSchedule"


@respx.mock
def test_get_fee_for_message():
    route = mock_rpc({"context": {"slot": 1}, "value": 5000})
    with HeliusClient(api_key="test") as client:
        assert client.get_fee_for_message("msg", commitment="processed") == (
            {"slot": 1},
            5000,
        )
    assert body(route)["method"] == "getFeeForMessage"
    assert body(route)["params"] == ["msg", {"commitment": "processed"}]


@respx.mock
def test_get_first_available_block():
    route = mock_rpc(1)
    with HeliusClient(api_key="test") as client:
        assert client.get_first_available_block() == 1
    assert body(route)["method"] == "getFirstAvailableBlock"


@respx.mock
def test_get_genesis_hash():
    route = mock_rpc("hash")
    with HeliusClient(api_key="test") as client:
        assert client.get_genesis_hash() == "hash"
    assert body(route)["method"] == "getGenesisHash"


@respx.mock
def test_get_health_true():
    route = mock_rpc("ok")
    with HeliusClient(api_key="test") as client:
        assert client.get_health() is True
    assert body(route)["method"] == "getHealth"


@respx.mock
def test_get_highest_snapshot_slot():
    route = mock_rpc({"full": 10, "incremental": 11})
    with HeliusClient(api_key="test") as client:
        assert client.get_highest_snapshot_slot() == {"full": 10, "incremental": 11}
    assert body(route)["method"] == "getHighestSnapshotSlot"


@respx.mock
def test_get_identity():
    route = mock_rpc({"identity": "node"})
    with HeliusClient(api_key="test") as client:
        assert client.get_identity() == "node"
    assert body(route)["method"] == "getIdentity"


@respx.mock
def test_get_inflation_governor():
    route = mock_rpc(
        {
            "initial": 0.08,
            "terminal": 0.015,
            "taper": 0.15,
            "foundation": 0.05,
            "foundationTerm": 7.0,
        }
    )
    with HeliusClient(api_key="test") as client:
        result = client.get_inflation_governor(commitment="finalized")
    assert result.foundation_term == 7.0
    assert body(route)["method"] == "getInflationGovernor"
    assert body(route)["params"] == [{"commitment": "finalized"}]


@respx.mock
def test_get_inflation_rate():
    route = mock_rpc({"total": 0.07, "validator": 0.06, "foudnation": 0.01, "epoch": 1})
    with HeliusClient(api_key="test") as client:
        result = client.get_inflation_rate()
    assert result.epoch == 1
    assert body(route)["method"] == "getInflationRate"


@respx.mock
def test_get_largest_accounts():
    route = mock_rpc(
        {"context": {"slot": 1}, "value": [{"address": "Acct", "lamports": 42}]}
    )
    with HeliusClient(api_key="test") as client:
        context, accounts = client.get_largest_accounts(filter="circulating")
    assert context == {"slot": 1}
    assert accounts[0].lamports == 42
    assert body(route)["method"] == "getLargestAccounts"
    assert body(route)["params"] == [{"filter": "circulating"}]


@respx.mock
def test_get_latest_blockhash():
    route = mock_rpc(
        {
            "context": {"slot": 1},
            "value": {"blockhash": "hash", "lastValidBlockHeight": 99},
        }
    )
    with HeliusClient(api_key="test") as client:
        assert client.get_latest_blockhash(min_context_slot=1) == (
            {"slot": 1},
            "hash",
            99,
        )
    assert body(route)["method"] == "getLatestBlockhash"
    assert body(route)["params"] == [{"minContextSlot": 1}]


@respx.mock
def test_get_leader_schedule():
    route = mock_rpc({"identity": [1, 2]})
    with HeliusClient(api_key="test") as client:
        assert client.get_leader_schedule(slot=1, identity="identity") == {
            "identity": [1, 2]
        }
    assert body(route)["method"] == "getLeaderSchedule"
    assert body(route)["params"] == [1, {"identity": "identity"}]


@respx.mock
def test_get_max_retransmit_slot():
    route = mock_rpc(10)
    with HeliusClient(api_key="test") as client:
        assert client.get_max_retransmit_slot() == 10
    assert body(route)["method"] == "getMaxRetransmitSlot"


@respx.mock
def test_get_max_shred_insert_slot():
    route = mock_rpc(10)
    with HeliusClient(api_key="test") as client:
        assert client.get_max_shred_insert_slot() == 10
    assert body(route)["method"] == "getMaxShredInsertSlot"


@respx.mock
def test_get_minimum_balance_for_rent_exemption():
    route = mock_rpc(2039280)
    with HeliusClient(api_key="test") as client:
        assert client.get_minimum_balance_for_rent_exemption(128) == 2039280
    assert body(route)["method"] == "getMinimumBalanceForRentExemption"
    assert body(route)["params"] == [128]


@respx.mock
def test_get_multiple_accounts():
    route = mock_rpc({"context": {"slot": 1}, "value": [ACCOUNT_VALUE]})
    with HeliusClient(api_key="test") as client:
        context, accounts = client.get_multiple_accounts(
            ["Acct"], encoding="base64", data_slice_offset=0, data_slice_length=8
        )
    assert context == {"slot": 1}
    assert accounts[0].rent_epoch == 123
    assert body(route)["method"] == "getMultipleAccounts"
    assert body(route)["params"] == [
        ["Acct"],
        {"encoding": "base64", "dataSliceOffset": 0, "dataSliceLength": 8},
    ]


def test_get_multiple_accounts_validates_data_slice():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="Set both"):
            client.get_multiple_accounts(["Acct"], data_slice_offset=0)
        with pytest.raises(ValueError, match="Data slice"):
            client.get_multiple_accounts(
                ["Acct"],
                encoding="jsonParsed",
                data_slice_offset=0,
                data_slice_length=8,
            )


@respx.mock
def test_get_program_accounts():
    route = mock_rpc([{"pubkey": "Acct", "account": ACCOUNT_VALUE}])
    with HeliusClient(api_key="test") as client:
        accounts = client.get_program_accounts(
            "Program", encoding="base64", data_slice_offset=0, data_slice_length=8
        )
    assert accounts[0][0] == "Acct"
    assert body(route)["method"] == "getProgramAccounts"
    assert body(route)["params"] == [
        "Program",
        {"encoding": "base64", "dataSlice": {"offset": 0, "length": 8}},
    ]


def test_get_program_accounts_validates_data_slice_pair():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="Set both"):
            client.get_program_accounts("Program", data_slice_offset=0)


@respx.mock
def test_get_recent_performance_samples():
    route = mock_rpc(
        [
            {
                "slot": 1,
                "numTransactions": 10,
                "numNonVoteTransactions": 7,
                "samplePeriodSecs": 60,
                "numSlots": 4,
            }
        ]
    )
    with HeliusClient(api_key="test") as client:
        samples = client.get_recent_performance_samples(limit=1)
    assert samples[0].num_transactions == 10
    assert body(route)["method"] == "getRecentPerformanceSamples"
    assert body(route)["params"] == [1]


@respx.mock
def test_get_recent_prioritization_fees():
    route = mock_rpc([{"slot": 1, "prioritizationFee": 2}])
    with HeliusClient(api_key="test") as client:
        assert client.get_recent_prioritization_fees(["Acct"]) == [(1, 2)]
    assert body(route)["method"] == "getRecentPrioritizationFees"
    assert body(route)["params"] == [["Acct"]]


@respx.mock
def test_get_signatures_for_address():
    route = mock_rpc(
        [
            {
                "signature": "sig",
                "slot": 1,
                "err": None,
                "memo": None,
                "blockTime": 123,
                "confirmationStatus": "finalized",
            }
        ]
    )
    with HeliusClient(api_key="test") as client:
        signatures = client.get_signatures_for_address("Addr", limit=1, before="before")
    assert signatures[0].signature == "sig"
    assert body(route)["method"] == "getSignaturesForAddress"
    assert body(route)["params"] == ["Addr", {"limit": 1, "before": "before"}]


@respx.mock
def test_get_signature_statuses():
    route = mock_rpc(
        {
            "context": {"slot": 1},
            "value": [
                {
                    "slot": 1,
                    "confirmations": None,
                    "err": None,
                    "confirmationStatus": "finalized",
                },
                None,
            ],
        }
    )
    with HeliusClient(api_key="test") as client:
        context, statuses = client.get_signature_statuses(
            ["sig"], search_transaction_history=True
        )
    assert context == {"slot": 1}
    assert statuses[0].confirmation_status == "finalized"
    assert statuses[1] is None
    assert body(route)["method"] == "getSignatureStatuses"
    assert body(route)["params"] == [["sig"], {"searchTransactionHistory": True}]


@respx.mock
def test_get_slot():
    route = mock_rpc(5)
    with HeliusClient(api_key="test") as client:
        assert client.get_slot(commitment="processed") == 5
    assert body(route)["method"] == "getSlot"
    assert body(route)["params"] == [{"commitment": "processed"}]


@respx.mock
def test_get_slot_leader():
    route = mock_rpc("Leader")
    with HeliusClient(api_key="test") as client:
        assert client.get_slot_leader(min_context_slot=1) == "Leader"
    assert body(route)["method"] == "getSlotLeader"
    assert body(route)["params"] == [{"minContextSlot": 1}]


@respx.mock
def test_get_slot_leaders():
    route = mock_rpc(["Leader"])
    with HeliusClient(api_key="test") as client:
        assert client.get_slot_leaders(1, 2) == ["Leader"]
    assert body(route)["method"] == "getSlotLeaders"
    assert body(route)["params"] == [1, 2]


@respx.mock
def test_get_stake_minimum_delegation():
    route = mock_rpc({"context": {"slot": 1}, "value": 1})
    with HeliusClient(api_key="test") as client:
        assert client.get_stake_minimum_delegation(commitment="confirmed") == (
            {"slot": 1},
            1,
        )
    assert body(route)["method"] == "getStakeMinimumDelegation"
    assert body(route)["params"] == [{"commitment": "confirmed"}]


@respx.mock
def test_get_supply():
    route = mock_rpc(
        {
            "context": {"slot": 1},
            "value": {
                "total": 100,
                "circulating": 80,
                "nonCirculating": 20,
                "nonCirculatingAccounts": ["Acct"],
            },
        }
    )
    with HeliusClient(api_key="test") as client:
        context, supply = client.get_supply(
            commitment="confirmed",
            exclude_non_circulating_accounts_list=True,
        )
    assert context == {"slot": 1}
    assert supply.non_circulating == 20
    assert body(route)["method"] == "getSupply"
    assert body(route)["params"] == [
        {"commitment": "confirmed", "excludeNonCirculatingAccountsList": True}
    ]


@respx.mock
def test_get_token_account_balance():
    route = mock_rpc({"context": {"slot": 1}, "value": TOKEN_BALANCE_VALUE})
    with HeliusClient(api_key="test") as client:
        context, balance = client.get_token_account_balance("TokenAcct")
    assert context == {"slot": 1}
    assert balance.ui_amount == 1.0
    assert body(route)["method"] == "getTokenAccountBalance"
    assert body(route)["params"] == ["TokenAcct"]


@respx.mock
def test_get_token_accounts_by_delegate():
    route = mock_rpc(
        {
            "context": {"slot": 1},
            "value": [{"pubkey": "TokenAcct", "account": ACCOUNT_VALUE}],
        }
    )
    with HeliusClient(api_key="test") as client:
        context, accounts = client.get_token_accounts_by_delegate(
            "Delegate", program_id="Program"
        )
    assert context == {"slot": 1}
    assert accounts[0][0] == "TokenAcct"
    assert body(route)["method"] == "getTokenAccountsByDelegate"
    assert body(route)["params"] == ["Delegate", {"programId": "Program"}]


def test_get_token_accounts_by_delegate_validates_filters_and_data_slice():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="exactly one"):
            client.get_token_accounts_by_delegate("Delegate")
        with pytest.raises(ValueError, match="exactly one"):
            client.get_token_accounts_by_delegate(
                "Delegate", mint="Mint", program_id="Program"
            )
        with pytest.raises(ValueError, match="Set both"):
            client.get_token_accounts_by_delegate(
                "Delegate", mint="Mint", data_slice_offset=0
            )
        with pytest.raises(ValueError, match="dataSlice"):
            client.get_token_accounts_by_delegate(
                "Delegate",
                mint="Mint",
                encoding="jsonParsed",
                data_slice_offset=0,
                data_slice_length=8,
            )


@respx.mock
def test_get_token_accounts_by_owner():
    route = mock_rpc(
        {
            "context": {"slot": 1},
            "value": [{"pubkey": "TokenAcct", "account": ACCOUNT_VALUE}],
        }
    )
    with HeliusClient(api_key="test") as client:
        context, accounts = client.get_token_accounts_by_owner(
            "Owner",
            mint="Mint",
            encoding="jsonParsed",
        )
    assert context == {"slot": 1}
    assert accounts[0][0] == "TokenAcct"
    assert accounts[0][1].rent_epoch == 123
    assert body(route)["method"] == "getTokenAccountsByOwner"
    assert body(route)["params"] == [
        "Owner",
        {"mint": "Mint"},
        {"encoding": "jsonParsed"},
    ]


def test_get_token_accounts_by_owner_validates_filters_and_data_slice():
    with HeliusClient(api_key="test") as client:
        with pytest.raises(ValueError, match="exactly one"):
            client.get_token_accounts_by_owner("Owner")
        with pytest.raises(ValueError, match="exactly one"):
            client.get_token_accounts_by_owner(
                "Owner", mint="Mint", program_id="Program"
            )
        with pytest.raises(ValueError, match="Set both"):
            client.get_token_accounts_by_owner(
                "Owner", mint="Mint", data_slice_offset=0
            )
        with pytest.raises(ValueError, match="dataSlice"):
            client.get_token_accounts_by_owner(
                "Owner",
                mint="Mint",
                encoding="jsonParsed",
                data_slice_offset=0,
                data_slice_length=8,
            )


@respx.mock
def test_get_token_largest_accounts():
    route = mock_rpc(
        {
            "context": {"slot": 1},
            "value": [{"address": "TokenAcct", **TOKEN_BALANCE_VALUE}],
        }
    )
    with HeliusClient(api_key="test") as client:
        context, accounts = client.get_token_largest_accounts(
            "Mint", commitment="finalized"
        )
    assert context == {"slot": 1}
    assert accounts[0].address == "TokenAcct"
    assert body(route)["method"] == "getTokenLargestAccounts"
    assert body(route)["params"] == ["Mint", {"commitment": "finalized"}]


@respx.mock
def test_get_token_supply():
    route = mock_rpc({"context": {"slot": 1}, "value": TOKEN_BALANCE_VALUE})
    with HeliusClient(api_key="test") as client:
        context, supply = client.get_token_supply("Mint")
    assert context == {"slot": 1}
    assert supply.amount == "100"
    assert body(route)["method"] == "getTokenSupply"
    assert body(route)["params"] == ["Mint"]


@respx.mock
def test_get_transaction():
    route = mock_rpc(
        {
            "slot": 1,
            "blockTime": 123,
            "meta": None,
            "transaction": {"signatures": ["sig"]},
            "version": "legacy",
        }
    )
    with HeliusClient(api_key="test") as client:
        transaction = client.get_transaction("sig", encoding="json")
    assert transaction.slot == 1
    assert body(route)["method"] == "getTransaction"
    assert body(route)["params"] == ["sig", {"encoding": "json"}]


@respx.mock
def test_get_transaction_count():
    route = mock_rpc(123)
    with HeliusClient(api_key="test") as client:
        assert client.get_transaction_count(min_context_slot=1) == 123
    assert body(route)["method"] == "getTransactionCount"
    assert body(route)["params"] == [{"minContextSlot": 1}]


@respx.mock
def test_get_version():
    route = mock_rpc({"solana-core": "1.18.0", "feature-set": 1})
    with HeliusClient(api_key="test") as client:
        assert client.get_version() == ("1.18.0", 1)
    assert body(route)["method"] == "getVersion"


@respx.mock
def test_get_vote_accounts():
    route = mock_rpc({"current": [VOTING_ACCOUNT_VALUE], "delinquent": []})
    with HeliusClient(api_key="test") as client:
        current, delinquent = client.get_vote_accounts(vote_pubkey="Vote")
    assert current[0].vote_pubkey.startswith("Vote")
    assert delinquent == []
    assert body(route)["method"] == "getVoteAccounts"
    assert body(route)["params"] == [{"votePubkey": "Vote"}]


@respx.mock
def test_is_blockhash_valid():
    route = mock_rpc({"context": {"slot": 1}, "value": True})
    with HeliusClient(api_key="test") as client:
        assert client.is_blockhash_valid("hash") == ({"slot": 1}, True)
    assert body(route)["method"] == "isBlockhashValid"
    assert body(route)["params"] == ["hash"]


@respx.mock
def test_request_airdrop():
    route = mock_rpc("sig")
    with HeliusClient(api_key="test") as client:
        assert client.request_airdrop("Pubkey", 1, commitment="confirmed") == "sig"
    assert body(route)["method"] == "requestAirdrop"
    assert body(route)["params"] == ["Pubkey", 1, {"commitment": "confirmed"}]


@respx.mock
def test_minimum_ledger_slot():
    route = mock_rpc(1)
    with HeliusClient(api_key="test") as client:
        assert client.minimum_ledger_slot() == 1
    assert body(route)["method"] == "minimumLedgerSlot"
