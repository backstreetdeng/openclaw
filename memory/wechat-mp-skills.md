# 微信公众号文章获取技能笔记

## 已验证技能

### 1. wechat-article-search
- **位置**：`~/.openclaw/workspace/skills/wechat-article-search/`
- **原理**：搜狗微信搜索索引
- **用法**：`node skills/wechat-article-search/scripts/search_wechat.js "关键词" -n 10`
- **局限**：关键词搜索，无法精确指定公众号名称

### 2. wechat-toolkit
- **位置**：`~/.openclaw/workspace/skills/wechat-toolkit/`
- **模块**：搜索、下载、洗稿、发布
- **搜索用法**：`node skills/wechat-toolkit/scripts/search/search_wechat.js "关键词" -n 10 -r`
- **局限**：同样是搜狗搜索，关键词匹配而非公众号筛选

### 3. wechat-article-aggregator
- **位置**：`~/.openclaw/workspace/skills/wechat-article-aggregator/`
- **原理**：mptext.top API
- **用法**：`python scripts/fetch_articles.py --api-key KEY --fakeids "公众号名或fakeid" --limit 5`
- **优势**：可按公众号名称获取，有预置账号列表
- **局限**：需要API Key，预置列表只有8个AI类公众号

## 关键限制

**搜狗搜索无法精确查找指定公众号**。搜索"汽车像素"返回的是包含该关键词的文章，而非"汽车像素"公众号发布的文章。

## 获取指定公众号文章的方法

1. 获取公众号的fakeid（唯一标识）
2. 使用mptext.top API（需申请API Key）
3. 将公众号添加到预置列表

## 技能优先级（获取公众号文章）

1. **首选**：wechat-article-aggregator（如果知道fakeid或公众号在预置列表）
2. **备选**：wechat-toolkit / wechat-article-search（关键词搜索，结果不精准）
3. **注意**：所有技能都依赖外部服务，可能受反爬限制

---

_创建时间：2026-03-25_
