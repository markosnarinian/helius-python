"""Wallet tracker: dump SOL balance, SPL token holdings, and recent activity.

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/wallet_tracker.py <WALLET_ADDRESS> [--limit 20]

Example (Helius's own treasury-ish address, replace with any):

    python examples/wallet_tracker.py 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU

It prints:
    - SOL balance (in SOL, not lamports)
    - All non-empty SPL token accounts (mint, balance, account address)
    - The last N transactions (timestamp, slot, status, signature)

Pure stdlib + helius-python. No solana-py, no solders, no extra deps.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

from helius.solana_rpc import SolanaRpcClient

# SPL Token program ID — used to list every token account owned by a wallet.
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
LAMPORTS_PER_SOL = 1_000_000_000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("address", help="Wallet public key (base58)")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of recent signatures to fetch (1-1000, default 20)",
    )
    args = parser.parse_args()

    with SolanaRpcClient() as client:  # reads HELIUS_API_KEY from env / .env
        # --- SOL balance ---------------------------------------------------
        _ctx, lamports = client.get_balance(args.address)
        print(f"\n=== {args.address} ===\n")
        print(
            f"SOL balance: {lamports / LAMPORTS_PER_SOL:.9f} SOL "
            f"({lamports} lamports)\n"
        )

        # --- SPL token holdings -------------------------------------------
        _ctx, token_accounts = client.get_token_accounts_by_owner(
            owner_pub_key=args.address,
            program_id=TOKEN_PROGRAM_ID,
            encoding="jsonParsed",
        )
        nonzero = []
        for pubkey, account in token_accounts:
            # With jsonParsed encoding, `data` is a dict — pull out the
            # parsed token-amount info.
            info = account.data["parsed"]["info"]  # type: ignore[index]
            amount = info["tokenAmount"]
            if int(amount["amount"]) == 0:
                continue
            nonzero.append((pubkey, info["mint"], amount["uiAmountString"]))

        if nonzero:
            print(f"SPL token accounts ({len(nonzero)} non-empty):")
            for pubkey, mint, ui_amount in nonzero:
                print(f"  {ui_amount:>20}  mint={mint}  acct={pubkey}")
            print()
        else:
            print("SPL token accounts: none with non-zero balance.\n")

        # --- Recent activity ----------------------------------------------
        sigs = client.get_signatures_for_address(args.address, limit=args.limit)
        print(f"Last {len(sigs)} signatures:")
        for sig in sigs:
            ts = (
                dt.datetime.fromtimestamp(sig.block_time, tz=dt.timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%SZ"
                )
                if sig.block_time is not None
                else "         (no time)         "
            )
            status = "ERR " if sig.err else "OK  "
            print(f"  {ts}  slot={sig.slot:>12}  {status}  {sig.signature}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
