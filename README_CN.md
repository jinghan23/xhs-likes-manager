# XHS Likes Manager — 小红书点赞/收藏管理工具

本地管理你的小红书点赞和收藏内容：导出、分类、标签、审阅。

## 为什么需要这个工具？

小红书没有搜索、标签或管理点赞/收藏内容的功能。点赞几百条之后，找任何东西都变得不可能。这个工具把数据导出到本地，让你按自己的方式整理。

## 功能

- 📥 **导出** — 通过浏览器自动化导出所有点赞和收藏
- 🏷️ **自动标签** — 根据可配置的关键词规则分类
- 📄 **论文提取** — 从AI/ML帖子中查找arXiv论文
- 📋 **交互式审阅** — 终端审阅工作流（保留/删除/标签/备注）
- 👎 **取消点赞** — 通过浏览器自动化取消点赞
- 📊 **统计** — 查看标签分布和进度

## 快速开始

```bash
# 安装
git clone https://github.com/jinghan23/xhs-likes-manager.git
cd xhs-likes-manager
pip install -e .
playwright install chromium

# 配置
cp config.example.yaml config.yaml
# 编辑 config.yaml

# 登录（会打开浏览器，手动登录）
python -m xhs_likes_manager login

# 导出点赞和收藏
python -m xhs_likes_manager fetch

# 自动标签
python -m xhs_likes_manager tag

# 查看统计
python -m xhs_likes_manager stats

# 交互式审阅
python -m xhs_likes_manager review --mode ai
```

## 命令

| 命令 | 说明 |
|------|------|
| `login` | 打开浏览器手动登录 |
| `fetch [likes\|bookmarks\|all]` | 导出数据 |
| `tag` | 自动标签所有未标签内容 |
| `stats` | 显示标签统计 |
| `list [--tag TAG]` | 列出内容 |
| `extract-papers` | 从AI帖子提取论文 |
| `unlike <id>` | 取消指定帖子的点赞 |
| `review [--mode ai\|other\|all]` | 交互式审阅 |

## ⚠️ 注意事项

- 小红书有反爬检测，本工具使用持久化浏览器配置（非无头模式）模拟正常用户，请勿频繁运行
- 登录信息保存在 `data/browser_profile/`，请勿分享此目录
- 所有数据保存在本地，不会上传任何内容

## License

MIT
