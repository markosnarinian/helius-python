"""List token and SOL transfers for an address.

Uses Helius's `getTransfersByAddress` RPC method exposed by this client as
`get_transfers_by_address`.

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/solana_rpc/address_transfers.py <ADDRESS> [--limit 20]
    python examples/solana_rpc/address_transfers.py <ADDRESS> --direction in --mint <MINT>

Docs:
    https://www.helius.dev/docs/getting-data/get-transfers-by-address

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


def format_time(block_time: int) -> str:
    return dt.datetime.fromtimestamp(block_time, tz=dt.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("address", help="Wallet, token account, or owner address")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of transfers to fetch (1-100, default 20)",
    )
    parser.add_argument(
        "--direction",
        choices=("in", "out", "any"),
        default="any",
        help="Transfer direction relative to address (default any)",
    )
    parser.add_argument("--with-address", help="Counterparty address filter")
    parser.add_argument("--mint", help="Mint address filter")
    parser.add_argument(
        "--pagination-token",
        help="Token returned by a previous page of results",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate arguments and print the planned request without sending it",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("Would call get_transfers_by_address with:")
        print(f"  address={args.address}")
        print(f"  with_address={args.with_address}")
        print(f"  direction={args.direction}")
        print(f"  mint={args.mint}")
        print(f"  limit={args.limit}")
        print(f"  pagination_token={args.pagination_token}")
        return 0

    try:
        with SolanaRpcClient() as client:
            transfers, next_token = client.get_transfers_by_address(
                address=args.address,
                with_address=args.with_address,
                direction=args.direction,
                mint=args.mint,
                limit=args.limit,
                pagination_token=args.pagination_token,
                commitment="finalized",
                sort_order="desc",
            )
    except httpx.HTTPStatusError as exc:
        print(
            f"HTTP {exc.response.status_code}: getTransfersByAddress was rejected. "
            "This Helius-exclusive method may require a Developer plan or higher.",
            file=sys.stderr,
        )
        return 2

    print(f"\n=== Transfers for {args.address} ===\n")
    if not transfers:
        print("No transfers returned.")
        return 0

    for transfer in transfers:
        from_acct = transfer.from_user_account or transfer.from_token_account or "-"
        to_acct = transfer.to_user_account or transfer.to_token_account or "-"
        print(
            f"{format_time(transfer.block_time)}  slot={transfer.slot:<12} "
            f"{transfer.type:<11} {transfer.ui_amount:>18}  mint={transfer.mint}"
        )
        print(f"    from={from_acct}")
        print(f"    to  ={to_acct}")
        print(f"    sig ={transfer.signature}")

    if next_token:
        print(f"\nNext page token: {next_token}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
