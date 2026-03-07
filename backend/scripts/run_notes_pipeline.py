from __future__ import annotations

import argparse
import json
import os
import sys

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the OpenAI notes pipeline endpoint.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--admin-token", default=os.getenv("ADMIN_TOKEN", ""), help="Admin token")
    parser.add_argument("--context", required=True, help="Context string for ideation")
    parser.add_argument("--count", type=int, default=8, help="Number of ideas")
    parser.add_argument("--draft-idea-index", type=int, default=0, help="Index of idea to draft")
    parser.add_argument("--target-words", type=int, default=1000, help="Target word count")
    parser.add_argument("--subdir", default="notes-drafts", help="Output subdir under content/")
    parser.add_argument("--no-save", action="store_true", help="Do not save files on server")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.admin_token:
        print("ADMIN_TOKEN is required (flag or env).", file=sys.stderr)
        return 2

    payload = {
        "context": args.context,
        "count": args.count,
        "draft_idea_index": args.draft_idea_index,
        "target_words": args.target_words,
        "save_to_disk": not args.no_save,
        "subdir": args.subdir,
    }

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            f"{args.base_url.rstrip('/')}/api/v1/openai/notes/pipeline",
            headers={"X-Admin-Token": args.admin_token, "Content-Type": "application/json"},
            json=payload,
        )

    if resp.status_code >= 400:
        print(f"Pipeline failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        return 1

    data = resp.json()
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
