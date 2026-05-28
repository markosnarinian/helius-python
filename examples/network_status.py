"""Solana network status dashboard.

Prints a quick health snapshot of the Solana cluster as seen by Helius:
node health, version, current slot / block height, epoch progress, and a
recent-performance summary (avg TPS over the last samples).

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/network_status.py

Uses (with `with`):
    get_health, get_version, get_slot, get_block_height, get_epoch_info,
    get_recent_performance_samples, get_identity.
"""

from __future__ import annotations

import sys

from helius.client import SolanaRpcClient


def main() -> int:
    with SolanaRpcClient() as helius:
        healthy = helius.get_health()
        solana_core, feature_set = helius.get_version()
        identity = helius.get_identity()
        slot = helius.get_slot()
        block_height = helius.get_block_height()
        epoch = helius.get_epoch_info()
        samples = helius.get_recent_performance_samples(limit=10)

    status = "OK" if healthy else "UNHEALTHY"
    print("=== Solana network status ===\n")
    print(f"Node health        : {status}")
    print(f"Solana version     : {solana_core}  (feature-set {feature_set})")
    print(f"Node identity      : {identity}")
    print(f"Current slot       : {slot:,}")
    print(f"Current block      : {block_height:,}")

    epoch_pct = 100 * epoch.slot_index / epoch.slots_in_epoch
    print(
        f"Epoch              : {epoch.epoch}  "
        f"({epoch.slot_index:,}/{epoch.slots_in_epoch:,} = {epoch_pct:.2f}%)"
    )
    print(f"Absolute slot      : {epoch.absolute_slot:,}")
    print(f"Transactions seen  : {epoch.transaction_count:,}")

    if samples:
        total_txs = sum(s.num_transactions for s in samples)
        total_secs = sum(s.sample_period_secs for s in samples)
        avg_tps = total_txs / total_secs if total_secs else 0.0
        print(
            f"\nAvg TPS over last {len(samples)} samples "
            f"({total_secs}s window): {avg_tps:,.0f}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
