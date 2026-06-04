from helius.webhooks.webhooks import Webhook


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


def test_webhook_model_validates_docs_response_shape():
    webhook = Webhook.model_validate(WEBHOOK_RESPONSE)

    assert webhook.webhook_id == "123e4567-e89b-12d3-a456-426614174000"
    assert webhook.wallet == "wallet-address"
    assert webhook.webhook_url == "https://example.com/webhook"
    assert webhook.transaction_types == ["TRANSFER"]
    assert webhook.account_addresses == ["account-address"]
    assert webhook.webhook_type == "enhanced"
    assert webhook.auth_header == "Bearer secret"
    assert webhook.active is True
