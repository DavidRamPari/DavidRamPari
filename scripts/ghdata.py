"""Live numbers for the banner header, read from the GitHub API during the daily build."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

API = "https://api.github.com"
UA = "DavidRamPari-profile-build"

CONTRIB_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection { contributionCalendar { totalContributions } }
  }
}
"""


def _request(url: str, token: str | None, body: dict | None = None) -> Any:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": UA}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch(user: str, token: str | None) -> dict[str, Any]:
    """Public repos and contributions in the last year. Raises on network or API errors."""
    profile = _request(f"{API}/users/{user}", token)
    contributions = None
    if token:  # the GraphQL API needs a token, even for public data
        try:
            res = _request(f"{API}/graphql", token, {"query": CONTRIB_QUERY, "variables": {"login": user}})
            contributions = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
        except (urllib.error.HTTPError, KeyError, TypeError):
            contributions = None
    return {
        "user": user,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "public_repos": profile.get("public_repos"),
        "contributions": contributions,
    }
