from typing import Annotated, Any, Literal

import httpx
from dotenv import dotenv_values
from pydantic import BaseModel, Field, TypeAdapter, validate_call

from helius.models import (
    Account,
    Block,
    BlockCommitment,
    ClusterNode,
    EpochInfo,
    EpochSchedule,
    InflationGovernor,
    InflationRate,
    LargestAccount,
    TransactionSignature,
)


class HeliusClient:
    # BUG: check which endpoints return meaningful data in context
    # BUG: handle helius errors that do not show by HTTP response code
    def __init__(
        self,
        *,
        base_url: str = "https://mainnet.helius-rpc.com",
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key or dotenv_values().get("HELIUS_API_KEY")
        if not self.api_key:
            raise ValueError("No API key provided.")
        self._client = httpx.Client(
            base_url=self.base_url,
            params={"api-key": self.api_key},
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._client.close()

    def __del__(self):
        self._client.close()

    def _send(self, json: dict, method="POST", url="/") -> dict:
        request = httpx.Request(method=method, url=url, json=json)
        response = self._client.send(request)
        response.raise_for_status()
        return response.json()

    def get_account_info(
        self,
        public_key: str,
        commitment: Literal["finalized", "confirmed", "processed"] = "finalized",
        encoding: Literal["base58", "base64", "base64+zstd", "jsonParsed"] = "base64",
        data_slice_offset: int | None = None,
        data_slice_length: int | None = None,
        min_context_slot: int | None = None,
    ) -> Account | None:
        if (data_slice_offset is None) != (data_slice_length is None):
            raise ValueError(
                "Set both data_slice_length and data_slice_offset or neither."
            )
        request = (
            RpcRequest(method="getAccountInfo")
            .add(public_key)
            .set("commitment", commitment)
            .set("encoding", encoding)
            .set(
                "dataSlice",
                (
                    {"offset": data_slice_offset, "length": data_slice_length}
                    if data_slice_offset is not None and data_slice_length is not None
                    else None
                ),
            )
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        account_info = Account.model_validate(response["result"])
        return account_info

    def get_balance(
        self,
        public_key: str,
        commitment: Literal["finalized", "confirmed", "processed"] = "finalized",
        min_context_slot: int | None = None,
    ) -> int:
        request = (
            RpcRequest(method="getBalance")
            .add(public_key)
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        return response["result"]["value"]

    def get_block(
        self,
        slot: int,
        commitment: Literal["finalized", "confirmed"] = "finalized",
        encoding: Literal["jsonParsed", "base58", "base64", "base64+std"] | None = None,
        transaction_details: Literal["full", "accounts", "signatures", "none"] = "full",
        rewards: bool = False,
        max_supported_transcation_version: int | None = None,
    ) -> Block | None:
        request = (
            RpcRequest(method="getBlock")
            .add(slot)
            .set("commitment", commitment)
            .set("encoding", encoding)
            .set("transactionDetails", transaction_details)
            .set("rewards", rewards)
            .set("maxSupportedTransactionVersion", max_supported_transcation_version)
            .build()
        )
        response = self._send(request)
        block = Block.model_validate(response["result"])
        return block

    def get_block_commitment(
        self,
        slot: int,
    ) -> BlockCommitment:
        request = RpcRequest(method="getBlockCommitment").add(slot).build()
        response = self._send(request)
        block_commitment = BlockCommitment.model_validate(response["result"])
        return block_commitment

    def get_block_height(
        self,
        commitment: Literal["finalized", "confirmed", "processed"] = "finalized",
        min_context_slot: int | None = None,
    ) -> int:
        request = (
            RpcRequest(method="getBlockHeight")
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        return response["result"]

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
        if first_slot is None:
            if identity is None:
                raise ValueError(
                    "At least one of identity or first_slot must be provided."
                )
            if last_slot is not None:
                raise ValueError("To set last_slot, first_slot is required.")
            if last_slot is None:
                range = None
        else:
            range = {"firstSlot": first_slot}
            if last_slot is not None:
                range.update({"lastSlot": last_slot})
        request = (
            RpcRequest(method="getBlockProduction")
            .set("commitment", commitment)
            .set("first_slot", first_slot)
            .set("lastSlot", last_slot)
            .set("identity", identity)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        value = response["result"]["value"]
        return context, value

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
        request = (
            RpcRequest(method="getBlocks")
            .add(start_slot)
            .add(end_slot)
            .set("commitment", commitment)
            .build()
        )
        response = self._send(request)
        return response["result"]

    def get_blocks_with_limit(
        self,
        start_slot: int,
        limit: int,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ) -> list[int]:
        request = (
            RpcRequest(method="getBlocksWithLimit")
            .add(start_slot)
            .add(limit)
            .set("commitment", commitment)
            .build()
        )
        response = self._send(request)
        return response["result"]

    def get_block_time(self, slot: int) -> int | None:
        request = RpcRequest(method="getBlockTime").add(slot).build()
        response = self._send(request)
        return response["result"]

    def get_cluster_nodes(self) -> list[ClusterNode]:
        request = RpcRequest(method="getClusterNodes").build()
        response = self._send(request)
        ta = TypeAdapter(list[ClusterNode])
        cluster_nodes = ta.validate_python(response["result"])
        return cluster_nodes

    def get_epoch_info(
        self,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        min_context_slot: int | None = None,
    ) -> EpochInfo:
        request = (
            RpcRequest(method="getEpochInfo")
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        epoch_info = EpochInfo.model_validate(response["result"])
        return epoch_info

    def get_epoch_schedule(self) -> EpochSchedule:
        request = RpcRequest(method="getEpochSchedule").build()
        response = self._send(request)
        epoch_schedule = EpochSchedule.model_validate(response["result"])
        return epoch_schedule

    def get_fee_for_message(
        self,
        message: str,
        commitment: Literal["finalized", "confirmed", "processed"] = "finalized",
        min_context_slot: int | None = None,
    ) -> tuple[dict, int | None]:
        request = (
            RpcRequest(method="getFeeForMessage")
            .add(message)
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        value = response["result"]["value"]
        return context, value

    def get_first_available_block(self) -> int:
        request = RpcRequest(method="getFirstAvailableBlock").build()
        response = self._send(request)
        return response["result"]

    def get_genesis_hash(self) -> str:
        request = RpcRequest(method="getGenesisHash").build()
        response = self._send(request)
        return response["result"]

    def get_health(self) -> bool:
        request = RpcRequest(method="getHealth").build()
        response = self._send(request)
        if "result" in response and response["result"] == "ok":
            return True
        else:
            return False

    def get_highest_snapshot_slot(self) -> dict:
        request = RpcRequest(method="getHighestSnapshotSlot").build()
        response = self._send(request)
        return response["result"]

    def get_identity(self) -> str:
        request = RpcRequest(method="getIdentity").build()
        response = self._send(request)
        identity = response["result"]["identity"]
        return identity

    def get_inflation_governor(
        self,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ) -> InflationGovernor:
        request = (
            RpcRequest(method="getInflationGovernor")
            .set("commitment", commitment)
            .build()
        )
        response = self._send(request)
        inflation_governor = InflationGovernor.model_validate(response["result"])
        return inflation_governor

    def get_inflation_rate(self) -> InflationRate:
        request = RpcRequest(method="getInflationRate").build()
        response = self._send(request)
        inflation_rate = InflationRate.model_validate(response["result"])
        return inflation_rate

    # TODO: getInflationReward

    def get_largest_accounts(
        self,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        filter: Literal["circulating", "nonCirculating"] | None = None,
    ) -> list[LargestAccount]:
        request = (
            RpcRequest(method="getLargestAccounts")
            .set("commitment", commitment)
            .set("filter", filter)
            .build()
        )
        response = self._send(request)
        value = response["result"]["value"]
        ta = TypeAdapter(list[LargestAccount])
        largest_accounts = ta.validate_python(value)
        return largest_accounts

    def get_latest_blockhash(
        self,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        min_context_slot: int | None = None,
    ) -> tuple[str, int]:
        request = (
            RpcRequest(method="getLatestBlockhash")
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        blockhash = response["result"]["blockhash"]
        last_valid_block_height = response["result"]["lastValidBlockHeight"]
        return (blockhash, last_valid_block_height)

    def get_leader_schedule(
        self,
        slot: int | None = None,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        identity: str | None = None,
    ) -> dict[str, list[int]] | None:
        request = (
            RpcRequest(method="getLeaderSchedule")
            .add(slot)
            .set("commitment", commitment)
            .set("identity", identity)
            .build()
        )
        response = self._send(request)
        result = response["result"]
        return result

    def get_max_retransmit_slot(self) -> int:
        request = RpcRequest(method="getMaxRetransmitSlot").build()
        response = self._send(request)
        result = response["result"]
        return result

    def get_max_shred_insert_slot(self) -> int:
        request = RpcRequest(method="getMaxShredInsertSlot").build()
        response = self._send(request)
        result = response["result"]
        return result

    def get_minimum_balance_for_rent_exemption(
        self,
        data_length: int,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ) -> int:
        request = (
            RpcRequest(method="getMinimumBalanceForRentExemption")
            .add(data_length)
            .set("commitment", commitment)
            .build()
        )
        response = self._send(request)
        result = response["result"]
        return result

    def get_multiple_accounts(
        self,
        pubkeys: list[str],
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        encoding: (
            Literal["base64", "base58", "base64+zstd", "jsonParsed"] | None
        ) = None,
        data_slice_offset: int | None = None,
        data_slice_length: int | None = None,
    ):
        if (data_slice_offset is None) != (data_slice_length is None):
            raise ValueError(
                "Set both data_slice_length and data_slice_offset or neither."
            )
        if (
            data_slice_length is not None
            and data_slice_offset is not None
            and encoding not in ["base58", "base64", "base64+zstd"]
        ):
            raise ValueError(
                "Data slice is only available for base58, base64, or base64+zstd encodings."
            )
        request = (
            RpcRequest(method="getMultipleAccounts")
            .add(pubkeys)
            .set("commitment", commitment)
            .set("encoding", encoding)
            .set("data_slice_offset", data_slice_offset)
            .set("data_slice_length", data_slice_length)
            .build()
        )
        response = self._send(request)
        value = response["result"]["value"]
        accounts = [Account.model_validate(i) for i in value]
        return accounts

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
        request = (
            RpcRequest(method="getSignaturesForAddress")
            .add(address)
            .set("limit", limit)
            .set("before", before)
            .set("until", until)
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        ta = TypeAdapter(list[TransactionSignature])
        transaction_signatures = ta.validate_python(response["result"])
        return transaction_signatures


class RpcRequest:
    class Request(BaseModel):
        jsonrpc: str
        method: str
        params: list[Any] | None = None
        id: str | int | None

    def __init__(
        self,
        *,
        jsonrpc: str = "2.0",
        method: str,
        id: str | int | None = 1,
    ):
        self._jsonrpc = jsonrpc
        self._method = method
        self._id = id
        self._positional: list[Any] = []
        self._config: dict[str, Any] = {}

    def add(self, value, can_be_none: bool = False):
        if value is not None:
            self._positional.append(value)
        elif can_be_none:
            self._positional.append(None)
        return self

    def set(self, key: str, value, can_be_none: bool = False):
        if value is not None:
            self._config.update({key: value})
        elif can_be_none:
            self._config.update({key: None})
        return self

    def build(self):
        params = self._positional if self._positional else []
        if self._config:
            params.append(self._config)
        request = {
            "method": self._method,
            "id": self._id,
        }
        if params:
            request.update({"params": params})
        return self.Request(**request).model_dump()
