"""List Helius enhanced transactions for an address.

Uses Helius's `getTransactionsForAddress` RPC method, which can return
either compact signature rows or full transaction payloads with pagination.

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/solana_rpc/address_transactions.py <ADDRESS> [--limit 10]
    python examples/solana_rpc/address_transactions.py <ADDRESS> --full --limit 5

Docs:
    https://www.helius.dev/docs/getting-data/get-transactions-for-address

Note:
    Helius documents this exclusive RPC method as requiring a Developer plan
    or higher.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

import httpx

from helius.solana_rpc import SolanaRpcClient


def format_time(block_time: int | None) -> str:
    if block_time is None:
        return "(no time)"
    return dt.datetime.fromtimestamp(block_time, tz=dt.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("address", help="Wallet, account, or program address")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of rows to fetch (1-1000, default 10)",
    )
    parser.add_argument(
        "--pagination-token",
        help="Token returned by a previous page of results",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Fetch full transaction details instead of signature rows",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate arguments and print the planned request without sending it",
    )
    args = parser.parse_args()

    details = "full" if args.full else "signatures"
    if args.dry_run:
        print("Would call get_transactions_for_address with:")
        print(f"  address={args.address}")
        print(f"  transaction_details={details}")
        print(f"  limit={args.limit}")
        print(f"  pagination_token={args.pagination_token}")
        print(f"  encoding={'jsonParsed' if args.full else None}")
        return 0

    try:
        with SolanaRpcClient() as client:
            transactions, next_token = client.get_transactions_for_address(
                address=args.address,
                transaction_details=details,
                sort_order="desc",
                commitment="finalized",
                limit=args.limit,
                pagination_token=args.pagination_token,
                encoding="jsonParsed" if args.full else None,
                max_supported_transaction_version=0 if args.full else None,
            )
    except httpx.HTTPStatusError as exc:
        print(
            f"HTTP {exc.response.status_code}: getTransactionsForAddress was rejected. "
            "This Helius-exclusive method may require a Developer plan or higher.",
            file=sys.stderr,
        )
        return 2

    print(f"\n=== Transactions for {args.address} ===\n")
    if not transactions:
        print("No transactions returned.")
        return 0

    for tx in transactions:
        if details == "signatures":
            status = "ERR" if tx.err else "OK "
            print(
                f"{format_time(tx.block_time)}  slot={tx.slot:<12} "
                f"idx={tx.transaction_index:<4} {status}  {tx.signature}"
            )
        else:
            signature = "(signature unavailable)"
            signatures = tx.transaction.get("signatures")
            if isinstance(signatures, list) and signatures:
                signature = signatures[0]
            err = tx.meta.get("err") if isinstance(tx.meta, dict) else None
            status = "ERR" if err else "OK "
            print(
                f"{format_time(tx.block_time)}  slot={tx.slot:<12} "
                f"idx={tx.transaction_index:<4} {status}  {signature}"
            )

    if next_token:
        print(f"\nNext page token: {next_token}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
