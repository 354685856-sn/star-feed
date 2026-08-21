# GitHub Star Feed

A portable, repository-link based feed of my GitHub Stars.

## Import

Paste this repository URL into a compatible importer:

```text
https://github.com/354685856-sn/star-feed
```

The importer should read `.star-feed/manifest.json` first, then load the files listed there.

Compatible importers should accept common GitHub repository references:

- `https://github.com/354685856-sn/star-feed`
- `354685856-sn/star-feed`
- `git@github.com:354685856-sn/star-feed.git`

Validate the feed contract locally:

```bash
python3 scripts/validate_import.py https://github.com/354685856-sn/star-feed
```

## Feed Files

- `.star-feed/manifest.json` - import entrypoint
- `.star-feed/stars.json` - complete machine-readable Star list
- `.star-feed/categories.json` - grouped by language and topic
- `.star-feed/feed.xml` - Atom feed of recent starred repositories
- `snapshots/` - dated Markdown snapshots

## Current Snapshot

- Owner: `354685856-sn`
- Total stars: `10`
- Generated: `2026-08-21T18:55:14Z`
- Languages: TypeScript (4), Python (4), Unknown (1), Shell (1)
- HTTP date: `Fri, 21 Aug 2026 18:55:14 +0000`

## Latest Stars

| Repository | Language | Stars | Description |
| --- | --- | ---: | --- |
| [DifTorHeSmushma/oracle-speakflow](https://github.com/DifTorHeSmushma/oracle-speakflow) | TypeScript | 3 | Hands-free speech-to-text that pastes where you type — for admins, teachers, writers, developers, and anyone who dictates daily. Windows shipped; macOS CI beta; Linux CI package. MIT. |
| [jremick/codexmaxxing](https://github.com/jremick/codexmaxxing) | Python | 1 | Guides and resources for getting more out of Codex in agentic work |
| [xingranya/GitHub-Stars-AI-Tools](https://github.com/xingranya/GitHub-Stars-AI-Tools) | TypeScript | 98 | 本地优先的 GitHub Stars AI 桌面应用，可 AI 检索/解析已 Star 项目。Local-first AI desktop app for GitHub Stars. |
| [crimeacs/claude-note](https://github.com/crimeacs/claude-note) | Python | 67 | Your AI pair programmer's memory, synced to Obsidian |
| [iansinnott/obsidian-claude-code-mcp](https://github.com/iansinnott/obsidian-claude-code-mcp) | TypeScript | 341 | Connect Claude Code and other AI tools to your Obsidian notes using Model Context Protocol (MCP) |
| [coleam00/claude-memory-compiler](https://github.com/coleam00/claude-memory-compiler) | Python | 1281 | Give Claude Code a memory that evolves with your codebase. Hooks automatically capture sessions, the Claude Agent SDK extracts key decisions and lessons, and an LLM compiler organizes everything into structured, cross-referenced knowledge articles - inspired by Karpathy's LLM Knowledge Base architecture. |
| [coleam00/second-brain-starter](https://github.com/coleam00/second-brain-starter) | Unknown | 745 | Build your own AI Second Brain with Claude Code - a skill that generates a personalized PRD for a proactive, persistent AI assistant |
| [ballred/obsidian-claude-pkm](https://github.com/ballred/obsidian-claude-pkm) | Shell | 1845 | A complete starter kit for an Obsidian + Claude Code personal knowledge management system. |
| [heyitsnoah/claudesidian](https://github.com/heyitsnoah/claudesidian) | Python | 2569 | - |
| [YishenTu/claudian](https://github.com/YishenTu/claudian) | TypeScript | 14900 | An Obsidian plugin that embeds Claude Code/Codex as an AI collaborator in your vault |

## Contract

This repository is intentionally public. Importing it does not require a GitHub token.
Private star feeds can use the same file contract, but consumers need their own read access.
