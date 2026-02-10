"""Configuration loading and defaults."""

import yaml
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = {
    "user_id": "",
    "data_dir": "./data",
    "browser_profile_dir": "./data/browser_profile",
    "xhs_base_url": "https://www.xiaohongshu.com",
    "browser": {
        "viewport_width": 1280,
        "viewport_height": 900,
        "locale": "zh-CN",
        "user_agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
    },
    "fetch": {
        "max_scrolls_likes": 50,
        "max_scrolls_bookmarks": 30,
        "scroll_wait_ms": 2000,
        "no_change_threshold": 3,
    },
    "tag_rules": [
        {
            "name": "AI/LLM",
            "keywords": [
                "llm", "大模型", "gpt", "transformer", "预训练", "fine-tun", "微调",
                "强化学习", "reinforcement", "rl ", "rlhf", "grpo", "reasoning",
                "推理", "思维链", "chain-of-thought", "cot", "agent", "tool use",
                "论文", "paper", "arxiv", "distill", "蒸馏", "alignment", "对齐",
                "多模态", "multimodal", "embedding", "token", "attention",
                "deepseek", "qwen", "claude", "openai", "anthropic", "模型",
                "神经网络", "训练", "scaling", "benchmark", "nlp", "self-evolving",
                "reward", "prompt", "inference", "tta", "test-time", "agentic",
                "context engineering", "survey",
            ],
        },
        {
            "name": "编程",
            "keywords": [
                "leetcode", "算法", "题单", "coding", "编程", "python", "代码",
                "开源", "github", "debug", "工程", "api", "框架", "cuda",
            ],
        },
        {
            "name": "学术/PhD",
            "keywords": [
                "phd", "博士", "科研", "学术", "导师", "读博", "研究生",
                "人才计划", "icml", "neurips", "iclr",
            ],
        },
        {
            "name": "美食",
            "keywords": [
                "美食", "餐厅", "好吃", "做饭", "菜谱", "咖啡", "日料",
                "火锅", "甜品", "一人食",
            ],
        },
        {
            "name": "旅行",
            "keywords": [
                "旅行", "旅游", "攻略", "景点", "滑雪", "崇礼", "酒店",
                "雪场", "雪道",
            ],
        },
        {
            "name": "体育",
            "keywords": [
                "球员", "比赛", "冬奥", "奥运", "短道", "足球", "篮球",
                "滑冰", "运动", "冰舞",
            ],
        },
        {
            "name": "小说/书评",
            "keywords": [
                "小说", "书评", "女主", "男主", "jj", "晋江", "耽美",
                "推荐文", "书单", "章小蕙",
            ],
        },
        {
            "name": "生活",
            "keywords": [
                "租房", "搬家", "理财", "省钱", "穿搭", "护肤", "健身",
                "攒钱", "正骨",
            ],
        },
    ],
    "paper_extraction": {
        "arxiv_rate_limit_sec": 1.0,
        "arxiv_max_results": 3,
        "content_selectors": ["#detail-title", "#detail-desc", ".note-text"],
        "page_load_wait_ms": 4000,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    """Application configuration."""

    def __init__(self, config_path: str | Path | None = None):
        self._data = DEFAULT_CONFIG.copy()
        if config_path:
            path = Path(config_path)
            if path.exists():
                with open(path) as f:
                    user_config = yaml.safe_load(f) or {}
                self._data = _deep_merge(DEFAULT_CONFIG, user_config)

        # Resolve paths
        self._base_dir = Path(config_path).parent if config_path else Path.cwd()

    def _resolve_path(self, p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = self._base_dir / path
        return path

    @property
    def user_id(self) -> str:
        return self._data.get("user_id", "")

    @user_id.setter
    def user_id(self, value: str):
        self._data["user_id"] = value

    @property
    def data_dir(self) -> Path:
        return self._resolve_path(self._data["data_dir"])

    @property
    def browser_profile_dir(self) -> Path:
        return self._resolve_path(self._data["browser_profile_dir"])

    @property
    def xhs_base_url(self) -> str:
        return self._data["xhs_base_url"]

    @property
    def browser(self) -> dict:
        return self._data["browser"]

    @property
    def fetch(self) -> dict:
        return self._data["fetch"]

    @property
    def tag_rules(self) -> list[dict]:
        return self._data["tag_rules"]

    @property
    def paper_extraction(self) -> dict:
        return self._data["paper_extraction"]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    # Convenience paths
    @property
    def likes_file(self) -> Path:
        return self.data_dir / "likes.json"

    @property
    def bookmarks_file(self) -> Path:
        return self.data_dir / "bookmarks.json"

    @property
    def likes_md(self) -> Path:
        return self.data_dir / "likes.md"

    @property
    def bookmarks_md(self) -> Path:
        return self.data_dir / "bookmarks.md"

    @property
    def review_state_file(self) -> Path:
        return self.data_dir / "review_state.json"
