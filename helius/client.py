from typing import Annotated, Literal
import httpx
from dotenv import dotenv_values
from pydantic import BaseModel, Field, validate_call

from helius.models import AccountInfo, TransactionSignature


class HeliusClient:
    # TODO: mainnet/devnet via configurable rpc_url
    def __init__(self, api_key: str | None = None) -> None:
        if api_key is not None:
            self.api_key = api_key
        else:
            config = dotenv_values()
            if "HELIUS_API_KEY" not in config or config["HELIUS_API_KEY"] is None:
                raise ValueError("No API key provided.")
            self.api_key = config["HELIUS_API_KEY"]

    @validate_call
    def get_signatures_for_address(
        self,
        address: str,
        limit: Annotated[int, Field(ge=1, le=1000)] = 1000,
        before: str | None = None,
        until: str | None = None,
        commitment: Literal["finalized", "confirmed"] | None = None,
        min_context_slot: int | None = None,
    ) -> list[TransactionSignature]:
        options = {
            key: value
            for key, value in {
                "limit": limit,
                "before": before,
                "until": until,
                "commitment": commitment,
                "minContextSlot": min_context_slot,
            }.items()
            if value is not None
        }
        response = httpx.post(
            f"https://mainnet.helius-rpc.com/?api-key={self.api_key}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [address, options],
            },
        )
        response.raise_for_status()
        transaction_signatures: list[TransactionSignature] = []
        result = response.json()["result"]
        for i in result:
            transaction_signature = TransactionSignature.model_validate(i)
            transaction_signatures.append(transaction_signature)
        return transaction_signatures

    @validate_call
    def get_account_info(
        self,
        public_key: str,
        commitment: Literal["finalized", "confirmed", "processed"] = "finalized",
        encoding: Literal["base58", "base64", "base64+zstd", "jsonParsed"] = "base64",
        data_slice_offset: int | None = None,
        data_slice_length: int | None = None,
        min_context_slot: int | None = None,
    ) -> AccountInfo | None:
        data_slice = (
            {"offset": data_slice_offset, "length": data_slice_length}
            if data_slice_offset is not None and data_slice_length is not None
            else None
        )
        config = {
            key: value
            for key, value in {
                "commitment": commitment,
                "encoding": encoding,
                "dataSlice": data_slice,
                "minContextSlot": min_context_slot,
            }.items()
            if value is not None
        }
        response = httpx.post(
            f"https://mainnet.helius-rpc.com/?api-key={self.api_key}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    public_key,
                    config,
                ],
            },
        )
        response.raise_for_status()
        result = response.json()["result"]
        account_info = AccountInfo.model_validate(result)
        return account_info

    @validate_call
    def get_balance(
        self,
        public_key: str,
        commitment: Literal["finalized", "confirmed", "processed"] = "finalized",
        min_context_slot: int | None = None,
    ) -> int:
        config = {
            key: value
            for key, value in {
                "commitment": commitment,
                "minContextSlot": min_context_slot,
            }.items()
            if value is not None
        }
        response = httpx.post(
            f"https://mainnet.helius-rpc.com/?api-key={self.api_key}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [public_key, config],
            },
        )
        response.raise_for_status()
        result = response.json()["result"]
        return result["value"]
