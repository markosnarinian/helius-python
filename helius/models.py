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
