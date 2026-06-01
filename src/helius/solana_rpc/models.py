from sys import stderr
from turtle import st
from typing import Literal, TypedDict

from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

# TODO: Improve camelCase <-> snake_case


class Account(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    lamports: int
    owner: str
    data: list | dict | str
    executable: bool
    rent_epoch: int
    space: int | None = None


class ProgramAccount(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    pubkey: str
    account: Account


class Rewards(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    pubkey: str
    lamports: int
    post_balance: int
    reward_type: str
    commission: int


class Block(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    blockhash: str
    previous_blockhash: str
    parent_slot: int
    transactions: list[dict]
    block_time: int | None
    block_height: int | None
    rewards: list[Rewards] | None = None


class BlockCommitment(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    commitment: list[int] | None
    total_stake: int


class ClusterNode(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    pubkey: str
    gossip: str | None
    tpu: str | None
    rpc: str | None
    version: str | None
    feature_set: int | None
    shred_version: int | None


class EpochInfo(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    absolute_slot: int
    block_height: int
    epoch: int
    slot_index: int
    slots_in_epoch: int
    transaction_count: int


class EpochSchedule(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    slots_per_epoch: int
    leader_schedule_slot_offset: int
    warmup: bool
    first_normal_epoch: int
    first_normal_slot: int


class InflationGovernor(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    initial: float
    terminal: float
    taper: float
    foundation: float
    foundation_term: float


class InflationRate(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    total: float
    validator: float
    foundation: float
    epoch: int


class InflationReward(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    epoch: int
    effective_slot: int
    amount: int
    post_balance: int
    commission: int | None


class PerformanceSample(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    slot: int
    num_transactions: int
    num_non_vote_transactions: int
    sample_period_secs: int
    num_slots: int


class LamportAccount(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    address: str
    lamports: int


class SignatureStatus(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    slot: int
    confirmations: int | None
    err: dict | None
    confirmation_status: str | None


class TransactionSignature(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    signature: str
    slot: int
    err: dict | None
    memo: str | None
    block_time: int | None
    confirmation_status: str | None


class Supply(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    total: int
    circulating: int
    non_circulating: int
    non_circulating_accounts: list[str] | None = None


class TokenAccountBalance(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    amount: str
    decimals: int
    ui_amount: float | None
    ui_amount_string: str


class TokenAccount(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    address: str
    amount: str
    decimals: int
    ui_amount: float | None
    ui_amount_string: str


class TokenSupply(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    amount: str
    decimals: int
    ui_amount: float | None
    ui_amount_string: str


class VotingAccount(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    vote_pubkey: str
    node_pubkey: str
    activated_stake: int
    epoch_vote_account: bool
    commission: int
    last_vote: int
    root_slot: int
    epoch_credits: list[list[int]]


class TransactionMetadata(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    err: dict | None
    fee: int
    pre_balances: list[int]
    post_balances: list[int]
    pre_token_balances: list[dict] | None
    post_token_balances: list[dict] | None
    inner_instructions: list[dict] | None
    log_messages: list[str] | None


class Transaction(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    slot: int
    block_time: int | None
    meta: TransactionMetadata | None
    transaction: dict | list
    version: Literal["legacy"] | int | None = None


class RangeFilter(TypedDict, total=False):
    gt: int
    gte: int
    lt: int
    lte: int


class ComparisonFilter(TypedDict, total=False):
    gte: int
    gt: int
    lte: int
    lt: int
    eq: int


TokenTransferFilter = TypedDict(
    "TokenTransferFilter",
    {
        "with": str,
        "direction": Literal["in", "out", "any"],
        "mint": str,
        "amount": RangeFilter,
    },
    total=False,
)


class TransactionFilters(TypedDict, total=False):
    slot: RangeFilter
    blockTime: ComparisonFilter
    signature: RangeFilter
    status: Literal["succeeded", "failed", "any"]
    tokenAccounts: Literal["none", "balanceChanged", "all"]
    tokenTransfer: TokenTransferFilter


class TransferFilters(TypedDict, total=False):
    amount: RangeFilter
    blockTime: RangeFilter
    slot: RangeFilter


class Transfer(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    signature: str
    slot: int
    block_time: int
    type: Literal[
        "transfer",
        "mint",
        "burn",
        "wrap",
        "unwrap",
        "chnageOwner",
        "withdrawWithheldFee",
    ]
    from_user_account: str | None
    to_user_account: str | None
    mint: str
    amount: str
    decimals: int
    ui_amount: str
    confirmation_status: Literal["finalized", "confirmed"]
    transaction_idx: int
    instruction_idx: int
    inner_instruction_idx: int
    from_token_account: str
    to_token_account: str
    fee_amount: str
    fee_ui_amount: str


class TransactionSignaturesDetail(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    signature: str
    slot: str
    transaction_index: str
    err: dict
    memo: str | None
    block_time: int | None
    confirmation_status: int | None


class TransactionFullDetail(BaseModel):
    slot: int
    transaction_index: int
    transaction: dict
    meta: dict | list
    block_time: int | None
