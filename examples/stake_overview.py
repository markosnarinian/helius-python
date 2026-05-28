"""Solana staking & inflation overview.

Prints the current inflation rate, governor parameters, total SOL
supply, and a stake breakdown across the active vs. delinquent
validator set (top 10 by stake).

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/stake_overview.py

Uses (with `try/finally`):
    get_inflation_rate, get_inflation_governor, get_supply,
    get_stake_minimum_delegation, get_vote_accounts.
"""

from __future__ import annotations

import sys

from helius.solana_rpc import SolanaRpcClient

LAMPORTS_PER_SOL = 1_000_000_000


def main() -> int:
    client = SolanaRpcClient()
    try:
        rate = client.get_inflation_rate()
        gov = client.get_inflation_governor()
        _ctx, supply = client.get_supply(exclude_non_circulating_accounts_list=True)
        _ctx, min_stake = client.get_stake_minimum_delegation()
        current, delinquent = client.get_vote_accounts()
    finally:
        client.close()

    print("\n=== Inflation ===\n")
    print(f"Epoch              : {rate.epoch}")
    print(f"Total rate         : {rate.total * 100:.4f}%")
    print(f"Validator share    : {rate.validator * 100:.4f}%")
    print(f"Foundation share   : {rate.foundation * 100:.4f}%")
    print()
    print("Governor:")
    print(f"  initial          : {gov.initial * 100:.2f}%")
    print(f"  terminal         : {gov.terminal * 100:.2f}%")
    print(f"  taper            : {gov.taper * 100:.2f}% per year")
    print(
        f"  foundation       : {gov.foundation * 100:.2f}% for "
        f"{gov.foundation_term:.1f} years"
    )

    print("\n=== Supply ===\n")
    print(f"Total              : {supply.total / LAMPORTS_PER_SOL:>16,.4f} SOL")
    print(f"Circulating        : {supply.circulating / LAMPORTS_PER_SOL:>16,.4f} SOL")
    print(
        f"Non-circulating    : {supply.non_circulating / LAMPORTS_PER_SOL:>16,.4f} SOL"
    )

    print("\n=== Stake ===\n")
    print(f"Minimum delegation : {min_stake / LAMPORTS_PER_SOL:.9f} SOL")
    active_stake = sum(v.activated_stake for v in current)
    delinquent_stake = sum(v.activated_stake for v in delinquent)
    total_stake = active_stake + delinquent_stake
    print(
        f"Active validators  : {len(current):>5}  "
        f"{active_stake / LAMPORTS_PER_SOL:>16,.0f} SOL"
    )
    print(
        f"Delinquent         : {len(delinquent):>5}  "
        f"{delinquent_stake / LAMPORTS_PER_SOL:>16,.0f} SOL"
    )
    if total_stake:
        print(f"Delinquent share   : {100 * delinquent_stake / total_stake:.3f}%")

    top = sorted(current, key=lambda v: v.activated_stake, reverse=True)[:10]
    print(f"\nTop {len(top)} validators by active stake:")
    for rank, v in enumerate(top, start=1):
        sol = v.activated_stake / LAMPORTS_PER_SOL
        share = 100 * v.activated_stake / active_stake if active_stake else 0.0
        print(
            f"  {rank:>2}. {v.vote_pubkey}  "
            f"{sol:>14,.0f} SOL  ({share:5.2f}%)  comm={v.commission}%"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
