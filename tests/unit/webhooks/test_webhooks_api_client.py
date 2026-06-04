import json

import httpx
import respx

from helius.webhooks.webhooks import WebhooksApiClient


WEBHOOK_RESPONSE = {
    "webhookID": "123e4567-e89b-12d3-a456-426614174000",
    "wallet": "wallet-address",
    "webhookURL": "https://example.com/webhook",
    "transactionTypes": ["TRANSFER"],
    "accountAddresses": ["account-address"],
    "webhookType": "enhanced",
    "authHeader": "Bearer secret",
    "active": True,
}


@respx.mock
def test_create_webhook_posts_request_and_parses_response():
    route = respx.post("https://mainnet.helius-rpc.com/v0/webhooks/").mock(
        return_value=httpx.Response(200, json=WEBHOOK_RESPONSE)
    )

    with WebhooksApiClient(api_key="test") as client:
        webhook = client.create_webhook(
            webhook_url="https://example.com/webhook",
            transaction_types=["TRANSFER"],
            account_addresses=["account-address"],
            webhook_type="enhanced",
            auth_header="Bearer secret",
            encoding="json",
            txn_status="success",
        )

    sent = route.calls.last.request
    assert sent.url.params["api-key"] == "test"
    assert json.loads(sent.content) == {
        "webhookURL": "https://example.com/webhook",
        "transactionTypes": ["TRANSFER"],
        "accountAddresses": ["account-address"],
        "webhookType": "enhanced",
        "authHeader": "Bearer secret",
        "encoding": "json",
        "txnStatus": "success",
    }
    assert webhook.webhook_id == "123e4567-e89b-12d3-a456-426614174000"
    assert webhook.webhook_url == "https://example.com/webhook"
    assert webhook.transaction_types == ["TRANSFER"]


@respx.mock
def test_get_webhook_fetches_webhook_by_id():
    route = respx.get(
        "https://mainnet.helius-rpc.com/v0/webhooks/123e4567-e89b-12d3-a456-426614174000"
    ).mock(return_value=httpx.Response(200, json=WEBHOOK_RESPONSE))

    with WebhooksApiClient(api_key="test") as client:
        webhook = client.get_webhook("123e4567-e89b-12d3-a456-426614174000")

    sent = route.calls.last.request
    assert sent.url.params["api-key"] == "test"
    assert webhook.webhook_id == "123e4567-e89b-12d3-a456-426614174000"
    assert webhook.webhook_url == "https://example.com/webhook"
    assert webhook.transaction_types == ["TRANSFER"]
    assert webhook.active is True


@respx.mock
def test_get_all_webhooks_fetches_all_webhooks():
    second_webhook = {
        **WEBHOOK_RESPONSE,
        "webhookID": "223e4567-e89b-12d3-a456-426614174000",
        "webhookURL": "https://example.com/second-webhook",
        "transactionTypes": ["NFT_SALE"],
    }
    route = respx.get("https://mainnet.helius-rpc.com/v0/webhooks/").mock(
        return_value=httpx.Response(200, json=[WEBHOOK_RESPONSE, second_webhook])
    )

    with WebhooksApiClient(api_key="test") as client:
        webhooks = client.get_all_webhooks()

    sent = route.calls.last.request
    assert sent.url.params["api-key"] == "test"
    assert len(webhooks) == 2
    assert webhooks[0].webhook_id == "123e4567-e89b-12d3-a456-426614174000"
    assert webhooks[1].webhook_id == "223e4567-e89b-12d3-a456-426614174000"
    assert webhooks[1].webhook_url == "https://example.com/second-webhook"
    assert webhooks[1].transaction_types == ["NFT_SALE"]


@respx.mock
def test_update_webhook_puts_request_and_parses_response():
    updated_response = {
        **WEBHOOK_RESPONSE,
        "webhookURL": "https://example.com/updated-webhook",
        "transactionTypes": ["NFT_SALE"],
        "accountAddresses": ["updated-account-address"],
        "authHeader": "Bearer updated-secret",
    }
    route = respx.put(
        "https://mainnet.helius-rpc.com/v0/webhooks/123e4567-e89b-12d3-a456-426614174000"
    ).mock(return_value=httpx.Response(200, json=updated_response))

    with WebhooksApiClient(api_key="test") as client:
        webhook = client.update_webhook(
            "123e4567-e89b-12d3-a456-426614174000",
            webhook_url="https://example.com/updated-webhook",
            transaction_types=["NFT_SALE"],
            account_addresses=["updated-account-address"],
            webhook_type="enhanced",
            auth_header="Bearer updated-secret",
            encoding="json",
            txn_status="success",
        )

    sent = route.calls.last.request
    assert sent.url.params["api-key"] == "test"
    assert json.loads(sent.content) == {
        "webhookURL": "https://example.com/updated-webhook",
        "transactionTypes": ["NFT_SALE"],
        "accountAddresses": ["updated-account-address"],
        "webhookType": "enhanced",
        "authHeader": "Bearer updated-secret",
        "encoding": "json",
        "txnStatus": "success",
    }
    assert webhook.webhook_id == "123e4567-e89b-12d3-a456-426614174000"
    assert webhook.webhook_url == "https://example.com/updated-webhook"
    assert webhook.transaction_types == ["NFT_SALE"]
    assert webhook.account_addresses == ["updated-account-address"]


@respx.mock
def test_toggle_webhook_patches_active_and_parses_response():
    toggled_response = {**WEBHOOK_RESPONSE, "active": False}
    route = respx.patch(
        "https://mainnet.helius-rpc.com/v0/webhooks/123e4567-e89b-12d3-a456-426614174000"
    ).mock(return_value=httpx.Response(200, json=toggled_response))

    with WebhooksApiClient(api_key="test") as client:
        webhook = client.toggle_webhook(
            "123e4567-e89b-12d3-a456-426614174000", active=False
        )

    sent = route.calls.last.request
    assert sent.url.params["api-key"] == "test"
    assert json.loads(sent.content) == {"active": False}
    assert webhook.webhook_id == "123e4567-e89b-12d3-a456-426614174000"
    assert webhook.active is False


@respx.mock
def test_delete_webhook_deletes_by_id():
    route = respx.delete(
        "https://mainnet.helius-rpc.com/v0/webhooks/123e4567-e89b-12d3-a456-426614174000"
    ).mock(return_value=httpx.Response(200, json={"message": "No content."}))

    with WebhooksApiClient(api_key="test") as client:
        message = client.delete_webhook("123e4567-e89b-12d3-a456-426614174000")

    sent = route.calls.last.request
    assert sent.url.params["api-key"] == "test"
    assert sent.content == b""
    assert message == "No content."
