# XHS Likes Manager

A local tool to fetch, organize, tag, and review your Xiaohongshu (小红书) liked and bookmarked posts.

[中文文档](README_CN.md)

## Why?

Xiaohongshu has no built-in way to search, tag, or manage your liked/bookmarked posts. After a few hundred likes, finding anything becomes impossible. This tool exports your data locally so you can organize it however you want.

## Features

- 📥 **Fetch** — Export all your likes and bookmarks via browser automation
- 🏷️ **Auto-tag** — Categorize posts by configurable keyword rules
- 📄 **Paper extraction** — Find arXiv papers from AI/ML posts
- 📋 **Interactive review** — Terminal-based review workflow (keep/remove/tag/note)
- 👎 **Unlike** — Remove likes directly via browser automation
- 📊 **Stats** — View tag distribution and progress
- 📝 **Markdown export** — Auto-generated readable markdown files

## Quick Start

```bash
# Clone and install
git clone https://github.com/jinghan23/xhs-likes-manager.git
cd xhs-likes-manager
pip install -e .
playwright install chromium

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your preferences

# Login (opens browser — log in manually)
python -m xhs_likes_manager login

# Fetch your likes and bookmarks
python -m xhs_likes_manager fetch

# Auto-tag everything
python -m xhs_likes_manager tag

# See what you've got
python -m xhs_likes_manager stats

# Review interactively
python -m xhs_likes_manager review --mode ai
```

## Commands

| Command | Description |
|---------|-------------|
| `login` | Open browser for manual XHS login |
| `fetch [likes\|bookmarks\|all]` | Fetch data (default: all) |
| `tag` | Auto-tag all untagged items |
| `stats` | Show tag distribution |
| `list [--tag TAG]` | List items, optionally filtered by tag |
| `extract-papers` | Extract papers from AI/LLM posts |
| `unlike <id>` | Unlike a specific post |
| `review [--mode ai\|other\|all]` | Interactive terminal review |

## Configuration

Copy `config.example.yaml` to `config.yaml`. Key settings:

- **`user_id`** — Your XHS user ID (shown after `login`, or from your profile URL)
- **`tag_rules`** — List of tag names + keywords. Customize to match your interests
- **`fetch.max_scrolls_*`** — How far to scroll (more = more posts, but slower)
- **`paper_extraction`** — Settings for arXiv paper detection

## Paper Extraction

For posts tagged "AI/LLM", the tool can:

1. Open each post and extract text content
2. Find arXiv IDs (e.g., `2401.12345`) via regex
3. Extract paper titles from `《》` quotes and `Title:` patterns
4. Search the arXiv API for papers without explicit IDs
5. Store results in the likes database

## ⚠️ Important Notes

- **Anti-bot measures**: XHS has aggressive anti-bot detection. This tool uses a persistent browser profile (not headless) to appear as a normal user. Avoid running fetches too frequently.
- **Rate limiting**: The tool respects rate limits (especially for arXiv API). Don't modify wait times to be too aggressive.
- **Login session**: Your login session is stored in `data/browser_profile/`. Don't share this directory.
- **Local only**: All data stays on your machine. Nothing is uploaded anywhere.

## Contributing

Contributions welcome! Some ideas:

- Better like button detection for unlike
- Image OCR for paper extraction from screenshots
- Export to Notion/Obsidian
- Tag suggestions via LLM

## License

MIT
