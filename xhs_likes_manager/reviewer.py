"""Interactive review session management."""

import json
from pathlib import Path
from .config import Config
from .utils import load_db, save_db, now_cn


def _load_state(config: Config) -> dict:
    path = config.review_state_file
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "mode": "ai",
        "reviewed_ids": [],
        "session_start": None,
        "last_shown_id": None,
    }


def _save_state(config: Config, state: dict) -> None:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.review_state_file.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _get_items(data: dict, mode: str, reviewed_ids: set) -> list[tuple[int, dict]]:
    """Get unreviewed items filtered by mode."""
    items = []
    for i, item in enumerate(data["items"]):
        if item["id"] in reviewed_ids:
            continue
        tags = item.get("tags", [])
        if mode == "ai" and "AI/LLM" not in tags:
            continue
        if mode == "other" and "AI/LLM" in tags:
            continue
        items.append((i, item))
    return items


def review(config: Config, mode: str = "ai") -> None:
    """Run interactive terminal review session."""
    state = _load_state(config)
    state["mode"] = mode
    state["session_start"] = now_cn()

    data = load_db(config.likes_file)
    reviewed = set(state.get("reviewed_ids", []))
    items = _get_items(data, mode, reviewed)

    if not items:
        print("✅ All done! No more items to review.")
        return

    print(f"📋 Review session: {len(items)} {mode} posts to review")
    print("   Commands: [k]eep / [r]emove / [s]kip / [t]ag <tags> / [n]ote <text> / [q]uit\n")

    pos = 0
    while pos < len(items):
        idx, item = items[pos]
        tags = ", ".join(item.get("tags", []))
        print(f"─── [{pos + 1}/{len(items)}] ───")
        print(f"📌 {item['title']}")
        print(f"👤 {item['author']}  |  🏷️ {tags}")
        if item.get("desc"):
            print(f"📝 {item['desc'][:200]}")
        print(f"🔗 {item['url']}")
        print()

        cmd = input(">>> ").strip().lower()

        if cmd in ("k", "keep", ""):
            item["reviewed"] = True
            reviewed.add(item["id"])
            print("  ✅ Kept\n")
            pos += 1
        elif cmd in ("r", "remove"):
            item["reviewed"] = True
            item["removed"] = True
            item["removed_at"] = now_cn()
            reviewed.add(item["id"])
            print("  🗑️ Marked for removal\n")
            pos += 1
        elif cmd in ("s", "skip"):
            print("  ⏭️ Skipped\n")
            pos += 1
        elif cmd.startswith("t ") or cmd.startswith("tag "):
            new_tags = cmd.split(maxsplit=1)[1].split(",")
            new_tags = [t.strip() for t in new_tags if t.strip()]
            existing = set(item.get("tags", []))
            existing.update(new_tags)
            item["tags"] = sorted(existing)
            print(f"  🏷️ Tags: {', '.join(item['tags'])}\n")
        elif cmd.startswith("n ") or cmd.startswith("note "):
            note_text = cmd.split(maxsplit=1)[1]
            item["note"] = note_text
            print(f"  📝 Note added\n")
        elif cmd in ("q", "quit"):
            break
        else:
            print("  Unknown command. Use k/r/s/t/n/q\n")

    # Save
    state["reviewed_ids"] = list(reviewed)
    _save_state(config, state)
    save_db(config.likes_file, data)
    print(f"\n💾 Saved. Reviewed {len(reviewed)} items total.")
