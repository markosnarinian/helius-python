from helius.models import (
    Account,
    Block,
    BlockCommitment,
    ClusterNode,
    EpochInfo,
    EpochSchedule,
    InflationGovernor,
    InflationRate,
    LamportAccount,
    PerformanceSample,
    Rewards,
    SignatureStatus,
    Supply,
    TokenAccount,
    TokenAccountBalance,
    TokenSupply,
    Transaction,
    TransactionMetadata,
    TransactionSignature,
    VotingAccount,
)


def test_account_validates_camel_case_aliases():
    account = Account.model_validate(
        {
            "lamports": 5_000_000_000,
            "owner": "11111111111111111111111111111111",
            "data": ["", "base64"],
            "executable": False,
            "rentEpoch": 18_446_744_073_709_551_615,
            "space": 0,
        }
    )

    assert account.rent_epoch == 18_446_744_073_709_551_615


def test_rewards_validates_camel_case_aliases():
    rewards = Rewards.model_validate(
        {
            "pubkey": "Vote11111111111111111111111111111111111",
            "lamports": 1,
            "postBalance": 2,
            "rewardType": "Fee",
            "commission": 5,
        }
    )

    assert rewards.post_balance == 2
    assert rewards.reward_type == "Fee"


def test_block_validates_nested_rewards_and_aliases():
    block = Block.model_validate(
        {
            "blockhash": "hash",
            "previousBlockhash": "prev",
            "parentSlot": 1,
            "transactions": [],
            "blockTime": 123,
            "blockHeight": 456,
            "rewards": [
                {
                    "pubkey": "Vote11111111111111111111111111111111111",
                    "lamports": 1,
                    "postBalance": 2,
                    "rewardType": "Fee",
                    "commission": 5,
                }
            ],
        }
    )

    assert block.previous_blockhash == "prev"
    assert block.rewards[0].post_balance == 2


def test_block_commitment_validates_fixture():
    commitment = BlockCommitment.model_validate(
        {"commitment": [1, 2, 3], "totalStake": 6}
    )

    assert commitment.total_stake == 6


def test_cluster_node_validates_aliases():
    node = ClusterNode.model_validate(
        {
            "pubkey": "Node11111111111111111111111111111111111",
            "gossip": None,
            "tpu": None,
            "rpc": None,
            "version": "1.18.0",
            "featureSet": 1,
            "shredVersion": 2,
        }
    )

    assert node.feature_set == 1
    assert node.shred_version == 2


def test_epoch_info_validates_aliases():
    info = EpochInfo.model_validate(
        {
            "absoluteSlot": 10,
            "blockHeight": 9,
            "epoch": 1,
            "slotIndex": 2,
            "slotsInEpoch": 32,
            "transactionCount": 100,
        }
    )

    assert info.absolute_slot == 10
    assert info.transaction_count == 100


def test_epoch_schedule_validates_aliases():
    schedule = EpochSchedule.model_validate(
        {
            "slotsPerEpoch": 32,
            "leaderScheduleSlotOffset": 8,
            "warmup": True,
            "firstNormalEpoch": 1,
            "firstNormalSlot": 32,
        }
    )

    assert schedule.slots_per_epoch == 32
    assert schedule.leader_schedule_slot_offset == 8
    assert schedule.first_normal_slot == 32


def test_inflation_governor_validates_aliases():
    governor = InflationGovernor.model_validate(
        {
            "initial": 0.08,
            "terminal": 0.015,
            "taper": 0.15,
            "foundation": 0.05,
            "foundationTerm": 7.0,
        }
    )

    assert governor.foundation_term == 7.0


def test_inflation_rate_validates_fixture():
    rate = InflationRate.model_validate(
        {"total": 0.149, "validator": 0.148, "foundation": 0.001, "epoch": 100}
    )

    assert rate.foundation == 0.001


def test_performance_sample_validates_aliases():
    sample = PerformanceSample.model_validate(
        {
            "slot": 1,
            "numTransactions": 10,
            "numNonVoteTransactions": 7,
            "samplePeriodSecs": 60,
            "numSlots": 4,
        }
    )

    assert sample.num_non_vote_transactions == 7
    assert sample.sample_period_secs == 60


def test_lamport_account_validates_fixture():
    account = LamportAccount.model_validate({"address": "Acct", "lamports": 42})

    assert account.lamports == 42


def test_signature_status_validates_aliases():
    status = SignatureStatus.model_validate(
        {"slot": 1, "confirmations": None, "err": None, "confirmationStatus": "finalized"}
    )

    assert status.confirmation_status == "finalized"


def test_transaction_signature_validates_aliases():
    signature = TransactionSignature.model_validate(
        {
            "signature": "sig",
            "slot": 1,
            "err": None,
            "memo": None,
            "blockTime": 123,
            "confirmationStatus": "confirmed",
        }
    )

    assert signature.block_time == 123
    assert signature.confirmation_status == "confirmed"


def test_supply_validates_camel_case_aliases():
    supply = Supply.model_validate(
        {
            "total": 100,
            "circulating": 80,
            "nonCirculating": 20,
            "nonCirculatingAccounts": ["Account111111111111111111111111111111111"],
        }
    )

    assert supply.non_circulating == 20
    assert supply.non_circulating_accounts == [
        "Account111111111111111111111111111111111"
    ]


def test_token_account_balance_validates_aliases():
    balance = TokenAccountBalance.model_validate(
        {"amount": "100", "decimals": 2, "uiAmount": 1.0, "uiAmountString": "1"}
    )

    assert balance.ui_amount == 1.0
    assert balance.ui_amount_string == "1"


def test_token_account_validates_aliases():
    account = TokenAccount.model_validate(
        {
            "address": "TokenAcct",
            "amount": "100",
            "decimals": 2,
            "uiAmount": 1.0,
            "uiAmountString": "1",
        }
    )

    assert account.ui_amount_string == "1"


def test_token_supply_validates_aliases():
    supply = TokenSupply.model_validate(
        {"amount": "100", "decimals": 2, "uiAmount": 1.0, "uiAmountString": "1"}
    )

    assert supply.ui_amount == 1.0


def test_voting_account_validates_aliases():
    account = VotingAccount.model_validate(
        {
            "votePubkey": "Vote11111111111111111111111111111111111",
            "nodePubkey": "Node11111111111111111111111111111111111",
            "activatedStake": 100,
            "epochVoteAccount": True,
            "commission": 5,
            "lastVote": 10,
            "rootSlot": 9,
            "epochCredits": [[1, 2, 3]],
        }
    )

    assert account.vote_pubkey.startswith("Vote")
    assert account.epoch_credits == [[1, 2, 3]]


def test_transaction_metadata_validates_aliases():
    metadata = TransactionMetadata.model_validate(
        {
            "err": None,
            "fee": 5000,
            "preBalances": [1],
            "postBalances": [2],
            "preTokenBalances": None,
            "postTokenBalances": None,
            "innerInstructions": None,
            "logMessages": ["ok"],
        }
    )

    assert metadata.pre_balances == [1]
    assert metadata.log_messages == ["ok"]


def test_transaction_validates_nested_metadata_and_aliases():
    transaction = Transaction.model_validate(
        {
            "slot": 1,
            "blockTime": 123,
            "meta": {
                "err": None,
                "fee": 5000,
                "preBalances": [1],
                "postBalances": [2],
                "preTokenBalances": None,
                "postTokenBalances": None,
                "innerInstructions": None,
                "logMessages": ["ok"],
            },
            "transaction": {"signatures": ["sig"]},
            "version": "legacy",
        }
    )

    assert transaction.block_time == 123
    assert transaction.meta.fee == 5000
