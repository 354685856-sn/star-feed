# Star Feed Import Contract

This repository can be imported from a single GitHub repository URL.

## Discovery

Given a repository URL:

```text
https://github.com/354685856-sn/star-feed
```

Compatible importers should also accept:

```text
354685856-sn/star-feed
git@github.com:354685856-sn/star-feed.git
https://github.com/354685856-sn/star-feed/tree/main
```

An importer should fetch:

```text
https://raw.githubusercontent.com/354685856-sn/star-feed/main/.star-feed/manifest.json
```

The manifest points to the canonical files:

- `.star-feed/stars.json`
- `.star-feed/categories.json`
- `.star-feed/feed.xml`
- `snapshots/YYYY-MM-DD.md`

## Public And Private Feeds

Public feeds do not require a GitHub token.

Private feeds may use the same structure, but the importer must authenticate with an account that can read the repository.

## Network Handling

Importers should retry transient raw file reads. GitHub raw responses can occasionally terminate early or return a temporary server error even when the repository and files are valid.

## Stable Fields

`stars.json` uses `schema_version: star-feed/v1`.

Required top-level fields:

- `schema_version`
- `generated_at`
- `owner`
- `source`
- `feed_repository`
- `count`
- `summary`
- `stars`

Required star item fields:

- `full_name`
- `name`
- `owner`
- `url`
- `description`
- `language`
- `topics`
- `stars`
- `forks`
- `license`
- `archived`
- `fork`
- `pushed_at`
- `updated_at`
- `created_at`
- `starred_at`
