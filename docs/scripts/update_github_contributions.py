"""Generate open source contribution pages from GitHub search data."""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = ROOT / "docs" / "source" / "projects"
GITHUB_API = "https://api.github.com/search/issues"
GITHUB_REPOS_API = "https://api.github.com/repos"
GITHUB_USER = "nicu1989"
PRIMARY_ORGS = {"eclipse-score", "nrfconnect"}
EXCLUDED_OWNERS = {GITHUB_USER, *PRIMARY_ORGS, "sandbox-nicu"}

ORG_CONFIG = {
    "eclipse-score": {
        "title": "Eclipse SCORE Open Source Contributions",
        "output": PROJECTS_DIR / "eclipse-score.rst",
        "org_label": "eclipse-score",
        "source_label": "SCORE",
        "areas": [
            "Documentation infrastructure and publishing workflows for SCORE repositories.",
            "Bazel registry and module integration work across emerging SCORE components.",
            "CI/CD workflow improvements, reusable workflows, and repository automation.",
            "Tooling for copyright checks, formatting, gitlint, rustfmt, and developer setup.",
            "Organization-level repository setup, CODEOWNERS, and Eclipse Foundation metadata.",
        ],
    },
    "nrfconnect": {
        "title": "Nordic nRF Connect Open Source Contributions",
        "output": PROJECTS_DIR / "nrfconnect.rst",
        "org_label": "nrfconnect",
        "source_label": "nrfconnect",
        "areas": [
            "SBOM tooling for Nordic Connect SDK, including SPDX reporting, input handling, "
            "symlink deduplication, and binary artifact support.",
            "License metadata and manifest license checks across SDK repositories.",
            "Requirements and developer-tooling updates in downstream Zephyr work.",
            "CI automation for SBOM generation and compliance checks.",
        ],
    },
}

OTHER_ORGS_CONFIG = {
    "title": "Other Open Source Contributions",
    "output": PROJECTS_DIR / "other-open-source.rst",
    "source_label": "other organizations",
}


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "nicolaedicu-ro-contribution-page-generator",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_search(query: str) -> list[dict]:
    items: list[dict] = []
    page = 1
    headers = github_headers()

    while True:
        params = urllib.parse.urlencode({"q": query, "per_page": 100, "page": page})
        request = urllib.request.Request(f"{GITHUB_API}?{params}", headers=headers)

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub search failed for {query!r}: {exc.code} {detail}") from exc

        page_items = payload.get("items", [])
        items.extend(page_items)

        total = min(payload.get("total_count", 0), 1000)
        if len(items) >= total or len(page_items) < 100:
            return items

        page += 1
        time.sleep(0.2)


def github_repo(full_repo: str) -> dict:
    request = urllib.request.Request(f"{GITHUB_REPOS_API}/{full_repo}", headers=github_headers())

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub repo lookup failed for {full_repo!r}: {exc.code} {detail}") from exc


def repo_name(item: dict) -> str:
    return item["repository_url"].removeprefix("https://api.github.com/repos/")


def repo_owner(item: dict) -> str:
    return repo_name(item).split("/", 1)[0]


def parse_date(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def rst_link(label: str, url: str) -> str:
    escaped = label.replace("`", "\\`")
    return f"`{escaped} <{url}>`_"


def public_search_link(label: str, query: str, search_type: str) -> str:
    encoded = urllib.parse.quote(query)
    return rst_link(label, f"https://github.com/search?q={encoded}&type={search_type}")


def repo_rows(org: str, prs: list[dict]) -> list[tuple[str, int, int]]:
    authored = Counter(repo_name(item) for item in prs)
    merged = Counter(repo_name(item) for item in prs if item.get("pull_request", {}).get("merged_at"))

    rows = []
    for full_repo, count in authored.most_common():
        short_repo = full_repo.split("/", 1)[1]
        rows.append((rst_link(short_repo, f"https://github.com/{full_repo}"), count, merged[full_repo]))
    return rows


def org_rows(prs: list[dict], issues: list[dict]) -> list[tuple[str, int, int, int]]:
    pr_counts = Counter(repo_owner(item) for item in prs)
    merged_counts = Counter(repo_owner(item) for item in prs if item.get("pull_request", {}).get("merged_at"))
    issue_counts = Counter(repo_owner(item) for item in issues)
    owners = sorted(
        set(pr_counts) | set(issue_counts),
        key=lambda owner: (pr_counts[owner] + issue_counts[owner], pr_counts[owner]),
        reverse=True,
    )

    rows = []
    for owner in owners:
        rows.append((rst_link(owner, f"https://github.com/{owner}"), pr_counts[owner], merged_counts[owner], issue_counts[owner]))
    return rows


def render_bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def render_page(org: str, prs: list[dict], issues: list[dict]) -> str:
    config = ORG_CONFIG[org]
    merged_count = sum(1 for item in prs if item.get("pull_request", {}).get("merged_at"))
    open_count = sum(1 for item in prs if item["state"] == "open")
    collected = dt.date.today().isoformat()
    pr_query = f"type:pr author:{GITHUB_USER} org:{org}"
    lines = [
        config["title"],
        "=" * len(config["title"]),
        "",
        f"All-time public contribution data for {rst_link(GITHUB_USER, f'https://github.com/{GITHUB_USER}')}",
        f"in the {rst_link(config['org_label'], f'https://github.com/{org}')} GitHub organization.",
        f"Data is generated from GitHub search. Last updated: {collected}.",
        "",
        "Snapshot",
        "--------",
        "",
        f"- Authored pull requests: {len(prs)}.",
        f"- Merged pull requests: {merged_count}.",
    ]

    if open_count:
        lines.append(f"- Open pull requests at collection time: {open_count}.")
    lines.extend(
        [
            f"- Authored issues returned by GitHub search: {len(issues)}.",
            f"- Public source query: {public_search_link(f'authored {config['source_label']} pull requests', pr_query, 'pullrequests')}.",
            "",
            "Contribution Areas",
            "------------------",
            "",
            *render_bullets(config["areas"]),
            "",
            "Pull Requests by Repository",
            "---------------------------",
            "",
            ".. list-table::",
            "   :header-rows: 1",
            "",
            "   * - Repository",
            "     - Authored PRs",
            "     - Merged PRs",
        ]
    )

    for repo_link, authored, merged in repo_rows(org, prs):
        lines.extend(
            [
                f"   * - {repo_link}",
                f"     - {authored}",
                f"     - {merged}",
            ]
        )

    lines.append("")

    return "\n".join(lines)


def organization_owned_items(items: list[dict]) -> list[dict]:
    repo_types: dict[str, str] = {}
    filtered = []

    for item in items:
        owner = repo_owner(item)
        if owner in EXCLUDED_OWNERS:
            continue

        full_repo = repo_name(item)
        if full_repo not in repo_types:
            repo_types[full_repo] = github_repo(full_repo)["owner"]["type"]
            time.sleep(0.2)

        if repo_types[full_repo] == "Organization":
            filtered.append(item)

    return filtered


def render_other_orgs_page(prs: list[dict], issues: list[dict]) -> str:
    config = OTHER_ORGS_CONFIG
    merged_count = sum(1 for item in prs if item.get("pull_request", {}).get("merged_at"))
    open_count = sum(1 for item in prs if item["state"] == "open")
    collected = dt.date.today().isoformat()
    pr_query = (
        f"type:pr author:{GITHUB_USER} "
        "-org:eclipse-score -org:nrfconnect -user:nicu1989 -org:sandbox-nicu"
    )

    lines = [
        config["title"],
        "=" * len(config["title"]),
        "",
        f"All-time public contribution data for {rst_link(GITHUB_USER, f'https://github.com/{GITHUB_USER}')}",
        "in organization-owned repositories outside ``eclipse-score`` and ``nrfconnect``.",
        f"Data is generated from GitHub search. Last updated: {collected}.",
        "",
        "Snapshot",
        "--------",
        "",
        f"- Authored pull requests: {len(prs)}.",
        f"- Merged pull requests: {merged_count}.",
    ]

    if open_count:
        lines.append(f"- Open pull requests at collection time: {open_count}.")

    source_link = public_search_link(f"authored {config['source_label']} pull requests", pr_query, "pullrequests")
    lines.extend(
        [
            f"- Authored issues returned by GitHub search: {len(issues)}.",
            f"- Public source query: {source_link}.",
            "",
            "Organizations",
            "-------------",
            "",
            ".. list-table::",
            "   :header-rows: 1",
            "",
            "   * - Organization",
            "     - Authored PRs",
            "     - Merged PRs",
            "     - Authored Issues",
        ]
    )

    for owner_link, authored, merged, issue_count in org_rows(prs, issues):
        lines.extend(
            [
                f"   * - {owner_link}",
                f"     - {authored}",
                f"     - {merged}",
                f"     - {issue_count}",
            ]
        )

    lines.extend(
        [
            "",
            "Pull Requests by Repository",
            "---------------------------",
            "",
            ".. list-table::",
            "   :header-rows: 1",
            "",
            "   * - Repository",
            "     - Authored PRs",
            "     - Merged PRs",
        ]
    )

    authored = Counter(repo_name(item) for item in prs)
    merged = Counter(repo_name(item) for item in prs if item.get("pull_request", {}).get("merged_at"))
    for full_repo, count in authored.most_common():
        lines.extend(
            [
                f"   * - {rst_link(full_repo, f'https://github.com/{full_repo}')}",
                f"     - {count}",
                f"     - {merged[full_repo]}",
            ]
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    for org, config in ORG_CONFIG.items():
        prs = github_search(f"type:pr author:{GITHUB_USER} org:{org}")
        issues = github_search(f"type:issue author:{GITHUB_USER} org:{org}")
        config["output"].write_text(render_page(org, prs, issues), encoding="utf-8")
        print(f"Updated {config['output'].relative_to(ROOT)}")

    all_prs = github_search(f"type:pr author:{GITHUB_USER}")
    all_issues = github_search(f"type:issue author:{GITHUB_USER}")
    other_prs = organization_owned_items(all_prs)
    other_issues = organization_owned_items(all_issues)
    OTHER_ORGS_CONFIG["output"].write_text(render_other_orgs_page(other_prs, other_issues), encoding="utf-8")
    print(f"Updated {OTHER_ORGS_CONFIG['output'].relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
