"""Recent priority-fee summary.

Calls `getRecentPrioritizationFees` and prints a quick statistical
summary (min / median / p75 / p90 / max) of micro-lamports-per-CU paid
in the last ~150 slots — useful when picking a `ComputeBudget` fee for a
transaction you're about to send.

Optionally takes one or more "locked writable account" addresses so the
sample only counts transactions that locked those accounts as writable
(matches your real contention).

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/priority_fees.py
    python examples/priority_fees.py --account <PUBKEY> --account <PUBKEY>

Uses (with `with`):
    get_recent_prioritization_fees.
"""

from __future__ import annotations

import argparse
import statistics
import sys

from helius.solana_rpc import SolanaRpcClient


def percentile(sorted_values: list[int], pct: float) -> int:
    if not sorted_values:
        return 0
    k = max(0, min(len(sorted_values) - 1, int(round(pct * (len(sorted_values) - 1)))))
    return sorted_values[k]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--account",
        action="append",
        default=[],
        help="Locked writable account to filter on. May be passed multiple times.",
    )
    args = parser.parse_args()
    accounts = args.account or None

    with SolanaRpcClient() as helius:
        samples = helius.get_recent_prioritization_fees(
            locked_writable_accounts=accounts
        )

    if not samples:
        print("No recent prioritization fee samples returned.")
        return 0

    fees = sorted(fee for _slot, fee in samples)
    slot_range = (min(slot for slot, _ in samples), max(slot for slot, _ in samples))

    print(f"\n=== Recent prioritization fees ({len(samples)} samples) ===\n")
    if accounts:
        print(f"Filtered on accounts: {', '.join(accounts)}\n")
    print(f"Slot range  : {slot_range[0]} – {slot_range[1]}")
    print(f"Min         : {fees[0]:>10} micro-lamports/CU")
    print(f"Median      : {int(statistics.median(fees)):>10} micro-lamports/CU")
    print(f"p75         : {percentile(fees, 0.75):>10} micro-lamports/CU")
    print(f"p90         : {percentile(fees, 0.90):>10} micro-lamports/CU")
    print(f"p99         : {percentile(fees, 0.99):>10} micro-lamports/CU")
    print(f"Max         : {fees[-1]:>10} micro-lamports/CU")

    return 0


if __name__ == "__main__":
    sys.exit(main())
