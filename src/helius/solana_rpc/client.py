from os import environ
from typing import Annotated, Literal

import httpx
from dotenv import dotenv_values
from pydantic import Field, TypeAdapter, validate_call

from helius.solana_rpc.models import (
    Account,
    Block,
    BlockCommitment,
    ClusterNode,
    EpochInfo,
    EpochSchedule,
    InflationGovernor,
    InflationRate,
    InflationReward,
    LamportAccount,
    PerformanceSample,
    SignatureStatus,
    Supply,
    TokenAccount,
    TokenAccountBalance,
    TokenSupply,
    Transaction,
    TransactionSignature,
    VotingAccount,
)
from helius.solana_rpc.rpc_request import RpcRequest


# TODO: Use Pydantic typed dict where useful
class SolanaRpcClient:
    def __init__(
        self,
        *,
        base_url: str = "https://mainnet.helius-rpc.com",
        api_key: str | None = None,
    ) -> None:
        base_url = base_url
        api_key = (
            api_key
            or environ.get("HELIUS_API_KEY")
            or dotenv_values().get("HELIUS_API_KEY")
            or None
        )
        if not api_key:
            raise ValueError("No API key provided.")
        self._client = httpx.Client(
            base_url=base_url,
            params={"api-key": api_key},
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def close(self) -> None:
        self._client.close()

    def _send(self, json: dict, method="POST", url="/") -> dict:
        response = self._client.request(method=method, url=url, json=json)
        response.raise_for_status()
        return response.json()

    def get_account_info(
        self,
        *,
        public_key: str,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        encoding: (
            Literal["base58", "base64", "base64+zstd", "jsonParsed"] | None
        ) = None,
        data_slice_offset: int | None = None,
        data_slice_length: int | None = None,
        min_context_slot: int | None = None,
    ) -> tuple[dict, Account | None]:
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
                    if data_slice_offset is not None
                    else None
                ),
            )
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        value = response["result"]["value"]
        account_info = Account.model_validate(value) if value is not None else None
        return context, account_info

    def get_balance(
        self,
        *,
        public_key: str,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        min_context_slot: int | None = None,
    ) -> tuple[dict, int]:
        request = (
            RpcRequest(method="getBalance")
            .add(public_key)
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        value = response["result"]["value"]
        return context, value

    def get_block(
        self,
        *,
        slot: int,
        commitment: Literal["finalized", "confirmed"] | None = None,
        encoding: Literal["jsonParsed", "base58", "base64", "base64+std"] | None = None,
        transaction_details: (
            Literal["full", "accounts", "signatures", "none"] | None
        ) = None,
        rewards: bool | None = None,
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
        *,
        slot: int,
    ) -> BlockCommitment:
        request = RpcRequest(method="getBlockCommitment").add(slot).build()
        response = self._send(request)
        block_commitment = BlockCommitment.model_validate(response["result"])
        return block_commitment

    def get_block_height(
        self,
        *,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
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
        *,
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
            .set("range", range)
            .set("identity", identity)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        value = response["result"]["value"]
        return context, value

    def get_blocks(
        self,
        *,
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
        *,
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

    def get_block_time(self, *, slot: int) -> int | None:
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
        *,
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
        *,
        message: str,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
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
        *,
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

    def get_inflation_reward(
        self,
        *,
        addresses: list[str],
        commitment: Literal["finalized", "confirmed"] | None = None,
        epoch: int | None = None,
        min_context_slot: int | None = None,
    ) -> list[InflationReward | None]:
        request = (
            RpcRequest(method="getInflationReward")
            .add(addresses)
            .set("commitment", commitment)
            .set("epoch", epoch)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        result = response["result"]
        ta = TypeAdapter(list[InflationReward | None])
        return ta.validate_python(result)

    def get_largest_accounts(
        self,
        *,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        filter: Literal["circulating", "nonCirculating"] | None = None,
    ) -> tuple[dict, list[LamportAccount]]:
        request = (
            RpcRequest(method="getLargestAccounts")
            .set("commitment", commitment)
            .set("filter", filter)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        value = response["result"]["value"]
        ta = TypeAdapter(list[LamportAccount])
        largest_accounts = ta.validate_python(value)
        return context, largest_accounts

    def get_latest_blockhash(
        self,
        *,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        min_context_slot: int | None = None,
    ) -> tuple[dict, str, int]:
        request = (
            RpcRequest(method="getLatestBlockhash")
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        value = response["result"]["value"]
        blockhash = value["blockhash"]
        last_valid_block_height = value["lastValidBlockHeight"]
        return context, blockhash, last_valid_block_height

    def get_leader_schedule(
        self,
        *,
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
        *,
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
        *,
        pubkeys: list[str],
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        encoding: (
            Literal["base64", "base58", "base64+zstd", "jsonParsed"] | None
        ) = None,
        data_slice_offset: int | None = None,
        data_slice_length: int | None = None,
    ) -> tuple[dict, list[Account | None]]:
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
            .set(
                "dataSlice",
                (
                    {"offset": data_slice_offset, "length": data_slice_length}
                    if data_slice_offset is not None
                    else None
                ),
            )
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        value = response["result"]["value"]
        accounts = [Account.model_validate(i) if i is not None else None for i in value]
        return context, accounts

    @validate_call
    def get_program_accounts(
        self,
        *,
        program_id: str,
        commitment: Literal["confirmed", "finalized", "processed"] | None = None,
        min_context_slot: int | None = None,
        with_context: bool | None = None,
        encoding: (
            Literal["jsonParsed", "base58", "base64", "base64+zstd"] | None
        ) = None,
        data_slice_offset: int | None = None,
        data_slice_length: int | None = None,
        changed_since_slot: int | None = None,
        filters: list[dict] | None = None,
    ) -> list[tuple[str, Account]]:
        if (data_slice_offset is None) != (data_slice_length is None):
            raise ValueError(
                "Set both data_slice_length and data_slice_offset or neither."
            )
        request = (
            RpcRequest(method="getProgramAccounts")
            .add(program_id)
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .set("withContext", with_context)
            .set("encoding", encoding)
            .set(
                "dataSlice",
                (
                    {"offset": data_slice_offset, "length": data_slice_length}
                    if data_slice_offset is not None
                    else None
                ),
            )
            .set("changedSinceSlot", changed_since_slot)
            .set("filters", filters)
            .build()
        )
        response = self._send(request)
        result = response["result"]
        return [(i["pubkey"], Account.model_validate(i["account"])) for i in result]

    def get_recent_performance_samples(
        self,
        *,
        limit: int | None = None,
    ) -> list[PerformanceSample]:
        request = RpcRequest(method="getRecentPerformanceSamples").add(limit).build()
        response = self._send(request)
        ta = TypeAdapter(list[PerformanceSample])
        return ta.validate_python(response["result"])

    def get_recent_prioritization_fees(
        self,
        *,
        locked_writable_accounts: list[str] | None = None,
    ) -> list[tuple[int, int]]:
        request = (
            RpcRequest(method="getRecentPrioritizationFees")
            .add(locked_writable_accounts)
            .build()
        )
        response = self._send(request)
        return [(i["slot"], i["prioritizationFee"]) for i in response["result"]]

    @validate_call
    def get_signatures_for_address(
        self,
        *,
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

    def get_signature_statuses(
        self,
        *,
        signatures: list[str],
        search_transaction_history: bool | None = None,
    ) -> tuple[dict, list[SignatureStatus | None]]:
        request = (
            RpcRequest(method="getSignatureStatuses")
            .add(signatures)
            .set("searchTransactionHistory", search_transaction_history)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        signature_statuses = [
            SignatureStatus.model_validate(value) if value is not None else value
            for value in response["result"]["value"]
        ]
        return context, signature_statuses

    def get_slot(
        self,
        *,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        min_context_slot: int | None = None,
    ) -> int:
        request = (
            RpcRequest(method="getSlot")
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        return response["result"]

    def get_slot_leader(
        self,
        *,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        min_context_slot: int | None = None,
    ) -> str:
        request = (
            RpcRequest(method="getSlotLeader")
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        return response["result"]

    @validate_call
    def get_slot_leaders(
        self,
        *,
        start_slot: int,
        limit: Annotated[int, Field(ge=1, le=5000)],
    ) -> list[str]:
        request = RpcRequest(method="getSlotLeaders").add(start_slot).add(limit).build()
        response = self._send(request)
        return response["result"]

    def get_stake_minimum_delegation(
        self,
        *,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ) -> tuple[dict, int]:
        request = (
            RpcRequest(method="getStakeMinimumDelegation")
            .set("commitment", commitment)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        value = response["result"]["value"]
        return context, value

    def get_supply(
        self,
        *,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        exclude_non_circulating_accounts_list: bool | None = None,
    ) -> tuple[dict, Supply]:
        request = (
            RpcRequest(method="getSupply")
            .set("commitment", commitment)
            .set(
                "excludeNonCirculatingAccountsList",
                exclude_non_circulating_accounts_list,
            )
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        supply = Supply.model_validate(response["result"]["value"])
        return context, supply

    # TODO: use getProgramAccountsV2 which supports pagination

    def get_token_account_balance(
        self,
        *,
        token_account: str,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ) -> tuple[dict, TokenAccountBalance]:
        request = (
            RpcRequest(method="getTokenAccountBalance")
            .add(token_account)
            .set("commitment", commitment)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        balance = TokenAccountBalance.model_validate(response["result"]["value"])
        return context, balance

    def get_token_accounts_by_delegate(
        self,
        *,
        delegate_pub_key: str,
        mint: str | None = None,
        program_id: str | None = None,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        encoding: (
            Literal["base58", "base64", "base64+zstd", "jsonParsed"] | None
        ) = None,
        data_slice_offset: int | None = None,
        data_slice_length: int | None = None,
        min_context_slot: int | None = None,
    ) -> tuple[dict, list[tuple[str, Account]]]:
        if (mint is None) == (program_id is None):
            raise ValueError("Provide exactly one of mint or program_id.")
        if (data_slice_offset is None) != (data_slice_length is None):
            raise ValueError(
                "Set both data_slice_offset and data_slice_length or neither."
            )
        if data_slice_offset is not None and encoding == "jsonParsed":
            raise ValueError(
                "dataSlice is only for bas58, bas64 and base64+zstd encodings."
            )
        filter = {"mint": mint} if mint is not None else {"programId": program_id}
        request = (
            RpcRequest(method="getTokenAccountsByDelegate")
            .add(delegate_pub_key)
            .add(filter)
            .set("commitment", commitment)
            .set("encoding", encoding)
            .set(
                "dataSlice",
                (
                    {"offset": data_slice_offset, "length": data_slice_length}
                    if data_slice_offset is not None
                    else None
                ),
            )
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        token_accounts = [
            (i["pubkey"], Account.model_validate(i["account"]))
            for i in response["result"]["value"]
        ]
        return context, token_accounts

    def get_token_accounts_by_owner(
        self,
        *,
        owner_pub_key: str,
        mint: str | None = None,
        program_id: str | None = None,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        encoding: (
            Literal["base58", "base64", "base64+zstd", "jsonParsed"] | None
        ) = None,
        data_slice_offset: int | None = None,
        data_slice_length: int | None = None,
        min_context_slot: int | None = None,
    ) -> tuple[dict, list[tuple[str, Account]]]:
        if (mint is None) == (program_id is None):
            raise ValueError("Provide exactly one of mint or program_id.")
        if (data_slice_offset is None) != (data_slice_length is None):
            raise ValueError(
                "Set both data_slice_offset and data_slice_length or neither."
            )
        if data_slice_offset is not None and encoding == "jsonParsed":
            raise ValueError(
                "dataSlice is only for bas58, bas64 and base64+zstd encodings."
            )
        filter = {"mint": mint} if mint is not None else {"programId": program_id}
        request = (
            RpcRequest(method="getTokenAccountsByOwner")
            .add(owner_pub_key)
            .add(filter)
            .set("commitment", commitment)
            .set("encoding", encoding)
            .set(
                "dataSlice",
                (
                    {"offset": data_slice_offset, "length": data_slice_length}
                    if data_slice_offset is not None
                    else None
                ),
            )
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        token_accounts = [
            (i["pubkey"], Account.model_validate(i["account"]))
            for i in response["result"]["value"]
        ]
        return context, token_accounts

    # TODO: use getTokenAccountsByOwnerV2 and do pagination

    def get_token_largest_accounts(
        self,
        *,
        mint: str,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ) -> tuple[dict, list[TokenAccount]]:
        request = (
            RpcRequest(method="getTokenLargestAccounts")
            .add(mint)
            .set("commitment", commitment)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        ta = TypeAdapter(list[TokenAccount])
        largest_accounts = ta.validate_python(response["result"]["value"])
        return context, largest_accounts

    def get_token_supply(
        self,
        *,
        mint_address: str,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ) -> tuple[dict, TokenSupply]:
        request = (
            RpcRequest(method="getTokenSupply")
            .add(mint_address)
            .set("commitment", commitment)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        token_supply = TokenSupply.model_validate(response["result"]["value"])
        return context, token_supply

    def get_transaction(
        self,
        *,
        transaction_signature: str,
        commitment: Literal["finalized", "confirmed"] | None = None,
        encoding: Literal["json", "jsonParsed", "base58", "base64"] | None = None,
        max_supported_transaction_version: int | None = None,
    ) -> Transaction:
        request = (
            RpcRequest(method="getTransaction")
            .add(transaction_signature)
            .set("commitment", commitment)
            .set("encoding", encoding)
            .set("maxSupportedTransactionVersion", max_supported_transaction_version)
            .build()
        )
        response = self._send(request)
        transaction = Transaction.model_validate(response["result"])
        return transaction

    def get_transaction_count(
        self,
        *,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        min_context_slot: int | None = None,
    ) -> int:
        request = (
            RpcRequest(method="getTransactionCount")
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        return response["result"]

    def get_version(self) -> tuple[str, int]:
        request = RpcRequest(method="getVersion").build()
        response = self._send(request)
        result = response["result"]
        return result["solana-core"], result["feature-set"]

    def get_vote_accounts(
        self,
        *,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        vote_pubkey: str | None = None,
        keep_unstaked_delinquents: bool | None = None,
        delinquent_slot_distance: int | None = None,
    ) -> tuple[list[VotingAccount], list[VotingAccount]]:
        request = (
            RpcRequest(method="getVoteAccounts")
            .set("commitment", commitment)
            .set("votePubkey", vote_pubkey)
            .set("keepUnstakedDelinquents", keep_unstaked_delinquents)
            .set("delinquentSlotDistance", delinquent_slot_distance)
            .build()
        )
        response = self._send(request)
        ta = TypeAdapter(list[VotingAccount])
        current = ta.validate_python(response["result"]["current"])
        delinquent = ta.validate_python(response["result"]["delinquent"])
        return current, delinquent

    def is_blockhash_valid(
        self,
        *,
        blockhash: str,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
        min_context_slot: int | None = None,
    ) -> tuple[dict, bool]:
        request = (
            RpcRequest(method="isBlockhashValid")
            .add(blockhash)
            .set("commitment", commitment)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        context = response["result"]["context"]
        value = response["result"]["value"]
        return context, value

    def minimum_ledger_slot(self) -> int:
        request = RpcRequest(method="minimumLedgerSlot").build()
        response = self._send(request)
        return response["result"]

    def request_airdrop(
        self,
        *,
        public_key: str,
        lamports: int,
        commitment: Literal["finalized", "confirmed", "processed"] | None = None,
    ) -> str:
        """
        Only available on Devnet and Testnet, not Mainnet Beta.
        """
        request = (
            RpcRequest(method="requestAirdrop")
            .add(public_key)
            .add(lamports)
            .set("commitment", commitment)
            .build()
        )
        response = self._send(request)
        return response["result"]

    def send_transaction(
        self,
        *,
        transaction: str,
        encoding: Literal["base58", "base64"] | None = None,
        skip_preflight: bool | None = None,
        preflight_commitment: (
            Literal["finalized", "confirmed", "processed"] | None
        ) = None,
        max_retries: int | None = None,
        min_context_slot: int | None = None,
    ) -> str:
        request = (
            RpcRequest(method="sendTransaction")
            .add(transaction)
            .set("encoding", encoding)
            .set("skipPreflight", skip_preflight)
            .set("preflightCommitment", preflight_commitment)
            .set("maxRetries", max_retries)
            .set("minContextSlot", min_context_slot)
            .build()
        )
        response = self._send(request)
        return response["result"]
