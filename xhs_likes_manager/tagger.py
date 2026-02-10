"""Auto-tagging with configurable keyword rules."""

from .config import Config
from .utils import load_db, save_db, export_markdown


def auto_tag(title: str, text: str, tag_rules: list[dict]) -> list[str]:
    """Match tags based on keyword rules."""
    combined = (title + " " + text).lower()
    tags = []
    for rule in tag_rules:
        for kw in rule["keywords"]:
            if kw.lower() in combined:
                tags.append(rule["name"])
                break
    return tags if tags else ["其他"]


def tag_all(config: Config, collection: str = "likes") -> None:
    """Auto-tag all untagged items in a collection."""
    if collection == "likes":
        db_path, md_path, title = config.likes_file, config.likes_md, "小红书点赞"
    else:
        db_path, md_path, title = config.bookmarks_file, config.bookmarks_md, "小红书收藏夹"

    db = load_db(db_path)
    tagged_count = 0

    for item in db["items"]:
        if not item.get("tags"):
            item["tags"] = auto_tag(item["title"], item.get("desc", ""), config.tag_rules)
            tagged_count += 1

    save_db(db_path, db)
    export_markdown(db, md_path, title)
    print(f"🏷️  Tagged {tagged_count} items in {collection}")


def tag_item(config: Config, collection: str, item_id: str, tags: list[str]) -> None:
    """Add tags to a specific item."""
    if collection == "likes":
        db_path, md_path, title = config.likes_file, config.likes_md, "小红书点赞"
    else:
        db_path, md_path, title = config.bookmarks_file, config.bookmarks_md, "小红书收藏夹"

    db = load_db(db_path)
    for item in db["items"]:
        if item["id"] == item_id:
            existing = set(item.get("tags", []))
            existing.update(tags)
            item["tags"] = sorted(existing)
            save_db(db_path, db)
            export_markdown(db, md_path, title)
            print(f"🏷️  Tagged '{item['title']}' with: {', '.join(item['tags'])}")
            return

    print(f"❌ Item not found: {item_id}")
