#!/usr/bin/env python3
"""Validate that a star-feed repository can be imported from its manifest."""

from __future__ import annotations

import argparse
import http.client
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "star-feed-import-validator"
DEFAULT_BRANCH = "main"


def read_bytes(source: str, attempts: int = 3) -> bytes:
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": USER_AGENT})
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.read()
            except (TimeoutError, http.client.IncompleteRead, OSError) as exc:
                last_error = exc
                if attempt == attempts:
                    break
                time.sleep(0.5 * attempt)
        raise RuntimeError(f"failed to read {source}: {last_error}") from last_error
    return (ROOT / source).read_bytes()


def load_json(source: str) -> Any:
    return json.loads(read_bytes(source).decode("utf-8"))


def load_xml(source: str) -> ET.Element:
    return ET.fromstring(read_bytes(source))


def parse_repo_reference(repo_reference: str) -> str:
    """Return owner/repo from common GitHub repository link forms."""
    cleaned = repo_reference.strip()
    if cleaned.startswith("git@github.com:"):
        cleaned = cleaned.removeprefix("git@github.com:")
    elif cleaned.startswith(("http://", "https://")):
        parsed = urllib.parse.urlparse(cleaned)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise ValueError("repo URL host must be github.com")
        cleaned = parsed.path
    elif cleaned.startswith("github.com/"):
        cleaned = cleaned.removeprefix("github.com/")
    cleaned = cleaned.strip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    parts = [part for part in cleaned.split("/") if part]
    if len(parts) < 2:
        raise ValueError("repo reference must include owner and repository")
    owner, repo = parts[0], parts[1]
    if not owner or not repo:
        raise ValueError("repo reference must include owner and repository")
    return f"{owner}/{repo}"


def raw_base(repo_reference: str, branch: str) -> str:
    owner_repo = parse_repo_reference(repo_reference)
    return f"https://raw.githubusercontent.com/{owner_repo}/{branch}/"


def validate(manifest: dict[str, Any], repo_url: str | None, branch: str) -> int:
    if manifest.get("schema_version") != "star-feed-manifest/v1":
        raise ValueError("manifest schema_version must be star-feed-manifest/v1")
    files = manifest.get("files")
    if not isinstance(files, dict) or "stars" not in files:
        raise ValueError("manifest files.stars is required")
    stars_path = str(files["stars"])
    source_base = raw_base(repo_url, branch) if repo_url else ""
    if repo_url:
        stars = load_json(source_base + stars_path)
    else:
        stars = load_json(stars_path)
    if stars.get("schema_version") != "star-feed/v1":
        raise ValueError("stars schema_version must be star-feed/v1")
    items = stars.get("stars")
    if not isinstance(items, list):
        raise ValueError("stars.stars must be a list")
    if stars.get("count") != len(items):
        raise ValueError("stars.count must match stars length")
    for index, item in enumerate(items):
        for key in ("full_name", "url", "language", "topics", "stars"):
            if key not in item:
                raise ValueError(f"star item {index} missing {key}")
    if "categories" in files:
        categories_source = source_base + str(files["categories"]) if repo_url else str(files["categories"])
        categories = load_json(categories_source)
        if categories.get("schema_version") != "star-feed-categories/v1":
            raise ValueError("categories schema_version must be star-feed-categories/v1")
    if "atom" in files:
        atom_source = source_base + str(files["atom"]) if repo_url else str(files["atom"])
        atom = load_xml(atom_source)
        if not atom.tag.endswith("feed"):
            raise ValueError("atom feed root must be feed")
    if "latest_snapshot" in files:
        snapshot_source = source_base + str(files["latest_snapshot"]) if repo_url else str(files["latest_snapshot"])
        snapshot = read_bytes(snapshot_source).decode("utf-8")
        if "# Star Snapshot" not in snapshot:
            raise ValueError("latest snapshot must be a Star Snapshot markdown file")
    return len(items)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "repo_url",
        nargs="?",
        help="Optional GitHub repository reference to validate remotely. Accepts URL, owner/repo, or git@github.com:owner/repo.git.",
    )
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    args = parser.parse_args(argv)

    manifest_source = (
        raw_base(args.repo_url, args.branch) + ".star-feed/manifest.json"
        if args.repo_url
        else ".star-feed/manifest.json"
    )
    manifest = load_json(manifest_source)
    count = validate(manifest, args.repo_url, args.branch)
    print(f"import ok: {count} starred repositories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
