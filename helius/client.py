from typing import Annotated, Literal
import httpx
from dotenv import dotenv_values
from pydantic import BaseModel, Field, validate_call


class TransactionSignature(BaseModel):
    signature: str
    slot: int
    err: dict | None
    memo: str | None
    blockTime: int | None
    confirmationStatus: str | None


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
                "min_context_slot": min_context_slot,
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
        signatures: list[TransactionSignature] = []
        for i in response.json()["result"]:
            signature = TransactionSignature.model_validate(i)
            signatures.append(signature)
        return signatures
