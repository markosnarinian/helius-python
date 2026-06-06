"""Run every example script with known-safe arguments.

This is a live smoke-test runner, not a pytest test module. It intentionally
executes the examples as subprocesses so imports, argument parsing, and runtime
behavior match how users run them from the repository root.

Usage:

    .venv/bin/python test_examples.py

The runner expects `HELIUS_API_KEY` to be available in the environment or in
`.env`, matching the examples themselves. Missing/unauthorized API key failures
are reported as "auth" instead of as example runtime bugs. Some Helius endpoints
are plan-gated or network-gated; other failures in that class are reported as
"external".
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHONPATH = str(ROOT / "src")
USE_COLOR = "NO_COLOR" not in os.environ

GREEN = "\033[32m"
YELLOW = "\033[33m"
ORANGE = "\033[38;5;208m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"

SYSTEM_PROGRAM = "11111111111111111111111111111111"
SMALL_MINT = "J5iyNuTa6zqqA62Xe4h1VBvcBW5CTSNNva3QPh8DU5RV"
KNOWN_SIGNATURE = "eqRntqi1tjXv1zEGBM5btQGWoxWc73XXGDJXjxLE65Atj6T6qzNnJf5LyTbUoGXHS9TzeAnQniAre48SjcJft9f"
DEVNET_ADDRESS = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"

AUTH_FAILURE_MARKERS = (
    "No API key provided.",
    "HTTP 401",
    "401 Unauthorized",
    "HTTP 403",
    "403 Forbidden",
    "Unauthorized",
    "Forbidden",
)


@dataclass(frozen=True)
class ExampleTest:
    name: str
    args: list[str]
    timeout: int = 60
    external_failure_markers: tuple[str, ...] = field(default_factory=tuple)


TESTS = [
    ExampleTest(
        name="rpc/address_transactions",
        args=[
            "examples/rpc/address_transactions.py",
            SYSTEM_PROGRAM,
            "--limit",
            "1",
            "--dry-run",
        ],
    ),
    ExampleTest(
        name="rpc/address_transfers",
        args=[
            "examples/rpc/address_transfers.py",
            SYSTEM_PROGRAM,
            "--limit",
            "1",
            "--dry-run",
        ],
    ),
    ExampleTest(
        name="rpc/block_explorer",
        args=["examples/rpc/block_explorer.py", "--slot", "423563000"],
        timeout=90,
    ),
    ExampleTest(
        name="rpc/devnet_airdrop",
        args=[
            "examples/rpc/devnet_airdrop.py",
            DEVNET_ADDRESS,
            "--sol",
            "0.000000001",
            "--timeout",
            "5",
            "--dry-run",
        ],
    ),
    ExampleTest(
        name="rpc/network_status",
        args=["examples/rpc/network_status.py"],
    ),
    ExampleTest(
        name="rpc/priority_fees",
        args=["examples/rpc/priority_fees.py"],
    ),
    ExampleTest(
        name="rpc/stake_overview",
        args=["examples/rpc/stake_overview.py"],
        timeout=120,
    ),
    ExampleTest(
        name="rpc/token_inspector",
        args=["examples/rpc/token_inspector.py", SMALL_MINT],
        timeout=90,
    ),
    ExampleTest(
        name="rpc/transaction_inspector",
        args=["examples/rpc/transaction_inspector.py", KNOWN_SIGNATURE],
        timeout=90,
    ),
    ExampleTest(
        name="rpc/wallet_tracker",
        args=["examples/rpc/wallet_tracker.py", SYSTEM_PROGRAM, "--limit", "1"],
        timeout=120,
    ),
    ExampleTest(
        name="laserstream/websocket_logs",
        args=["examples/laserstream/websocket_logs.py", "--count", "1"],
        timeout=45,
        external_failure_markers=(
            "TimeoutError: timed out",
        ),
    ),
    ExampleTest(
        name="webhooks/webhook_crud",
        args=[
            "examples/webhooks/webhook_crud.py",
            "create",
            "https://example.com/helius/webhook",
            SYSTEM_PROGRAM,
            "--dry-run",
        ],
    ),
]


def color(text: str, ansi_color: str) -> str:
    if not USE_COLOR:
        return text
    return f"{ansi_color}{text}{RESET}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-v",
        action="count",
        default=0,
        dest="verbose_count",
        help="increase verbosity; use -v for level 1 or -vv for level 2",
    )
    parser.add_argument(
        "--verbose",
        type=int,
        choices=(0, 1, 2),
        default=None,
        help=(
            "0: only results and failure names; "
            "1: include script output for non-passing tests; "
            "2: include script output for all tests"
        ),
    )
    args = parser.parse_args()
    args.verbose = (
        args.verbose if args.verbose is not None else min(args.verbose_count, 2)
    )
    return args


def output_preview(output: str) -> str:
    lines = output.strip().splitlines()
    preview = "\n".join(lines[:30])
    if len(lines) > 30:
        preview += f"\n... ({len(lines) - 30} more lines)"
    return preview


def run_example(test: ExampleTest) -> tuple[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        f"{PYTHONPATH}{os.pathsep}{env['PYTHONPATH']}"
        if env.get("PYTHONPATH")
        else PYTHONPATH
    )

    command = [sys.executable, *test.args]
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=test.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        return "external" if "websocket" in test.name else "failed", output

    output = result.stdout + result.stderr
    if result.returncode == 0:
        return "passed", output
    if any(marker in output for marker in AUTH_FAILURE_MARKERS):
        return "auth", output
    if any(marker in output for marker in test.external_failure_markers):
        return "external", output
    return "failed", output


def main() -> int:
    args = parse_args()
    passed: list[str] = []
    auth: list[str] = []
    external: list[str] = []
    failed: list[tuple[str, str]] = []

    for test in TESTS:
        status, output = run_example(test)
        if status == "passed":
            passed.append(test.name)
            result = color("PASS", GREEN + BOLD)
        elif status == "auth":
            auth.append(test.name)
            result = (
                color("AUTH", ORANGE + BOLD)
                + " - missing API key or endpoint is not authorized for this key"
            )
        elif status == "external":
            external.append(test.name)
            result = (
                color("EXTERNAL", YELLOW + BOLD)
                + " - endpoint, plan, or network prevented a live success"
            )
        else:
            failed.append((test.name, output))
            result = color("FAIL", RED + BOLD)

        print(f"{result}: {test.name}", flush=True)

        should_print_output = output.strip() and (
            args.verbose == 2 or (args.verbose == 1 and status != "passed")
        )
        if should_print_output:
            print(output_preview(output))

    print("\n=== Summary ===")
    print(f"{color('Passed', GREEN)}   : {len(passed)}")
    print(f"{color('Auth', ORANGE)}     : {len(auth)}")
    print(f"{color('External', YELLOW)} : {len(external)}")
    print(f"{color('Failed', RED)}   : {len(failed)}")

    if auth:
        print("\nAuth failures:")
        for name in auth:
            print(f"  - {name}")

    if external:
        print("\nExternal failures:")
        for name in external:
            print(f"  - {name}")

    if failed:
        print("\nUnexpected failures:")
        for name, output in failed:
            print(f"  - {name}")
            if args.verbose >= 1:
                print(f"\n--- {name} ---")
                print(output.strip())
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
