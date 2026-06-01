"""Request a devnet SOL airdrop and wait for it to confirm.

Points the client at devnet (not mainnet), requests an airdrop, then
polls `getSignatureStatuses` until the airdrop transaction reaches a
`confirmed` (or better) status. Finally prints the post-airdrop balance.

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/solana_rpc/devnet_airdrop.py <WALLET_ADDRESS> [--sol 1.0]

Note:
    `requestAirdrop` is only available on Devnet and Testnet — never on
    Mainnet Beta. This script forces `base_url` to the Helius devnet
    endpoint regardless of any other configuration.

Uses (with `try/finally`):
    request_airdrop, get_signature_statuses, get_balance.
"""

from __future__ import annotations

import argparse
import sys
import time

import httpx

from helius.solana_rpc import SolanaRpcClient

LAMPORTS_PER_SOL = 1_000_000_000
DEVNET_URL = "https://devnet.helius-rpc.com"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("address", help="Wallet public key (base58)")
    parser.add_argument(
        "--sol",
        type=float,
        default=1.0,
        help="Amount of devnet SOL to airdrop (default: 1.0)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Seconds to wait for confirmation (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate arguments and print the planned airdrop without sending it",
    )
    args = parser.parse_args()
    lamports = int(args.sol * LAMPORTS_PER_SOL)

    if args.dry_run:
        print("Would request devnet airdrop with:")
        print(f"  address={args.address}")
        print(f"  sol={args.sol}")
        print(f"  lamports={lamports}")
        print(f"  timeout={args.timeout}")
        return 0

    client = SolanaRpcClient(base_url=DEVNET_URL)
    try:
        print(f"Requesting {args.sol} SOL airdrop to {args.address} on devnet...")
        try:
            signature = client.request_airdrop(public_key=args.address, lamports=lamports)
        except httpx.HTTPStatusError as exc:
            print(
                f"HTTP {exc.response.status_code}: devnet airdrop request was rejected.",
                file=sys.stderr,
            )
            return 2
        print(f"  signature: {signature}")

        deadline = time.monotonic() + args.timeout
        status = None
        while time.monotonic() < deadline:
            _ctx, statuses = client.get_signature_statuses(
                signatures=[signature], search_transaction_history=True
            )
            status = statuses[0]
            if status is not None and status.confirmation_status in (
                "confirmed",
                "finalized",
            ):
                break
            time.sleep(1.0)

        if status is None or status.confirmation_status not in (
            "confirmed",
            "finalized",
        ):
            print(f"  TIMEOUT: not confirmed within {args.timeout:.0f}s")
            return 1
        if status.err:
            print(f"  FAILED on-chain: {status.err}")
            return 1
        print(f"  status: {status.confirmation_status} at slot {status.slot}")

        _ctx, balance = client.get_balance(public_key=args.address)
        print(f"Post-airdrop balance: {balance / LAMPORTS_PER_SOL:.9f} SOL")
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
