from pydantic import BaseModel


class TransactionSignature(BaseModel):
    signature: str
    slot: int
    err: dict | None
    memo: str | None
    blockTime: int | None
    confirmationStatus: str | None


class AccountInfo(BaseModel):
    lamports: int
    owner: str
    data: list | dict | str
    executable: bool
    rentEpoch: int
    space: int | None
