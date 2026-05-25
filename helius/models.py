from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class TransactionSignature(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    signature: str
    slot: int
    err: dict | None
    memo: str | None
    block_time: int | None
    confirmation_status: str | None


class AccountInfo(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    lamports: int
    owner: str
    data: list | dict | str
    executable: bool
    rent_epoch: int
    space: int | None = None


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
    loader_schedule_slot_offset: int
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
    foudnation: float
    epoch: int


# TODO: consider creating an account details composite model
# HACK: Simply return a tuple
class LargestAccount(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    address: str
    lamports: int
