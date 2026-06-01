"""Inspect an SPL token mint: supply, decimals, and biggest holders.

Given a mint address, prints:
    - The total / circulating supply (UI amount + raw amount)
    - The top 20 token accounts (largest holders) and their share of supply

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/solana_rpc/token_inspector.py <MINT_ADDRESS>

Example with a small-holder-count mint:

    python examples/solana_rpc/token_inspector.py J5iyNuTa6zqqA62Xe4h1VBvcBW5CTSNNva3QPh8DU5RV

Note:
    Very large mints may be rejected by `getTokenLargestAccounts` if the
    upstream RPC would need to scan too many accounts.

Uses (with `try/finally`):
    get_token_supply, get_token_largest_accounts.
"""

from __future__ import annotations

import argparse
import sys

import httpx

from helius.solana_rpc import SolanaRpcClient


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mint", help="SPL token mint address (base58)")
    args = parser.parse_args()

    client = SolanaRpcClient()
    client._client.timeout = httpx.Timeout(30.0)
    try:
        _ctx, supply = client.get_token_supply(mint_address=args.mint)
        _ctx, holders = client.get_token_largest_accounts(mint=args.mint)
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
