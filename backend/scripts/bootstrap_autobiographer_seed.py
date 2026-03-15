from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed autobiographer memory events from known site facts.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--admin-token", default=os.getenv("ADMIN_TOKEN", ""), help="Admin token")
    parser.add_argument("--year", type=int, default=datetime.now(timezone.utc).year, help="Target year")
    return parser.parse_args()


def build_seed_events(year: int) -> list[dict]:
    return [
        {
            "source": "site-bootstrap",
            "source_kind": "bootstrap",
            "title": "Living in Ojai with family",
            "detail": (
                "Home base is Ojai, California. Life is centered around living with Sara, Willa, "
                "and Bruce the cat. This is a family season, not just a work season, and that fact "
                "should be part of the narrative spine."
            ),
            "tags": ["family", "home", "ojai", "season-of-life"],
            "people": ["Sara", "Willa"],
            "place_label": "Ojai, California",
            "privacy_level": "private",
            "review_state": "accepted",
            "joy_score": 0.92,
            "family_relevance_score": 0.98,
            "importance_score": 0.9,
            "event_at": f"{year}-03-01T08:00:00+00:00",
        },
        {
            "source": "site-bootstrap",
            "source_kind": "bootstrap",
            "title": "Working at Sift as VP Product",
            "detail": (
                "Current work chapter is serving as Vice President of Product at Sift. "
                "The season combines product leadership, execution pressure, and the question "
                "of how to build while still staying present inside family life."
            ),
            "tags": ["work", "sift", "product", "leadership"],
            "people": [],
            "place_label": "Ojai, California",
            "privacy_level": "private",
            "review_state": "accepted",
            "joy_score": 0.64,
            "family_relevance_score": 0.5,
            "importance_score": 0.92,
            "event_at": f"{year}-03-03T17:00:00+00:00",
        },
        {
            "source": "site-bootstrap",
            "source_kind": "bootstrap",
            "title": "Building a living autobiography for family",
            "detail": (
                "A deliberate effort began to build an autobiographer agent that could remember life "
                "faithfully over time: one chapter each year, one living post that keeps revising, "
                "and a system designed so the people closest to him could later understand what this "
                "season of life actually felt like."
            ),
            "tags": ["autobiography", "family", "memory", "ai"],
            "people": ["Sara", "Willa"],
            "place_label": "Ojai, California",
            "privacy_level": "private",
            "review_state": "accepted",
            "joy_score": 0.88,
            "family_relevance_score": 0.96,
            "importance_score": 0.95,
            "event_at": f"{year}-03-14T18:30:00+00:00",
        },
    ]


def main() -> int:
    args = parse_args()
    if not args.admin_token:
        print("ADMIN_TOKEN is required (flag or env).", file=sys.stderr)
        return 2

    events = build_seed_events(args.year)
    headers = {"X-Admin-Token": args.admin_token, "Content-Type": "application/json"}
    created: list[dict] = []
    with httpx.Client(timeout=60.0) as client:
        for event in events:
            resp = client.post(
                f"{args.base_url.rstrip('/')}/api/v1/lab/autobiographer/events",
                headers=headers,
                json=event,
            )
            if resp.status_code >= 400:
                print(f"Seed failed ({resp.status_code}): {resp.text}", file=sys.stderr)
                return 1
            created.append(resp.json())

    print(json.dumps({"created": created}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
