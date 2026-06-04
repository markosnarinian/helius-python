"""Run a tiny local HTTP server that prints Helius webhook payloads.

This receiver uses only the Python standard library. It is useful for local
development with a tunnel such as ngrok, Cloudflare Tunnel, or `ssh -R`.

Usage:

    python examples/webhooks/webhook_receiver.py --port 8080

    # In another shell, expose it publicly and use that URL in Helius:
    ngrok http 8080

    # If your webhook was created with authHeader="Bearer shared-secret":
    python examples/webhooks/webhook_receiver.py \
        --auth-header "Bearer shared-secret"

The handler accepts POST requests on any path, verifies the optional
Authorization header, pretty-prints JSON payloads, and replies with 200 OK.
"""

from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class WebhookHandler(BaseHTTPRequestHandler):
    expected_auth_header: str | None = None

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler hook name
        if self.expected_auth_header is not None:
            actual = self.headers.get("Authorization")
            if actual != self.expected_auth_header:
                self.respond(HTTPStatus.UNAUTHORIZED, {"ok": False})
                print("Rejected request with missing or invalid Authorization header")
                return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)

        try:
            payload: Any = json.loads(raw_body)
        except json.JSONDecodeError:
            payload = raw_body.decode("utf-8", errors="replace")

        print("\n=== Helius webhook received ===")
        print(f"Path: {self.path}")
        print(f"User-Agent: {self.headers.get('User-Agent', '-')}")
        if isinstance(payload, (dict, list)):
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(payload)

        self.respond(HTTPStatus.OK, {"ok": True})

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler hook name
        self.respond(
            HTTPStatus.OK, {"ok": True, "message": "POST webhook payloads here"}
        )

    def log_message(self, format: str, *args: Any) -> None:
        # Keep the default access log, but send it to stdout next to payload logs.
        print(f"{self.address_string()} - {format % args}")

    def respond(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--host", default="127.0.0.1", help="Bind host (default 127.0.0.1)"
    )
    parser.add_argument("--port", type=int, default=8080, help="Bind port (default 8080)")
    parser.add_argument(
        "--auth-header",
        help="Required Authorization header value, matching the webhook authHeader",
    )
    args = parser.parse_args()

    WebhookHandler.expected_auth_header = args.auth_header
    server = ThreadingHTTPServer((args.host, args.port), WebhookHandler)

    print(f"Listening on http://{args.host}:{args.port}")
    if args.auth_header:
        print("Authorization header verification is enabled")
    print("Press Ctrl+C to stop", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping receiver", file=sys.stderr)
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
