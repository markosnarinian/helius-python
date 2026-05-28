"""Pretty-print a single transaction by its signature.

Fetches a transaction with `jsonParsed` encoding and prints the slot,
block time, fee, success/error, the SOL balance change of every account
involved, and any log messages emitted by the on-chain programs.

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/transaction_inspector.py <SIGNATURE>

Uses (with `with`):
    get_transaction.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

from helius.client import HeliusClient

LAMPORTS_PER_SOL = 1_000_000_000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("signature", help="Transaction signature (base58)")
    args = parser.parse_args()

    with HeliusClient() as helius:
        tx = helius.get_transaction(
            args.signature,
            encoding="jsonParsed",
            max_supported_transaction_version=0,
        )

    print(f"\n=== Transaction {args.signature} ===\n")
    print(f"Slot          : {tx.slot:,}")
    if tx.block_time is not None:
        when = dt.datetime.fromtimestamp(tx.block_time, tz=dt.timezone.utc)
        print(f"Block time    : {when.strftime('%Y-%m-%d %H:%M:%SZ')}")
    if tx.version is not None:
        print(f"Tx version    : {tx.version}")

    meta = tx.meta
    if meta is None:
        print("\n(no metadata returned)")
        return 0

    print(f"Fee           : {meta.fee} lamports "
          f"({meta.fee / LAMPORTS_PER_SOL:.9f} SOL)")
    print(f"Result        : {'ERROR ' + str(meta.err) if meta.err else 'success'}")

    # Account balance changes ------------------------------------------------
    # jsonParsed transaction has account keys at transaction.message.accountKeys
    message = tx.transaction["message"] if isinstance(tx.transaction, dict) else {}
    account_keys = [
        k["pubkey"] if isinstance(k, dict) else k
        for k in message.get("accountKeys", [])
    ]
    if account_keys and len(meta.pre_balances) == len(account_keys):
        print("\nSOL balance changes:")
        for key, pre, post in zip(account_keys, meta.pre_balances, meta.post_balances):
            delta = post - pre
            if delta == 0:
                continue
            sign = "+" if delta > 0 else "-"
            print(
                f"  {key}  {sign}{abs(delta) / LAMPORTS_PER_SOL:.9f} SOL  "
                f"(pre={pre}, post={post})"
            )

    if meta.log_messages:
        print(f"\nLogs ({len(meta.log_messages)}):")
        for line in meta.log_messages:
            print(f"  {line}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
