"""Unlike posts via browser automation."""

import json
from playwright.sync_api import sync_playwright

from .config import Config
from .auth import create_persistent_context
from .utils import load_db, save_db, now_cn


def unlike_post(config: Config, item_id: str) -> None:
    """Unlike a post by navigating to it and toggling the like button."""
    db = load_db(config.likes_file)
    item = None
    for i in db["items"]:
        if i["id"] == item_id:
            item = i
            break

    if not item:
        print(f"❌ Item not found: {item_id}")
        return

    url = item["url"]
    print(f"📝 {item['title']}")
    print(f"🔗 Opening: {url}")

    with sync_playwright() as p:
        context = create_persistent_context(p, config, headless=False)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Try to find the active like button
        like_btn = page.query_selector(
            '[class*="like"][class*="active"], '
            ".like-wrapper.active, "
            ".like-active, "
            'button[class*="like"].active'
        )

        if not like_btn:
            like_btn = page.query_selector(
                ".engage-bar .like-wrapper, "
                ".note-detail .like-wrapper, "
                '[data-type="like"]'
            )

        if not like_btn:
            # Inspect DOM for like-related elements
            result = page.evaluate(
                """() => {
                const candidates = document.querySelectorAll('[class*="like"], [class*="Like"]');
                const info = [];
                for (const el of candidates) {
                    info.push({
                        tag: el.tagName,
                        class: el.className,
                        hasActive: el.className.includes('active') || el.className.includes('Active'),
                    });
                }
                return info;
            }"""
            )

            for el_info in result:
                if el_info.get("hasActive"):
                    selector = "." + ".".join(el_info["class"].split())
                    try:
                        el = page.query_selector(selector)
                        if el:
                            like_btn = el
                            break
                    except Exception:
                        continue

        if like_btn:
            print("❤️ Found like button, clicking to unlike...")
            like_btn.click()
            page.wait_for_timeout(2000)
            print("✅ Clicked! Post should be unliked.")
        else:
            print("⚠️ Could not find like button automatically.")
            print("   You may need to unlike manually.")

        context.close()

    # Mark as removed in DB
    item["removed"] = True
    item["removed_at"] = now_cn()
    item["reviewed"] = True
    save_db(config.likes_file, db)
    print("🗑️ Marked as removed in database.")
