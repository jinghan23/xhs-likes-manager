"""CLI entry point for XHS Likes Manager."""

import argparse
import sys
from pathlib import Path

from .config import Config
from .utils import load_db


def _find_config() -> str | None:
    """Look for config.yaml in current directory."""
    for name in ("config.yaml", "config.yml"):
        if Path(name).exists():
            return name
    return None


def _load_config(args) -> Config:
    config_path = getattr(args, "config", None) or _find_config()
    return Config(config_path)


def cmd_login(args):
    from .browser import login
    login(_load_config(args))


def cmd_fetch(args):
    from .browser import fetch_likes, fetch_bookmarks
    config = _load_config(args)
    kind = args.type
    full = getattr(args, "full", False)
    if kind in ("likes", "all"):
        fetch_likes(config, full=full)
    if kind in ("bookmarks", "all"):
        fetch_bookmarks(config, full=full)


def cmd_tag(args):
    from .tagger import tag_all
    config = _load_config(args)
    tag_all(config, "likes")
    tag_all(config, "bookmarks")


def cmd_stats(args):
    config = _load_config(args)
    for label, path in [("点赞", config.likes_file), ("收藏", config.bookmarks_file)]:
        data = load_db(path)
        items = data["items"]
        reviewed = sum(1 for i in items if i.get("reviewed"))
        removed = sum(1 for i in items if i.get("removed"))
        tagged = sum(1 for i in items if i.get("tags"))
        print(
            f"{label}: {len(items)} total | {reviewed} reviewed | "
            f"{removed} removed | {tagged} tagged | "
            f"last: {data.get('last_fetch', 'N/A')}"
        )

        # Tag distribution
        tag_counts: dict[str, int] = {}
        for item in items:
            for t in item.get("tags", []):
                tag_counts[t] = tag_counts.get(t, 0) + 1
        if tag_counts:
            dist = ", ".join(
                f"{t}({c})"
                for t, c in sorted(tag_counts.items(), key=lambda x: -x[1])
            )
            print(f"  Tags: {dist}")
        print()


def cmd_list(args):
    config = _load_config(args)
    tag_filter = args.tag

    for kind, path, label in [
        ("likes", config.likes_file, "点赞"),
        ("bookmarks", config.bookmarks_file, "收藏"),
    ]:
        data = load_db(path)
        items = data["items"]

        if tag_filter:
            items = [i for i in items if tag_filter in i.get("tags", [])]

        if not items:
            continue

        print(f"{'─' * 40}")
        print(f"📚 {label}: {len(items)} items")
        print()

        for i, item in enumerate(items, 1):
            reviewed = " ✅" if item.get("reviewed") else ""
            print(f"  {i:3}. {item['title']}{reviewed}")
            print(
                f"       👤 {item.get('author', '?')} | "
                f"🏷️ {', '.join(item.get('tags', [])) or '无标签'}"
            )
            print(f"       🔗 {item['url']}")
            if item.get("note"):
                print(f"       📝 {item['note']}")
            print()


def cmd_extract_papers(args):
    from .paper_extractor import extract_papers
    extract_papers(_load_config(args))


def cmd_unlike(args):
    from .browser import unlike_post
    unlike_post(_load_config(args), args.id)


def cmd_review(args):
    from .reviewer import review
    review(_load_config(args), mode=args.mode)


def main():
    parser = argparse.ArgumentParser(
        prog="xhs-likes-manager",
        description="Manage your Xiaohongshu (小红书) likes and bookmarks",
    )
    parser.add_argument(
        "-c", "--config", help="Path to config.yaml (default: ./config.yaml)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # login
    subparsers.add_parser("login", help="Open browser for manual XHS login")

    # fetch
    p_fetch = subparsers.add_parser("fetch", help="Fetch likes or bookmarks")
    p_fetch.add_argument(
        "type",
        nargs="?",
        default="all",
        choices=["likes", "bookmarks", "all"],
        help="What to fetch (default: all)",
    )
    p_fetch.add_argument(
        "--full",
        action="store_true",
        help="Full fetch (ignore known IDs, re-fetch everything)",
    )

    # tag
    subparsers.add_parser("tag", help="Auto-tag all untagged items")

    # stats
    subparsers.add_parser("stats", help="Show tag distribution and stats")

    # list
    p_list = subparsers.add_parser("list", help="List items")
    p_list.add_argument("--tag", help="Filter by tag name")

    # extract-papers
    subparsers.add_parser(
        "extract-papers", help="Extract papers from AI/LLM posts"
    )

    # unlike
    p_unlike = subparsers.add_parser("unlike", help="Unlike a post")
    p_unlike.add_argument("id", help="Post ID to unlike")

    # review
    p_review = subparsers.add_parser(
        "review", help="Interactive terminal review session"
    )
    p_review.add_argument(
        "--mode",
        default="ai",
        choices=["ai", "other", "all"],
        help="Review mode (default: ai)",
    )

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "login": cmd_login,
        "fetch": cmd_fetch,
        "tag": cmd_tag,
        "stats": cmd_stats,
        "list": cmd_list,
        "extract-papers": cmd_extract_papers,
        "unlike": cmd_unlike,
        "review": cmd_review,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
