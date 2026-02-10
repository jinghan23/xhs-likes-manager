"""Shared utilities."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

CN_TZ = timezone(timedelta(hours=8))


def now_cn() -> str:
    """Return current time in CN timezone as formatted string."""
    return datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M")


def load_db(path: Path) -> dict:
    """Load a JSON database file."""
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"items": [], "last_fetch": None}


def save_db(path: Path, data: dict) -> None:
    """Save a JSON database file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def export_markdown(data: dict, md_path: Path, title: str) -> None:
    """Export items to a readable markdown file."""
    lines = [
        f"# {title}",
        "",
        f"最后更新: {data.get('last_fetch', 'N/A')}",
        f"总计: {len(data['items'])} 条",
        "",
    ]

    tagged: dict[str, list] = {}
    untagged: list = []
    for item in data["items"]:
        tags = item.get("tags", [])
        if tags:
            for t in tags:
                tagged.setdefault(t, []).append(item)
        else:
            untagged.append(item)

    for tag, items in sorted(tagged.items()):
        lines.append(f"## {tag}")
        lines.append("")
        for item in items:
            status = " ✅" if item.get("reviewed") else ""
            lines.append(
                f"- **[{item['title']}]({item['url']})** — "
                f"{item.get('author', '未知')}{status}"
            )
            if item.get("desc"):
                lines.append(f"  > {item['desc'][:100]}")
            if item.get("note"):
                lines.append(f"  📝 {item['note']}")
            lines.append("")

    if untagged:
        lines.append("## 未分类")
        lines.append("")
        for item in untagged:
            status = " ✅" if item.get("reviewed") else ""
            lines.append(
                f"- **[{item['title']}]({item['url']})** — "
                f"{item.get('author', '未知')}{status}"
            )
            if item.get("desc"):
                lines.append(f"  > {item['desc'][:100]}")
            if item.get("note"):
                lines.append(f"  📝 {item['note']}")
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
