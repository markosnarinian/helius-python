import json
from os import environ
from typing import Annotated, Literal, TypedDict

import httpx
from dotenv import dotenv_values
from pydantic import BaseModel, Field, model_validator
from websockets.sync.client import connect

from helius.rpc import JsonRpcRequest


class Notification(BaseModel):
    pass


class LogsNotification(Notification):
    signature: str
    err: dict | str
    logs: list[str]


class TransactionNotification(Notification):
    transaction: dict
    signature: str
    slot: int


class RootNotification(Notification):
    root: int

    @model_validator(mode="before")
    @classmethod
    def wrap_scalar(cls, data):
        if not isinstance(data, dict):
            return {"a": data}
        return data


class WebSocketClient:
    class MentionsFilter(TypedDict):
        mentions: Annotated[list[str], Field(min_length=1, max_length=1)]

    MODELS = {
        "logsNotification": LogsNotification,
        "transactionNotification": TransactionNotification,
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

    def __exit__(self):
        self.close()

    def _send(self, request) -> dict:
        self._websocket.send(json.dumps(request))
        return json.loads(self._websocket.recv())

    def _recv(self):
        response = self._websocket.recv()
        return json.loads(response)

    def _unsubscribe(self, subscription, subscription_type) -> bool:
        request = (
            JsonRpcRequest(method=f"{subscription_type}Unsubscribe")
            .add(subscription)
            .build()
        )
        response = self._send(request)
        return response["result"]

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
        self._send(request)
        response = self._send(request)
        subscription = response["result"]
        return subscription

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

    def logs_unsubscribe(self, subscription) -> bool:
        return self._unsubscribe("logs", subscription)

    def transaction_unsubscribe(self, subscription):
        return self._unsubscribe("transaction", subscription)

    def receive(self):
        response = json.loads(self._websocket.recv())
        model = self.MODELS[response["method"]]
        result = response["result"]
        subscription = response["subscription"]
        context = result["context"] if "context" in result else None
        value = result["value"] if "value" in result else None
        if value is not None:
            notification = model.model_validate(value)
        else:
            notification = model.model_validate(result)
        return context, notification, subscription

    def listen(self):
        while True:
            notification = self.receive()
            yield notification
