#!/usr/bin/env python3
"""Publish a portable GitHub Star feed for repo-link imports."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from email.utils import format_datetime
from html import escape
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
FEED_DIR = ROOT / ".star-feed"
SNAPSHOT_DIR = ROOT / "snapshots"


def _request_json(url: str, token: str | None) -> tuple[Any, dict[str, str]]:
    headers = {
        "Accept": "application/vnd.github.star+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "star-feed-publisher",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data, dict(response.headers)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {exc.code}: {body}") from exc


def _parse_next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue
        left, _, _right = section.partition(";")
        return left.strip()[1:-1]
    return None


def fetch_starred(username: str, token: str | None) -> list[dict[str, Any]]:
    encoded_user = urllib.parse.quote(username)
    url = f"https://api.github.com/users/{encoded_user}/starred?per_page=100"
    entries: list[dict[str, Any]] = []
    while url:
        data, headers = _request_json(url, token)
        if not isinstance(data, list):
            raise RuntimeError("Unexpected GitHub API response: expected a list.")
        entries.extend(data)
        url = _parse_next_link(headers.get("Link"))
    return entries


def normalize_star(entry: dict[str, Any]) -> dict[str, Any]:
    repo = entry.get("repo") if "repo" in entry else entry
    if not isinstance(repo, dict):
        raise RuntimeError("Unexpected starred entry: missing repo object.")
    owner = repo.get("owner") or {}
    license_info = repo.get("license") or {}
    topics = repo.get("topics") or []
    if not isinstance(topics, list):
        topics = []
    return {
        "full_name": repo.get("full_name"),
        "name": repo.get("name"),
        "owner": owner.get("login"),
        "url": repo.get("html_url"),
        "description": repo.get("description") or "",
        "language": repo.get("language") or "Unknown",
        "topics": sorted(str(topic) for topic in topics),
        "stars": repo.get("stargazers_count") or 0,
        "forks": repo.get("forks_count") or 0,
        "open_issues": repo.get("open_issues_count") or 0,
        "license": license_info.get("spdx_id") if isinstance(license_info, dict) else None,
        "homepage": repo.get("homepage") or "",
        "archived": bool(repo.get("archived")),
        "fork": bool(repo.get("fork")),
        "pushed_at": repo.get("pushed_at"),
        "updated_at": repo.get("updated_at"),
        "created_at": repo.get("created_at"),
        "starred_at": entry.get("starred_at"),
    }


def build_payload(username: str, repo_url: str, stars: list[dict[str, Any]]) -> dict[str, Any]:
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    normalized = [normalize_star(entry) for entry in stars]
    normalized.sort(key=lambda item: item.get("starred_at") or item.get("updated_at") or "", reverse=True)
    language_counts = Counter(item["language"] for item in normalized)
    topic_counts = Counter(topic for item in normalized for topic in item["topics"])
    return {
        "schema_version": "star-feed/v1",
        "generated_at": generated_at,
        "owner": username,
        "source": {
            "type": "github-stars",
            "user": username,
            "url": f"https://github.com/{username}?tab=stars",
        },
        "feed_repository": repo_url,
        "count": len(normalized),
        "summary": {
            "languages": dict(language_counts.most_common()),
            "topics": dict(topic_counts.most_common(50)),
        },
        "stars": normalized,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_manifest(username: str, repo_url: str, payload: dict[str, Any]) -> None:
    manifest = {
        "schema_version": "star-feed-manifest/v1",
        "name": f"{username}'s GitHub Star Feed",
        "owner": username,
        "generated_at": payload["generated_at"],
        "source": payload["source"],
        "files": {
            "stars": ".star-feed/stars.json",
            "categories": ".star-feed/categories.json",
            "atom": ".star-feed/feed.xml",
            "latest_snapshot": f"snapshots/{payload['generated_at'][:10]}.md",
        },
        "import": {
            "mode": "repository-link",
            "hint": "Paste this public repository URL into a compatible importer.",
            "repository_url": repo_url,
        },
    }
    write_json(FEED_DIR / "manifest.json", manifest)


def write_categories(payload: dict[str, Any]) -> None:
    by_language: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in payload["stars"]:
        repo = {"full_name": item["full_name"], "url": item["url"], "description": item["description"]}
        by_language[item["language"]].append(repo)
        for topic in item["topics"]:
            by_topic[topic].append(repo)
    categories = {
        "schema_version": "star-feed-categories/v1",
        "generated_at": payload["generated_at"],
        "by_language": dict(sorted(by_language.items())),
        "by_topic": dict(sorted(by_topic.items())),
    }
    write_json(FEED_DIR / "categories.json", categories)


def write_atom(payload: dict[str, Any]) -> None:
    ET.register_namespace("", "http://www.w3.org/2005/Atom")
    root = ET.Element("feed", xmlns="http://www.w3.org/2005/Atom")
    ET.SubElement(root, "title").text = f"{payload['owner']}'s GitHub Stars"
    ET.SubElement(root, "id").text = f"tag:github.com,{payload['owner']}:stars"
    ET.SubElement(root, "updated").text = payload["generated_at"]
    ET.SubElement(root, "link", href=payload["source"]["url"])
    for item in payload["stars"][:50]:
        entry = ET.SubElement(root, "entry")
        ET.SubElement(entry, "title").text = item["full_name"]
        ET.SubElement(entry, "id").text = item["url"]
        ET.SubElement(entry, "updated").text = item.get("starred_at") or item.get("updated_at") or payload["generated_at"]
        ET.SubElement(entry, "link", href=item["url"])
        content = f"{item['description']}\n\nLanguage: {item['language']} | Stars: {item['stars']}"
        ET.SubElement(entry, "summary").text = content
    tree = ET.ElementTree(root)
    FEED_DIR.mkdir(parents=True, exist_ok=True)
    tree.write(FEED_DIR / "feed.xml", encoding="utf-8", xml_declaration=True)


def format_repo_row(item: dict[str, Any]) -> str:
    desc = item["description"].replace("\n", " ").strip() or "-"
    return (
        f"| [{item['full_name']}]({item['url']}) | {item['language']} | "
        f"{item['stars']} | {desc} |"
    )


def write_snapshot(payload: dict[str, Any]) -> Path:
    date = payload["generated_at"][:10]
    path = SNAPSHOT_DIR / f"{date}.md"
    lines = [
        f"# Star Snapshot - {date}",
        "",
        f"- Owner: `{payload['owner']}`",
        f"- Generated: `{payload['generated_at']}`",
        f"- Total stars: `{payload['count']}`",
        "",
        "## Latest Stars",
        "",
        "| Repository | Language | Stars | Description |",
        "| --- | --- | ---: | --- |",
    ]
    lines.extend(format_repo_row(item) for item in payload["stars"][:100])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_readme(payload: dict[str, Any], repo_url: str) -> None:
    languages = ", ".join(f"{name} ({count})" for name, count in list(payload["summary"]["languages"].items())[:8])
    updated = datetime.fromisoformat(payload["generated_at"].replace("Z", "+00:00"))
    lines = [
        "# GitHub Star Feed",
        "",
        "A portable, repository-link based feed of my GitHub Stars.",
        "",
        "## Import",
        "",
        "Paste this repository URL into a compatible importer:",
        "",
        f"```text\n{repo_url}\n```",
        "",
        "The importer should read `.star-feed/manifest.json` first, then load the files listed there.",
        "",
        "## Feed Files",
        "",
        "- `.star-feed/manifest.json` - import entrypoint",
        "- `.star-feed/stars.json` - complete machine-readable Star list",
        "- `.star-feed/categories.json` - grouped by language and topic",
        "- `.star-feed/feed.xml` - Atom feed of recent starred repositories",
        "- `snapshots/` - dated Markdown snapshots",
        "",
        "## Current Snapshot",
        "",
        f"- Owner: `{payload['owner']}`",
        f"- Total stars: `{payload['count']}`",
        f"- Generated: `{payload['generated_at']}`",
        f"- Languages: {languages or '-'}",
        f"- HTTP date: `{format_datetime(updated)}`",
        "",
        "## Latest Stars",
        "",
        "| Repository | Language | Stars | Description |",
        "| --- | --- | ---: | --- |",
    ]
    lines.extend(format_repo_row(item) for item in payload["stars"][:30])
    lines.extend(
        [
            "",
            "## Contract",
            "",
            "This repository is intentionally public. Importing it does not require a GitHub token.",
            "Private star feeds can use the same file contract, but consumers need their own read access.",
        ]
    )
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default=os.environ.get("STAR_FEED_USER", "354685856-sn"))
    parser.add_argument("--repo-url", default=os.environ.get("STAR_FEED_REPO_URL", "https://github.com/354685856-sn/star-feed"))
    args = parser.parse_args(argv)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    stars = fetch_starred(args.user, token)
    payload = build_payload(args.user, args.repo_url, stars)
    write_json(FEED_DIR / "stars.json", payload)
    write_manifest(args.user, args.repo_url, payload)
    write_categories(payload)
    write_atom(payload)
    write_snapshot(payload)
    write_readme(payload, args.repo_url)
    print(f"published {payload['count']} starred repositories for {args.user}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
