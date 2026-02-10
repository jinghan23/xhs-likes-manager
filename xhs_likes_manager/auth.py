"""Browser context management and login."""

from playwright.sync_api import sync_playwright, BrowserContext, Playwright

from .config import Config


def create_persistent_context(
    playwright: Playwright, config: Config, headless: bool = False
) -> BrowserContext:
    """Create a persistent browser context with anti-detection settings."""
    config.browser_profile_dir.mkdir(parents=True, exist_ok=True)
    browser_cfg = config.browser
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(config.browser_profile_dir),
        headless=headless,
        viewport={
            "width": browser_cfg["viewport_width"],
            "height": browser_cfg["viewport_height"],
        },
        locale=browser_cfg["locale"],
        args=[f"--lang={browser_cfg['locale']}"],
        user_agent=browser_cfg["user_agent"],
    )
    return context


def get_my_user_id(page) -> str | None:
    """Detect logged-in user ID from XHS API response."""
    user_id = None

    def capture(response):
        nonlocal user_id
        if "user/me" in response.url:
            try:
                data = response.json()
                uid = data.get("data", {}).get("user_id")
                guest = data.get("data", {}).get("guest", True)
                if uid and not guest:
                    user_id = uid
            except Exception:
                pass

    page.on("response", capture)
    page.goto("https://www.xiaohongshu.com", wait_until="networkidle")
    page.wait_for_timeout(3000)
    page.remove_listener("response", capture)
    return user_id


def login(config: Config) -> None:
    """Open browser for manual XHS login."""
    print("🔐 Opening browser for XHS login...")
    print("   Log in manually, then press Enter here.\n")
    with sync_playwright() as p:
        context = create_persistent_context(p, config, headless=False)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(config.xhs_base_url)
        input("⏳ Press Enter after login... ")
        uid = get_my_user_id(page)
        if uid:
            print(f"✅ Logged in! User ID: {uid}")
            print(f"   Add this to your config.yaml: user_id: \"{uid}\"")
        else:
            print("⚠️  Could not verify login, but browser profile saved.")
        context.close()
