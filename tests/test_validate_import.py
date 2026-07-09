#!/usr/bin/env python3
"""Tests for the star-feed import contract validator."""

from __future__ import annotations

import unittest

from scripts import validate_import


class RepoReferenceTests(unittest.TestCase):
    def test_parse_https_repo_url(self) -> None:
        self.assertEqual(
            validate_import.parse_repo_reference("https://github.com/354685856-sn/star-feed"),
            "354685856-sn/star-feed",
        )

    def test_parse_https_repo_url_with_extra_path(self) -> None:
        self.assertEqual(
            validate_import.parse_repo_reference("https://github.com/354685856-sn/star-feed/tree/main"),
            "354685856-sn/star-feed",
        )

    def test_parse_owner_repo(self) -> None:
        self.assertEqual(validate_import.parse_repo_reference("354685856-sn/star-feed"), "354685856-sn/star-feed")

    def test_parse_ssh_repo_url(self) -> None:
        self.assertEqual(
            validate_import.parse_repo_reference("git@github.com:354685856-sn/star-feed.git"),
            "354685856-sn/star-feed",
        )

    def test_reject_non_github_url(self) -> None:
        with self.assertRaises(ValueError):
            validate_import.parse_repo_reference("https://example.com/354685856-sn/star-feed")


class LocalContractTests(unittest.TestCase):
    def test_validate_local_manifest(self) -> None:
        manifest = validate_import.load_json(".star-feed/manifest.json")
        count = validate_import.validate(manifest, None, validate_import.DEFAULT_BRANCH)
        self.assertGreaterEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
