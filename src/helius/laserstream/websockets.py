import json
from os import environ
from typing import Annotated, Generator, Literal, TypedDict

import httpx
from dotenv import dotenv_values
from pydantic import AliasGenerator, BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from websockets.sync.client import connect

from helius.rpc import JsonRpcRequest


class Notification(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))


class TransactionNotification(Notification):
    transaction: dict
    signature: str
    slot: int


class AccountNotification(Notification):
    lamports: int
    owner: str
    data: list | dict | str
    executable: bool
    rent_epoch: int
    space: int | None = None


class BlockNotification(Notification):
    slot: int
    err: dict | None
    block: dict | None


class LogsNotification(Notification):
    signature: str
    err: dict | str | None
    logs: list[str]


class ProgramNotification(Notification):
    pubkey: str
    account: AccountNotification


class RootNotification(Notification):
    root: int

    @model_validator(mode="before")
    @classmethod
    def wrap_scalar(cls, data):
        if not isinstance(data, dict):
            return {"root": data}
        return data


class SignatureNotification(Notification):
    value: dict[str, None | str]

    @model_validator(mode="before")
    @classmethod
    def wrap_value(cls, data):
        return {"value": data}


class SlotNotification(Notification):
    parent: int
    root: int
    slot: int


class SlotsUpdatesNotification(Notification):
    err: str | None = None
    parent: int | None = None
    slot: int
    stats: dict[str, int] | None = None
    timestamp: int
    type: Literal[
        "firstShredReceived",
        "completed",
        "createdBank",
        "frozen",
        "dead",
        "optimisticConfirmation",
        "root",
    ]


class VoteNotification(Notification):
    hash: str
    slots: list[int]
    timestamp: int | None
    signature: str
    vote_pubkey: str


class WebSocketClient:
    class MentionsFilter(TypedDict):
        mentions: Annotated[list[str], Field(min_length=1, max_length=1)]

    class BlockMentionsFilter(TypedDict):
        mentionsAccountOrProgram: str

    class MemcmpFilter(TypedDict):
        offset: int
        bytes: str

    class DataSizeFilter(TypedDict):
        dataSize: int

    MODELS = {
        "transactionNotification": TransactionNotification,
        "accountNotification": AccountNotification,
        "blockNotification": BlockNotification,
        "logsNotification": LogsNotification,
        "programNotification": ProgramNotification,
        "rootNotification": RootNotification,
        "signatureNotification": SignatureNotification,
        "slotNotification": SlotNotification,
        "slotsUpdatesNotification": SlotsUpdatesNotification,
        "voteNotification": VoteNotification,
    }

    def __init__(
        self,
        *,
        base_url="wss://mainnet.helius-rpc.com",
        api_key: str | None = None,
        proxy: str | None = None,
    ):

        base_url = base_url
        api_key = (
            api_key
            or environ.get("HELIUS_API_KEY")
            or dotenv_values().get("HELIUS_API_KEY")
            or None
        )
        if not api_key:
            raise ValueError("No API key provided.")
        uri = httpx.URL(base_url).copy_with(path="/", params={"api-key": api_key})
        self._websocket = connect(str(uri), proxy=proxy)

    def close(self):
        self._websocket.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _send(self, request) -> dict:
        self._websocket.send(json.dumps(request))
        return json.loads(self._websocket.recv())

    def _recv(self):
        response = self._websocket.recv()
        return json.loads(response)

    def _unsubscribe(self, subscription_type, subscription) -> bool:
        request = (
            JsonRpcRequest(method=f"{subscription_type}Unsubscribe")
            .add(subscription)
            .build()
        )
        response = self._send(request)
        return response["result"]

    def transaction_subscribe(
        self,
        *,
        vote: bool | None = None,
        failed: bool | None = None,
        signature: str | None = None,
        account_include: list[str] | None = None,
        account_exclude: list[str] | None = None,
        account_required: list[str] | None = None,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        encoding: Literal["base58", "base64", "jsonParsed"] | None = None,
        transaction_details: (
            Literal["full", "signatures", "accounts", "none"] | None
        ) = None,
        show_rewards: bool | None = None,
        max_supported_transaction_version: int | None = None,
    ) -> int:
        if max_supported_transaction_version is None and transaction_details in [
            "accounts",
            "full",
        ]:
            raise ValueError(
                'max_supported_transaction_version is required when transaction_details is set to "accounts" or "full".'
            )
        filter = {
            key: value
            for key, value in {
                "vote": vote,
                "failed": failed,
                "signature": signature,
                "accountInclude": account_include,
                "accountExclude": account_exclude,
                "accountRequired": account_required,
            }.items()
            if value is not None
        }
        request = (
            JsonRpcRequest(method="transactionSubscribe")
            .add(filter if filter else None)
            .set("commitment", commitment)
            .set("encoding", encoding)
            .set("transactionDetails", transaction_details)
            .set("showRewards", show_rewards)
            .set("maxSupportedTransactionVersion", max_supported_transaction_version)
            .build()
        )
        response = self._send(request)
        subscription = response["result"]
        return subscription

    def account_subscribe(
        self,
        *,
        pubkey: str,
        encoding: Literal["base58", "base64", "base64+zstd", "jsonParsed"]
        | None = None,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ) -> int:
        request = (
            JsonRpcRequest(method="accountSubscribe")
            .add(pubkey)
            .set("commitment", commitment)
            .set("encoding", encoding)
            .build()
        )
        response = self._send(request)
        subscription = response["result"]
        return subscription

    def block_subscribe(
        self,
        *,
        filter: Literal["all"] | BlockMentionsFilter,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        encoding: Literal["base58", "base64", "base64+zstd", "jsonParsed"]
        | None = None,
        transaction_details: (
            Literal["full", "signatures", "accounts", "none"] | None
        ) = None,
        max_supported_transaction_version: int | None = None,
        show_rewards: bool | None = None,
    ) -> int:
        request = (
            JsonRpcRequest(method="blockSubscribe")
            .add(filter)
            .set("commitment", commitment)
            .set("encoding", encoding)
            .set("transactionDetails", transaction_details)
            .set("maxSupportedTransactionVersion", max_supported_transaction_version)
            .set("showRewards", show_rewards)
            .build()
        )
        response = self._send(request)
        subscription = response["result"]
        return subscription

    def logs_subscribe(
        self,
        *,
        filter: Literal["all", "allWithVotes"] | MentionsFilter,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ):
        request = (
            JsonRpcRequest(method="logsSubscribe")
            .add(filter)
            .set("commitment", commitment)
            .build()
        )
        response = self._send(request)
        subscription = response["result"]
        return subscription

    def program_subscribe(
        self,
        *,
        program_id: str,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        encoding: Literal["base58", "base64", "base64+zstd", "jsonParsed"]
        | None = None,
        filters: list[MemcmpFilter | DataSizeFilter] | None = None,
    ) -> int:
        request = (
            JsonRpcRequest(method="programSubscribe")
            .add(program_id)
            .set("commitment", commitment)
            .set("encoding", encoding)
            .set("filters", filters)
            .build()
        )
        response = self._send(request)
        subscription = response["result"]
        return subscription

    def root_subscribe(self) -> int:
        request = JsonRpcRequest(method="rootSubscribe").build()
        response = self._send(request)
        subscription = response["result"]
        return subscription

    def signature_subscribe(
        self,
        *,
        signature: str,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        enable_received_notification: bool | None = None,
    ) -> int:
        request = (
            JsonRpcRequest(method="signatureSubscribe")
            .add(signature)
            .set("commitment", commitment)
            .set("enableReceivedNotification", enable_received_notification)
            .build()
        )
        response = self._send(request)
        subscription = response["result"]
        return subscription

    def slot_subscribe(self) -> int:
        request = JsonRpcRequest(method="slotSubscribe").build()
        response = self._send(request)
        subscription = response["result"]
        return subscription

    def slots_updates_subscribe(self) -> int:
        request = JsonRpcRequest(method="slotsUpdatesSubscribe").build()
        response = self._send(request)
        subscription = response["result"]
        return subscription

    def vote_subscribe(self) -> int:
        request = JsonRpcRequest(method="voteSubscribe").build()
        response = self._send(request)
        subscription = response["result"]
        return subscription

    def transaction_unsubscribe(self, subscription) -> bool:
        return self._unsubscribe("transaction", subscription)

    def account_unsubscribe(self, subscription) -> bool:
        return self._unsubscribe("account", subscription)

    def block_unsubscribe(self, subscription) -> bool:
        return self._unsubscribe("block", subscription)

    def logs_unsubscribe(self, subscription) -> bool:
        return self._unsubscribe("logs", subscription)

    def program_unsubscribe(self, subscription) -> bool:
        return self._unsubscribe("program", subscription)

    def root_unsubscribe(self, subscription) -> bool:
        return self._unsubscribe("root", subscription)

    def signature_unsubscribe(self, subscription) -> bool:
        return self._unsubscribe("signature", subscription)

    def slot_unsubscribe(self, subscription) -> bool:
        return self._unsubscribe("slot", subscription)

    def slots_updates_unsubscribe(self, subscription) -> bool:
        return self._unsubscribe("slotsUpdates", subscription)

    def vote_unsubscribe(self, subscription) -> bool:
        return self._unsubscribe("vote", subscription)

    def receive(self) -> tuple[dict | None, Notification, int]:
        response = json.loads(self._websocket.recv())
        model = self.MODELS[response["method"]]
        result = response["params"]["result"]
        subscription = response["params"]["subscription"]
        if isinstance(result, dict):
            context = result.get("context")
            value = result.get("value")
        else:
            context, value = None, None
        if value is not None:
            notification = model.model_validate(value)
        else:
            notification = model.model_validate(result)
        return context, notification, subscription

    def listen(self) -> Generator[tuple[dict | None, Notification, int]]:
        while True:
            context, notification, subscription = self.receive()
            yield context, notification, subscription
