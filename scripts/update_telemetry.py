#!/usr/bin/env python3
"""Refresh the [telemetry] block in the profile README."""

from __future__ import annotations

import json
import os
import random
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
STATE = ROOT / "telemetry.json"
USER = "nightfun-pixel"
API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")
DRY_RUN = "--dry-run" in sys.argv

LOCAL_TZ = timezone(timedelta(hours=4))
TODAY = datetime.now(LOCAL_TZ).date().isoformat()


def request(path: str, payload: dict | None = None) -> dict:
    req = urllib.request.Request(f"{API}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "nightfun-telemetry")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=data, timeout=30) as resp:
        return json.load(resp)


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {}


def human(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.3f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    return str(n)


def row(key: str, value: object, comment: str = "") -> str:
    line = f"{key:<17}= {str(value):<15}"
    if comment:
        line += f" # {comment}"
    return line.rstrip()


def main() -> None:
    state = load_state()
    tokens = int(state.get("tokens_burned", 1_240_000_000))
    if state.get("last_sync") != TODAY:
        tokens += random.Random(TODAY).randint(2_000_000, 9_000_000)

    try:
        user = request(f"/users/{USER}")
        public_repos = int(user["public_repos"])
        followers = int(user["followers"])
    except Exception as exc:  # a stale stat beats a failed nightly job
        print(f"warn: user stats: {exc}")
        public_repos = int(state.get("public_repos", 0))
        followers = int(state.get("followers", 0))

    try:
        repos = request(f"/users/{USER}/repos?per_page=100&type=owner")
        stars = sum(int(repo.get("stargazers_count", 0)) for repo in repos)
    except Exception as exc:
        print(f"warn: repo stats: {exc}")
        stars = int(state.get("stars", 0))

    contributions = int(state.get("contributions", 0))
    if TOKEN:
        query = """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar { totalContributions }
            }
          }
        }
        """
        try:
            data = request("/graphql", {"query": query, "variables": {"login": USER}})
            contributions = int(
                data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
            )
        except Exception as exc:
            print(f"warn: contributions: {exc}")

    energy = max(1, contributions // 13)
    block = "\n".join(
        [
            "[telemetry]",
            row("tokens_burned", f'"{human(tokens)}"', "estimated by vibes"),
            row("contributions", contributions, "public, this year"),
            row("public_repos", public_repos),
            row("stars", stars, "received"),
            row("followers", followers),
            row("energy_drinks", f'"0x{energy:X}"', "this year, roughly"),
            row("contexts_lost", 404),
            row("patience", '"deprecated"'),
            row("router_load", '"0.0% — runs on GitHub Actions"'),
            row("last_sync", f'"{TODAY}"'),
        ]
    )

    text = README.read_text(encoding="utf-8")
    start = text.index("[telemetry]")
    end = text.index("\n[stack]", start)
    updated = text[:start] + block + "\n\n" + text[end + 1 :]

    print(block)
    print(
        f"-- tokens={tokens} repos={public_repos} stars={stars} "
        f"followers={followers} contributions={contributions}"
    )

    if DRY_RUN:
        return

    STATE.write_text(
        json.dumps(
            {
                "tokens_burned": tokens,
                "last_sync": TODAY,
                "public_repos": public_repos,
                "stars": stars,
                "followers": followers,
                "contributions": contributions,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if updated != text:
        README.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
