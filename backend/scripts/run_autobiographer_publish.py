from __future__ import annotations

import argparse
import json
import os
import sys

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish autobiographer notes.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--admin-token", default=os.getenv("ADMIN_TOKEN", ""), help="Admin token")
    parser.add_argument(
        "--mode",
        choices=("live", "year"),
        default="year",
        help="Publish the live monthly note or the yearly chapter note",
    )
    parser.add_argument("--year", type=int, required=True, help="Target year")
    parser.add_argument("--month", type=int, help="Target month (1-12) for live mode")
    parser.add_argument("--persona", default="founder-biographer", help="Persona label")
    parser.add_argument(
        "--style-brief",
        default=(
            "Concise biographical nonfiction: direct, observant, emotionally precise, "
            "grounded in real scenes, and adapted toward Noah's own spare, practical tone."
        ),
        help="Style prompt for chapter generation",
    )
    parser.add_argument("--subdir", default="notes-drafts", help="Output subdir under content/")
    parser.add_argument("--force", action="store_true", help="Force regenerate target month")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.admin_token:
        print("ADMIN_TOKEN is required (flag or env).", file=sys.stderr)
        return 2

    if args.mode == "live" and not args.month:
        print("--month is required when --mode live.", file=sys.stderr)
        return 2

    payload = {
        "year": args.year,
        "persona_label": args.persona,
        "style_brief": args.style_brief,
        "include_private_context": False,
        "force_regenerate": args.force,
        "subdir": args.subdir,
    }
    endpoint = "/api/v1/lab/autobiographer/publish-year-note"
    if args.mode == "live":
        payload["month"] = args.month
        endpoint = "/api/v1/lab/autobiographer/publish-live-note"

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            f"{args.base_url.rstrip('/')}{endpoint}",
            headers={"X-Admin-Token": args.admin_token, "Content-Type": "application/json"},
            json=payload,
        )

    if resp.status_code >= 400:
        print(f"Publish failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        return 1

    print(json.dumps(resp.json(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
