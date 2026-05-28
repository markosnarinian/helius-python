"""Explore a single Solana block.

Without arguments, picks the latest finalized slot and prints its block.
With `--slot N`, prints that specific slot. Shows the blockhash,
parent slot, block height, block time, transaction count, and a
breakdown of successful vs. failed transactions plus total fees paid.

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/block_explorer.py
    python examples/block_explorer.py --slot 250000000

Uses (with `with`):
    get_slot, get_block.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

from helius.solana_rpc import SolanaRpcClient

LAMPORTS_PER_SOL = 1_000_000_000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--slot",
        type=int,
        default=None,
        help="Slot to inspect. Defaults to the latest finalized slot.",
    )
    args = parser.parse_args()

    with SolanaRpcClient() as helius:
        slot = (
            args.slot
            if args.slot is not None
            else helius.get_slot(commitment="finalized")
        )
        block = helius.get_block(
            slot,
            commitment="finalized",
            encoding="jsonParsed",
            max_supported_transcation_version=0,
        )

    if block is None:
        print(f"No block returned for slot {slot}.")
        return 1

    print(f"\n=== Block at slot {slot:,} ===\n")
    print(f"Blockhash        : {block.blockhash}")
    print(f"Previous hash    : {block.previous_blockhash}")
    print(f"Parent slot      : {block.parent_slot:,}")
    if block.block_height is not None:
        print(f"Block height     : {block.block_height:,}")
    if block.block_time is not None:
        when = dt.datetime.fromtimestamp(block.block_time, tz=dt.timezone.utc)
        print(f"Block time       : {when.strftime('%Y-%m-%d %H:%M:%SZ')}")

    txs = block.transactions
    total = len(txs)
    failed = sum(1 for tx in txs if (tx.get("meta") or {}).get("err") is not None)
    succeeded = total - failed
    fees = sum((tx.get("meta") or {}).get("fee", 0) for tx in txs)

    print(f"\nTransactions     : {total:,} total")
    print(f"  succeeded      : {succeeded:,}")
    print(f"  failed         : {failed:,}")
    print(
        f"Total fees       : {fees / LAMPORTS_PER_SOL:.9f} SOL " f"({fees:,} lamports)"
    )

    if block.rewards:
        print(f"\nRewards ({len(block.rewards)}):")
        for r in block.rewards[:10]:
            print(f"  {r.pubkey}  +{r.lamports} lamports  ({r.reward_type})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
