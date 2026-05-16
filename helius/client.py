from pprint import pprint
from typing import Annotated, Literal
import httpx
from dotenv import dotenv_values
from pydantic import BaseModel, Field, validate_call

from helius.models import AccountInfo, Block, BlockCommitment, TransactionSignature


class HeliusClient:
    # BUG: check which endpoints return meaningful data in context
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
    def get_account_info(
        self,
        public_key: str,
        commitment: Literal["finalized", "confirmed", "processed"] = "finalized",
        encoding: Literal["base58", "base64", "base64+zstd", "jsonParsed"] = "base64",
        data_slice_offset: int | None = None,
        data_slice_length: int | None = None,
        min_context_slot: int | None = None,
    ) -> AccountInfo | None:
        if data_slice_offset is not None and data_slice_length is not None:
            data_slice = {"offset": data_slice_offset, "length": data_slice_length}
        elif data_slice_offset is None and data_slice_length:
            data_slice = None
        else:
            raise ValueError(
                "Set both data_slice_length and data_slice_offset or neither."
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
                "params": [public_key, config] if config != {} else [public_key],
            },
        )
        response.raise_for_status()
        # BUG: handle helius errors that do not show by HTTP response code
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
                "params": [public_key, config] if config != {} else [public_key],
            },
        )
        response.raise_for_status()
        result = response.json()["result"]
        return result["value"]

    @validate_call
    def get_block(
        self,
        slot: int,
        commitment: Literal["finalized", "confirmed"] = "finalized",
        encoding: Literal["jsonParsed", "base58", "base64", "base64+std"] | None = None,
        transaction_details: Literal["full", "accounts", "signatures", "none"] = "full",
        rewards: bool = False,
        max_supported_transcation_version: int | None = None,
    ) -> Block | None:
        config = {
            key: value
            for key, value in {
                "commitment": commitment,
                "encoding": encoding,
                "transactionDetails": transaction_details,
                "rewards": rewards,
                "maxSupportedTransactionVersion": max_supported_transcation_version,
            }.items()
            if value is not None
        }
        response = httpx.post(
            f"https://mainnet.helius-rpc.com/?api-key={self.api_key}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBlock",
                "params": [slot, config] if config != {} else [slot],
            },
        )
        result = response.json()["result"]
        block = Block.model_validate(result)
        return block

    @validate_call
    def get_block_commitment(
        self,
        slot: int,
    ) -> BlockCommitment:
        response = httpx.post(
            f"https://mainnet.helius-rpc.com/?api-key={self.api_key}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBlockCommitment",
                "params": [slot],
            },
        )
        result = response.json()["result"]
        block_commitment = BlockCommitment.model_validate(result)
        return block_commitment

    @validate_call
    def get_block_height(
        self,
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
                "method": "getBlock",
                "params": [config] if config != {} else [],
            },
        )
        result = response.json()["result"]
        return result

    @validate_call
    def get_block_production(
        self,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        first_slot: int | None = None,
        last_slot: int | None = None,
        identity: str | None = None,
    ) -> tuple[dict, dict]:
        """
        At least one of identity or first_slot must be provided.
        """
        if (identity is None and first_slot is not None) or (
            identity is not None and first_slot is None
        ):
            raise ValueError("At least one of identity or first_slot must be provided.")
        if first_slot is None and last_slot is not None:
            raise ValueError("To set last_slot, first_slot is required.")
        if first_slot is None and last_slot is None:
            range = None
        elif first_slot is not None:
            range = {"firstSlot": first_slot}
            if last_slot is not None:
                range.update({"lastSlot": last_slot})
        else:
            raise ValueError("Set both first_slot or last_slot or neither.")
        params = {
            key: value
            for key, value in {
                "commitment": commitment,
                "range": range,
                "identity": identity,
            }.items()
            if value is not None
        }
        response = httpx.post(
            f"https://mainnet.helius-rpc.com/?api-key={self.api_key}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBlockProduction",
                "params": [params] if params != {} else [],
            },
        )
        result = response.json()["result"]
        context = result["context"]
        value = result["value"]
        return context, value

    @validate_call
    def get_blocks(
        self,
        start_slot: int,
        end_slot: int | None,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ) -> list[int]:
        """
        If not provided, the query will return blocks up to the latest confirmed slot from start_slot.
        The range between start_slot and end_slot (or latest slot if end_slot is omitted) must not exceed 500,000 slots.
        """
        params: list = [start_slot]
        if end_slot is not None:
            params.append(end_slot)
        if commitment is not None:
            params.append({"commitment": commitment})
        response = httpx.post(
            f"https://mainnet.helius-rpc.com/?api-key={self.api_key}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBlock",
                "params": params,
            },
        )
        result = response.json()["result"]
        return result

    @validate_call
    def get_blocks_with_limit(
        self,
        start_slot: int,
        limit: int,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ) -> list[int]:
        params: list = [start_slot, limit]
        if commitment is not None:
            params.append({"commitment": commitment})
        response = httpx.post(
            f"https://mainnet.helius-rpc.com/?api-key={self.api_key}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBlockWithLimit",
                "params": params,
            },
        )
        result = response.json()["result"]
        return result

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
                "params": [address, options] if options != {} else [address],
            },
        )
        response.raise_for_status()
        transaction_signatures: list[TransactionSignature] = []
        result = response.json()["result"]
        for i in result:
            transaction_signature = TransactionSignature.model_validate(i)
            transaction_signatures.append(transaction_signature)
        return transaction_signatures
