#!/usr/bin/env python3
"""Validate that a star-feed repository can be imported from its manifest."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(source: str) -> Any:
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": "star-feed-import-validator"})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    return json.loads((ROOT / source).read_text(encoding="utf-8"))


def raw_base(repo_url: str, branch: str) -> str:
    prefix = "https://github.com/"
    if not repo_url.startswith(prefix):
        raise ValueError("repo URL must start with https://github.com/")
    owner_repo = repo_url.removeprefix(prefix).strip("/")
    return f"https://raw.githubusercontent.com/{owner_repo}/{branch}/"


def validate(manifest: dict[str, Any], repo_url: str | None, branch: str) -> int:
    if manifest.get("schema_version") != "star-feed-manifest/v1":
        raise ValueError("manifest schema_version must be star-feed-manifest/v1")
    files = manifest.get("files")
    if not isinstance(files, dict) or "stars" not in files:
        raise ValueError("manifest files.stars is required")
    stars_path = str(files["stars"])
    if repo_url:
        stars = load_json(raw_base(repo_url, branch) + stars_path)
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
    return len(items)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_url", nargs="?", help="Optional GitHub repository URL to validate remotely.")
    parser.add_argument("--branch", default="main")
    args = parser.parse_args(argv)

    manifest_source = raw_base(args.repo_url, args.branch) + ".star-feed/manifest.json" if args.repo_url else ".star-feed/manifest.json"
    manifest = load_json(manifest_source)
    count = validate(manifest, args.repo_url, args.branch)
    print(f"import ok: {count} starred repositories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
