from __future__ import annotations

import argparse
import json
import os
import sys

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the lab daily brief endpoint.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--admin-token", default=os.getenv("ADMIN_TOKEN", ""), help="Admin token")
    parser.add_argument("--priority", action="append", default=[], help="Repeat for multiple priorities")
    parser.add_argument("--risk", action="append", default=[], help="Repeat for multiple risks")
    parser.add_argument("--context", default="", help="Optional context")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.admin_token:
        print("ADMIN_TOKEN is required (flag or env).", file=sys.stderr)
        return 2
    if not args.priority:
        print("At least one --priority is required.", file=sys.stderr)
        return 2

    payload = {
        "priorities": args.priority,
        "risks": args.risk,
        "context": args.context,
    }

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            f"{args.base_url.rstrip('/')}/api/v1/lab/daily-brief",
            headers={"X-Admin-Token": args.admin_token, "Content-Type": "application/json"},
            json=payload,
        )

    if resp.status_code >= 400:
        print(f"Daily brief failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        return 1

    print(json.dumps(resp.json(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
