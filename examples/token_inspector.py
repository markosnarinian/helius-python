"""Inspect an SPL token mint: supply, decimals, and biggest holders.

Given a mint address, prints:
    - The total / circulating supply (UI amount + raw amount)
    - The top 20 token accounts (largest holders) and their share of supply

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/token_inspector.py <MINT_ADDRESS>

Example with USDC:

    python examples/token_inspector.py EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v

Uses (with `try/finally`):
    get_token_supply, get_token_largest_accounts.
"""

from __future__ import annotations

import argparse
import sys

from helius.client import HeliusClient


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mint", help="SPL token mint address (base58)")
    args = parser.parse_args()

    client = HeliusClient()
    try:
        _ctx, supply = client.get_token_supply(args.mint)
        _ctx, holders = client.get_token_largest_accounts(args.mint)
    finally:
        client.close()

    total = int(supply.amount)
    print(f"\n=== Mint {args.mint} ===\n")
    print(f"Decimals       : {supply.decimals}")
    print(f"Total supply   : {supply.ui_amount_string}  ({supply.amount} base units)")

    if not holders or total == 0:
        print("\nNo holders found.")
        return 0

    print(f"\nTop {len(holders)} holders:")
    print(f"  {'#':>3}  {'share':>8}  {'amount':>22}  account")
    for rank, acct in enumerate(holders, start=1):
        share = 100 * int(acct.amount) / total
        print(
            f"  {rank:>3}  {share:>7.3f}%  {acct.ui_amount_string:>22}  {acct.address}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
