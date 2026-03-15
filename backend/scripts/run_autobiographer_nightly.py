from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nightly autobiographer refresh and provenance export.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--admin-token", default=os.getenv("ADMIN_TOKEN", ""), help="Admin token")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="Target year")
    parser.add_argument("--month", type=int, default=datetime.now().month, help="Target month (1-12)")
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.admin_token:
        print("ADMIN_TOKEN is required (flag or env).", file=sys.stderr)
        return 2

    publish_payload = {
        "year": args.year,
        "month": args.month,
        "persona_label": args.persona,
        "style_brief": args.style_brief,
        "include_private_context": True,
        "force_regenerate": False,
        "subdir": args.subdir,
    }
    export_payload = {
        "year": args.year,
        "include_private_context": True,
    }

    headers = {"X-Admin-Token": args.admin_token, "Content-Type": "application/json"}
    with httpx.Client(timeout=180.0) as client:
        publish_resp = client.post(
            f"{args.base_url.rstrip('/')}/api/v1/lab/autobiographer/publish-live-note",
            headers=headers,
            json=publish_payload,
        )
        if publish_resp.status_code >= 400:
            print(f"Nightly publish failed ({publish_resp.status_code}): {publish_resp.text}", file=sys.stderr)
            return 1

        export_resp = client.post(
            f"{args.base_url.rstrip('/')}/api/v1/openai/provenance/export",
            headers=headers,
            json=export_payload,
        )
        if export_resp.status_code >= 400:
            print(f"Provenance export failed ({export_resp.status_code}): {export_resp.text}", file=sys.stderr)
            return 1

    print(
        json.dumps(
            {
                "published": publish_resp.json(),
                "provenance_export": export_resp.json(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
