"""Listen for Solana log notifications over Helius WebSockets.

Subscribes with `logsSubscribe`, prints a small number of notifications,
then unsubscribes cleanly. Use `--mentions <ADDRESS>` to filter logs to a
single account or program; otherwise the example listens to all logs.

Usage:

    export HELIUS_API_KEY=your_helius_api_key
    python examples/laserstream/websocket_logs.py --mentions <ADDRESS>
    python examples/laserstream/websocket_logs.py --count 3

Docs:
    https://www.helius.dev/docs/api-reference/rpc/websocket/logssubscribe
"""

from __future__ import annotations

import argparse
from contextlib import suppress
import sys

from helius.laserstream.websockets import WebSocketClient


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--mentions",
        help="Only receive logs mentioning this account or program address",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of notifications to print before exiting (default 5)",
    )
    args = parser.parse_args()

    log_filter = {"mentions": [args.mentions]} if args.mentions else "all"

    with WebSocketClient() as client:
        subscription = client.logs_subscribe(
            filter=log_filter,
            commitment="confirmed",
        )
        print(f"Subscribed to logs with id {subscription}. Waiting...\n")

        try:
            for index, (context, notification, _subscription) in enumerate(
                client.listen(), start=1
            ):
                slot = context.get("slot") if context else "unknown"
                status = "ERR" if notification.err else "OK "
                print(f"[{index}/{args.count}] slot={slot} {status} {notification.signature}")
                for line in notification.logs[:5]:
                    print(f"    {line}")
                if len(notification.logs) > 5:
                    print(f"    ... {len(notification.logs) - 5} more log lines")
                print()
                if index >= args.count:
                    break
        finally:
            # A busy `logsSubscribe` stream can deliver another notification
            # between our unsubscribe request and the unsubscribe response. The
            # client helper currently expects the very next frame to be the RPC
            # response, so ignore that race here and let the context manager
            # close the socket cleanly.
            with suppress(KeyError):
                client.logs_unsubscribe(subscription)

    return 0


if __name__ == "__main__":
    sys.exit(main())
