"""Extract papers from AI/LLM posts and search arXiv API."""

import re
import time
import urllib.parse
import urllib.request
from playwright.sync_api import sync_playwright

from .config import Config
from .browser import create_persistent_context
from .utils import load_db, save_db, now_cn


def extract_paper_info(text: str) -> dict:
    """Extract paper titles and arXiv IDs from text."""
    arxiv_ids = list(set(re.findall(r"(\d{4}\.\d{4,5})", text)))

    # Titles in 《》 or "" quotes
    paper_titles = re.findall(r'[《""]([^》""]{5,100})[》""]', text)

    # "题目：" / "paper:" patterns
    english_titles = re.findall(
        r"(?:题目[：:]|paper[：:]|论文[：:]|Title[：:])\s*(.{10,120})",
        text,
        re.IGNORECASE,
    )
    paper_titles.extend(english_titles)
    paper_titles = list(set(paper_titles))

    is_paper = bool(
        arxiv_ids
        or paper_titles
        or any(
            k in text.lower()
            for k in ["arxiv", "论文", "paper", "题目：", "一句话总结"]
        )
    )

    return {
        "arxiv_ids": arxiv_ids,
        "paper_titles": paper_titles,
        "is_paper": is_paper,
    }


def search_arxiv(query: str, max_results: int = 3) -> list[tuple[str, str]]:
    """Search arXiv API for papers matching query."""
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query=all:{urllib.parse.quote(query)}"
        f"&max_results={max_results}&sortBy=relevance"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        text = resp.read().decode()
        ids = re.findall(
            r"<id>http://arxiv.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?)</id>", text
        )
        titles = re.findall(r"<title>(.*?)</title>", text, re.DOTALL)
        titles = [t.strip().replace("\n", " ") for t in titles[1:]]
        return list(zip(ids, titles))[:max_results]
    except Exception as e:
        print(f"  ⚠️ arXiv search failed: {e}")
        return []


def extract_papers(config: Config) -> None:
    """Extract papers from AI/LLM tagged posts."""
    db = load_db(config.likes_file)
    ai_items = [
        item
        for item in db["items"]
        if "AI/LLM" in item.get("tags", []) and not item.get("papers_extracted")
    ]

    if not ai_items:
        print("No AI/LLM posts to process.")
        return

    print(f"📖 Processing {len(ai_items)} AI/LLM posts...")
    pe_cfg = config.paper_extraction
    rate_limit = pe_cfg.get("arxiv_rate_limit_sec", 1.0)
    max_results = pe_cfg.get("arxiv_max_results", 3)
    load_wait = pe_cfg.get("page_load_wait_ms", 4000)

    results = []
    with sync_playwright() as p:
        ctx = create_persistent_context(p, config, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        for item in ai_items:
            xsec = item.get("xsec_token", "")
            url = (
                f"{config.xhs_base_url}/explore/{item['id']}"
                f"?xsec_token={xsec}&xsec_source=pc_collect"
            )
            print(f"\n  📄 {item['title']}")

            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(load_wait)

            content = page.evaluate(
                """() => {
                const title = document.querySelector('#detail-title');
                const desc = document.querySelector('#detail-desc, .note-text');
                const imgs = document.querySelectorAll('.swiper-slide img, .note-slider-img img');
                return {
                    title: title?.innerText?.trim() || '',
                    text: desc?.innerText?.trim() || '',
                    image_count: imgs.length,
                };
            }"""
            )

            text = content["text"]
            info = extract_paper_info(text)

            # Store description if not already present
            if not item.get("desc") and text:
                item["desc"] = text[:500]

            # Search arXiv for papers without IDs
            if info["is_paper"] and not info["arxiv_ids"] and info["paper_titles"]:
                for pt in info["paper_titles"][:2]:
                    print(f"    🔍 Searching arXiv: {pt[:60]}")
                    arxiv_results = search_arxiv(pt, max_results)
                    time.sleep(rate_limit)
                    if arxiv_results:
                        for aid, atitle in arxiv_results:
                            aid_clean = re.sub(r"v\d+$", "", aid)
                            info["arxiv_ids"].append(aid_clean)
                            print(f"       → {aid_clean}: {atitle[:60]}")

            # Determine status
            has_id = bool(info["arxiv_ids"] or info["paper_titles"])
            text_short = len(text) < 100

            if has_id:
                status = "extracted"
            elif info["is_paper"] and content["image_count"] > 0 and text_short:
                status = "needs_vision"
            elif info["is_paper"]:
                status = "no_id_found"
            else:
                status = "insight"

            result = {
                "id": item["id"],
                "status": status,
                "paper_titles": info["paper_titles"],
                "arxiv_ids": info["arxiv_ids"],
                "arxiv_links": [f"https://arxiv.org/abs/{a}" for a in info["arxiv_ids"]],
                "text_length": len(text),
                "image_count": content["image_count"],
            }
            results.append(result)

            item["papers_extracted"] = True
            item["paper_info"] = result
            print(f"    {'✅' if status == 'extracted' else '⚠️'} {status}")

        ctx.close()

    save_db(config.likes_file, db)

    # Summary
    extracted = sum(1 for r in results if r["status"] == "extracted")
    print(f"\n✅ Done: {extracted}/{len(results)} papers extracted")
    print(f"   Results saved to likes database")
