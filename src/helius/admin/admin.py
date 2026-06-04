from os import environ

import httpx
from dotenv import dotenv_values
from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BillingCycle(BaseModel):
    start: str
    end: str


class SubscriptionDetails(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    billing_cycle: BillingCycle
    credits_limit: float
    plan: str


class Usage(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    api: int
    archival: int
    das: int
    grpc: int
    grpc_geyser: int
    photon: int
    rpc: int
    stream: int
    webhook: int
    websocket: int


class ProjectUsage(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))

    credits_remaining: float
    credits_used: float
    prepaid_credits_remaining: float
    prepaid_credits_used: float
    subscription_details: SubscriptionDetails
    usage: Usage


class AccountManagementClient:
    def __init__(
        self,
        *,
        base_url: str = "https://admin-api.helius.xyz/v0/admin/projects/{id}/usage",
        api_key: str | None = None,
        project_id: str | None = None,
        headers: dict[str, str] | None = None,
        proxy: str | None = None,
    ) -> None:
        base_url = base_url
        api_key = (
            api_key
            or environ.get("HELIUS_API_KEY")
            or dotenv_values().get("HELIUS_API_KEY")
            or None
        )
        self.project_id = project_id
        client_options: dict = {
            "base_url": base_url,
            "headers": headers,
            "proxy": proxy,
        }
        if api_key is not None:
            client_options.update({"params": {"api-key": api_key}})
        self._client = httpx.Client(**client_options)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def close(self) -> None:
        self._client.close()

    def get_project_usage(self, project_id: str | None = None) -> ProjectUsage:
        project_id = project_id or self.project_id or None
        if project_id is None:
            raise ValueError("No project ID provided.")
        response = self._client.request(
            method="GET", url="/", params={"id": project_id}
        )
        response.raise_for_status()
        return ProjectUsage.model_validate(response.json())
