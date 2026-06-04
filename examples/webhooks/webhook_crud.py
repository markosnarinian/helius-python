"""Create, list, update, toggle, and delete Helius webhooks.

Usage:

    export HELIUS_API_KEY=your_helius_api_key

    # Print all configured webhooks.
    python examples/webhooks/webhook_crud.py list

    # Inspect one webhook.
    python examples/webhooks/webhook_crud.py show <WEBHOOK_ID>

    # Create a webhook that watches one or more accounts.
    python examples/webhooks/webhook_crud.py create \
        https://example.com/helius/webhook \
        <ACCOUNT_ADDRESS> [<ACCOUNT_ADDRESS> ...] \
        --transaction-type TRANSFER \
        --auth-header "Bearer shared-secret"

    # Update every mutable field on an existing webhook.
    python examples/webhooks/webhook_crud.py update <WEBHOOK_ID> \
        https://example.com/helius/webhook \
        <ACCOUNT_ADDRESS> [<ACCOUNT_ADDRESS> ...]

    # Pause, resume, or delete.
    python examples/webhooks/webhook_crud.py toggle <WEBHOOK_ID> --inactive
    python examples/webhooks/webhook_crud.py delete <WEBHOOK_ID> --yes

Docs:
    https://www.helius.dev/docs/api-reference/webhooks/create-webhook
    https://www.helius.dev/docs/api-reference/webhooks/get-all-webhooks
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx

from helius.webhooks.webhooks import Webhook, WebhooksApiClient


def print_webhook(webhook: Webhook) -> None:
    print(json.dumps(webhook.model_dump(mode="json"), indent=2, sort_keys=True))


def print_dry_run(action: str, payload: dict[str, Any]) -> int:
    print(f"Would {action} with:")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def add_webhook_payload_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("webhook_url", help="Public HTTPS endpoint Helius will POST to")
    parser.add_argument(
        "account_addresses",
        nargs="+",
        help="One or more account addresses to watch",
    )
    parser.add_argument(
        "--transaction-type",
        dest="transaction_types",
        action="append",
        help="Transaction type to subscribe to; repeat for multiple (default TRANSFER)",
    )
    parser.add_argument(
        "--webhook-type",
        default="enhanced",
        choices=(
            "enhanced",
            "raw",
            "discord",
            "enhancedDevnet",
            "rawDevnet",
            "discordDevnet",
        ),
        help="Webhook payload type (default enhanced)",
    )
    parser.add_argument(
        "--auth-header",
        default="",
        help="Value Helius should include in the Authorization header",
    )
    parser.add_argument(
        "--encoding",
        default="jsonParsed",
        help="Webhook transaction encoding (default jsonParsed)",
    )
    parser.add_argument(
        "--txn-status",
        default="all",
        choices=("all", "success", "failed"),
        help="Transaction status filter (default all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the request payload without sending it",
    )


def webhook_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "webhook_url": args.webhook_url,
        "transaction_types": args.transaction_types or ["TRANSFER"],
        "account_addresses": args.account_addresses,
        "webhook_type": args.webhook_type,
        "auth_header": args.auth_header,
        "encoding": args.encoding,
        "txn_status": args.txn_status,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List all webhooks")

    show = subparsers.add_parser("show", help="Show one webhook")
    show.add_argument("webhook_id")

    create = subparsers.add_parser("create", help="Create a webhook")
    add_webhook_payload_args(create)

    update = subparsers.add_parser("update", help="Replace an existing webhook")
    update.add_argument("webhook_id")
    add_webhook_payload_args(update)

    toggle = subparsers.add_parser("toggle", help="Activate or deactivate a webhook")
    toggle.add_argument("webhook_id")
    status = toggle.add_mutually_exclusive_group(required=True)
    status.add_argument("--active", action="store_true", help="Resume the webhook")
    status.add_argument("--inactive", action="store_true", help="Pause the webhook")
    toggle.add_argument("--dry-run", action="store_true")

    delete = subparsers.add_parser("delete", help="Delete a webhook")
    delete.add_argument("webhook_id")
    delete.add_argument("--yes", action="store_true", help="Confirm permanent deletion")
    delete.add_argument("--dry-run", action="store_true")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command in {"create", "update"} and args.dry_run:
        return print_dry_run(args.command, webhook_payload(args))
    if args.command == "toggle" and args.dry_run:
        return print_dry_run(
            "toggle", {"webhook_id": args.webhook_id, "active": args.active}
        )
    if args.command == "delete":
        if args.dry_run:
            return print_dry_run("delete", {"webhook_id": args.webhook_id})
        if not args.yes:
            print("Refusing to delete without --yes", file=sys.stderr)
            return 2

    try:
        with WebhooksApiClient() as client:
            if args.command == "list":
                webhooks = client.get_all_webhooks()
                print(json.dumps([w.model_dump(mode="json") for w in webhooks], indent=2))
            elif args.command == "show":
                print_webhook(client.get_webhook(args.webhook_id))
            elif args.command == "create":
                print_webhook(client.create_webhook(**webhook_payload(args)))
            elif args.command == "update":
                print_webhook(
                    client.update_webhook(args.webhook_id, **webhook_payload(args))
                )
            elif args.command == "toggle":
                print_webhook(client.toggle_webhook(args.webhook_id, active=args.active))
            elif args.command == "delete":
                print(client.delete_webhook(args.webhook_id))
    except httpx.HTTPStatusError as exc:
        print(f"HTTP {exc.response.status_code}: {exc.response.text}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
