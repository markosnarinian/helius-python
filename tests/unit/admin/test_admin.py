import httpx
import pytest
import respx

from helius.admin import AccountManagementClient, ProjectUsage

PROJECT_USAGE_RESPONSE = {
    "creditsRemaining": 487500,
    "creditsUsed": 12500,
    "prepaidCreditsRemaining": 50000,
    "prepaidCreditsUsed": 0,
    "subscriptionDetails": {
        "billingCycle": {"start": "2026-04-01", "end": "2026-05-01"},
        "creditsLimit": 500000,
        "plan": "business",
    },
    "usage": {
        "api": 1200,
        "archival": 0,
        "das": 5000,
        "grpc": 300,
        "grpcGeyser": 0,
        "photon": 0,
        "rpc": 4500,
        "stream": 100,
        "webhook": 800,
        "websocket": 600,
    },
}


def test_project_usage_parses_docs_response():
    usage = ProjectUsage.model_validate(PROJECT_USAGE_RESPONSE)

    assert usage.credits_remaining == 487500
    assert usage.subscription_details.billing_cycle.start == "2026-04-01"
    assert usage.subscription_details.credits_limit == 500000
    assert usage.usage.grpc_geyser == 0


@respx.mock
def test_get_project_usage_sends_api_key_and_project_id():
    route = respx.get(
        "https://admin-api.helius.xyz/v0/admin/projects/{id}/usage/"
    ).mock(return_value=httpx.Response(200, json=PROJECT_USAGE_RESPONSE))

    with AccountManagementClient(api_key="test") as client:
        usage = client.get_project_usage("project-1")

    sent = route.calls.last.request
    assert sent.url.params["api-key"] == "test"
    assert sent.url.params["id"] == "project-1"
    assert usage.credits_used == 12500
    assert usage.usage.websocket == 600


@respx.mock
def test_get_project_usage_uses_default_project_id():
    route = respx.get(
        "https://admin-api.helius.xyz/v0/admin/projects/{id}/usage/"
    ).mock(return_value=httpx.Response(200, json=PROJECT_USAGE_RESPONSE))

    with AccountManagementClient(
        api_key="test", project_id="default-project"
    ) as client:
        client.get_project_usage()

    assert route.calls.last.request.url.params["id"] == "default-project"


def test_get_project_usage_requires_project_id():
    with AccountManagementClient() as client:
        with pytest.raises(ValueError, match="No project ID provided"):
            client.get_project_usage()
