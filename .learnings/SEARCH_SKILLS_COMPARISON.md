# 搜索类Skill对比与选用经验（2026-04-29）

## 结论

### 1. cn-web-search vs multi-search-engine
- **国内中文搜索优先选 cn-web-search**（独家集思录/ArXiv/Stack Overflow/GitHub Trending）
- **需要Google/WolframAlpha时用 multi-search-engine**（国内可访问）
- 两者互补，不是替代关系

### 2. cn-web-search vs baidu-search
- **cn-web-search**：完全免费，22个引擎聚合，但输出原始HTML需二次解析
- **baidu-search**：百度AI搜索API，返回JSON结构化结果，每天100次免费额度（需配置BAIDU_API_KEY）
- **建议**：日常轻量用cn-web-search，高质量需求用baidu-search

### 3. 百度API免费额度确认
- 百度千帆AI Search：每天100次免费额度
- 配置：`BAIDU_API_KEY` 环境变量（已配置在用户环境）
- **无法通过API查询剩余额度**，需手动访问 https://console.bce.baidu.com/qianfan/ais/console/overview 查看

### 4. 国内网络状况
| 引擎 | 状态 |
|------|------|
| DuckDuckGo | ❌ 被墙 |
| Brave Search | ❌ 被墙 |
| Google | ❌ 被墙 |
| 百度 | ⚠️ 可用但有人机验证 |
| 搜狗 | ✅ 正常 |
| 360 | ✅ 正常 |
| 头条搜索 | ✅ 正常 |
| 东方财富 | ✅ 正常 |
| WolframAlpha | ✅ 正常 |

### 5. 汽车资讯源覆盖
- 盖世汽车/汽车之家/懂车帝/太平洋：JS渲染页面，**agent-browser**最稳
- 微信公众号：**wechat-article-fetcher / wechat-article-search**
- 财经：**cn-web-search**（东方财富/集思录）
- agent-browser skill：适用于所有JS渲染/反爬强的站点

## 来源
- 整理自 2026-04-29 与老大的技能调研对话
