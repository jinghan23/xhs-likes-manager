"""Fetch likes and bookmarks via XHS API interception."""

import sys
from playwright.sync_api import sync_playwright

from .config import Config
from .auth import create_persistent_context, get_my_user_id
from .utils import load_db, save_db, export_markdown, now_cn

# XHS API patterns
COLLECT_API = "note/collect/page"
LIKE_API = "note/like/page"


def _fetch_by_tab(
    config: Config,
    tab_name: str,
    api_pattern: str,
    max_scrolls: int,
) -> list[dict]:
    """Click a tab on the profile page and intercept API responses."""
    all_notes: list[dict] = []
    fetch_cfg = config.fetch

    with sync_playwright() as p:
        context = create_persistent_context(p, config, headless=False)
        page = context.pages[0] if context.pages else context.new_page()

        user_id = config.user_id or get_my_user_id(page)
        if not user_id:
            print("❌ Not logged in. Run 'login' first.")
            context.close()
            sys.exit(1)
        print(f"👤 User ID: {user_id}")

        collected: list[dict] = []

        def capture_api(response):
            if api_pattern in response.url:
                try:
                    collected.append(response.json())
                except Exception:
                    pass

        page.on("response", capture_api)
        page.goto(
            f"{config.xhs_base_url}/user/profile/{user_id}",
            wait_until="networkidle",
        )
        page.wait_for_timeout(2000)

        tab = page.query_selector(f'.reds-tab-item:has-text("{tab_name}")')
        if tab:
            tab.click()
            page.wait_for_timeout(3000)
        else:
            print(f"⚠️  Could not find '{tab_name}' tab")
            context.close()
            return []

        for resp in collected:
            notes = resp.get("data", {}).get("notes", [])
            all_notes.extend(notes)
        print(f"   Initial: {len(all_notes)} items")

        prev_count = len(all_notes)
        no_change = 0
        scroll_wait = fetch_cfg.get("scroll_wait_ms", 2000)
        threshold = fetch_cfg.get("no_change_threshold", 3)

        for i in range(max_scrolls):
            collected.clear()
            page.evaluate("window.scrollBy(0, 1000)")
            page.wait_for_timeout(scroll_wait)

            for resp in collected:
                notes = resp.get("data", {}).get("notes", [])
                all_notes.extend(notes)

            curr = len(all_notes)
            if curr == prev_count:
                no_change += 1
                if no_change >= threshold:
                    break
            else:
                no_change = 0
                print(f"   Scroll {i + 1}: {curr} total")
            prev_count = curr

        context.close()

    # Deduplicate
    seen: set[str] = set()
    unique: list[dict] = []
    for note in all_notes:
        nid = note.get("note_id", "")
        if nid and nid not in seen:
            seen.add(nid)
            unique.append(note)

    return unique


def _process_notes(notes: list[dict], config: Config, db_path, md_path, md_title) -> int:
    """Merge fetched notes into the database."""
    timestamp = now_cn()
    db = load_db(db_path)
    existing_ids = {item["id"] for item in db["items"]}

    new_count = 0
    for note in notes:
        nid = note.get("note_id", "")
        if nid not in existing_ids:
            display_title = (
                note.get("display_title", "")
                or note.get("title", "")
                or f"笔记 {nid[:8]}"
            )
            user_info = note.get("user", {})
            cover = note.get("cover", {})
            item = {
                "id": nid,
                "title": display_title,
                "author": user_info.get("nickname", ""),
                "author_id": user_info.get("user_id", ""),
                "url": f"{config.xhs_base_url}/explore/{nid}",
                "cover": cover.get("url", "") if isinstance(cover, dict) else "",
                "type": note.get("type", ""),
                "tags": [],
                "desc": "",
                "note": "",
                "reviewed": False,
                "xsec_token": note.get("xsec_token", ""),
                "first_seen": timestamp,
                "saved_at": timestamp,
            }
            db["items"].append(item)
            new_count += 1

    db["last_fetch"] = timestamp
    save_db(db_path, db)
    export_markdown(db, md_path, md_title)
    return new_count


def fetch_likes(config: Config) -> int:
    """Fetch liked posts."""
    print("❤️ Fetching likes (点赞)...")
    max_scrolls = config.fetch.get("max_scrolls_likes", 50)
    notes = _fetch_by_tab(config, "点赞", LIKE_API, max_scrolls)
    new = _process_notes(notes, config, config.likes_file, config.likes_md, "小红书点赞")
    db = load_db(config.likes_file)
    print(f"\n✅ {len(notes)} found, {new} new. Total: {len(db['items'])}")
    return new


def fetch_bookmarks(config: Config) -> int:
    """Fetch bookmarked posts."""
    print("📚 Fetching bookmarks (收藏)...")
    max_scrolls = config.fetch.get("max_scrolls_bookmarks", 30)
    notes = _fetch_by_tab(config, "收藏", COLLECT_API, max_scrolls)
    new = _process_notes(
        notes, config, config.bookmarks_file, config.bookmarks_md, "小红书收藏夹"
    )
    db = load_db(config.bookmarks_file)
    print(f"\n✅ {len(notes)} found, {new} new. Total: {len(db['items'])}")
    return new
