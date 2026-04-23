# 公众号信息获取技能（2026-03-19）

## 核心技能1：wechat-article-search

**路径：** `~/.openclaw/workspace/skills/wechat-article-search/`

**用途：** 搜索微信公众号文章，返回标题、摘要、时间、来源公众号、链接

**依赖安装：**
```bash
cd ~/.openclaw/workspace/skills/wechat-article-search
npm install cheerio  # 已在本地安装
```

**使用方法：**
```bash
node scripts/search_wechat.js "关键词" -n 10 -r
```
- `-n 10`：返回10条结果（最大50）
- `-r`：解析真实微信文章URL（mp.weixin.qq.com）
- `-o result.json`：输出到文件

**输出字段：** title、url、summary、datetime、date_text、date_description、source

**注意：**
- 不带 `-r` 只返回搜狗中转链接，无法直接访问
- **带 `-r`** 可解析出真实微信文章URL，成功率约90%
- 搜狗微信有JS混淆反爬，直接网页抓取会返回hex编码内容

---

## 核心技能2：Agent Browser

**用途：** Rust/Playwright 驱动的无头浏览器自动化，可渲染JS页面、绕过微信反爬

**安装状态：** ✅ Chromium 已安装（agent-browser 0.18.0）

**核心命令：**
```bash
agent-browser open <url>         # 打开页面
agent-browser snapshot -c        # 获取内容快照（compact）
agent-browser snapshot -i        # 获取可交互元素
agent-browser screenshot <path>  # 截图
agent-browser close              # 关闭
```

**优势：**
- 完全绕过微信反爬，渲染JS动态内容
- 可获取公众号文章全文（含格式、数据、图片引用）
- 支持截图保存

---

## 组合工作流（最优方案）

```
Step 1: wechat-article-search（搜索）
   node search_wechat.js "公众号名" -n 10 -r
   → 获取真实 mp.weixin.qq.com URL

Step 2: Agent Browser（验证/抓取）
   agent-browser open <微信文章URL>
   agent-browser snapshot -c
   → 获取完整渲染后的文章内容
```

---

## 关键发现

1. **微信公众号反爬机制：**
   - 搜狗微信搜索：JS混淆+hex编码，Python直接抓取只能获取骨架
   - mp.weixin.qq.com直接访问：无Cookie会触发验证码（wappoc_appmsgcaptcha）
   - Agent Browser：完全绕过，使用Playwright渲染，可获取完整内容

2. **wechat-article-search -r 参数重要性：**
   - 不带 `-r`：返回 weixin.sogou.com 中转链接（不可直接访问微信文章）
   - 带 `-r`：解析出真实 mp.weixin.qq.com URL，可配合 Agent Browser 使用

3. **微信公众号命名特点：**
   - 搜索公众号建议同时用关键词+ID（如"汽车像素 autopix"）提高精准度
   - 同一公众号文章可能出现在不同转载账号下，需认准 source 字段

---

## 已验证可正常获取的公众号示例

| 公众号 | 最近文章日期 | 状态 |
|--------|------------|------|
| 动力系统技术 | 2026-03-18 | ✅ |
| 汽车像素 | 2026-03-15 | ✅ |
| 盖世汽车每日速递 | 2026-03-09 | ✅ |


---

## 重要工作流学习（2026-03-19）

### PPT图表数据提取 + 驱动型摘要生成工作流

**项目背景：** 红旗C200用户问题调研PPT（137页）

**核心发现：**
- 子进程无法调用AI推理模型生成高质量摘要
- 主会话（MiniMax-M2.7推理模式）可以生成业务驱动型摘要
- python-pptx可以完整提取图表数据

**已验证的正确工作流：**
1. python-pptx提取所有图表数据（categories + series.values）
2. 主会话用推理模型分析数据 → 生成驱动型摘要
3. 子进程写入PPT（复制文件 + 插入文本框 + 管理位置）

**关键参数：**
- 文本框位置：y=0.95英寸
- 文本框规格：left=0.3in, width=15.4in, height=0.6in
- 字体：微软雅黑，11pt，黑色，加粗

**学习记录：** 已同步记录到 .learnings/LEARNINGS.md 和 TOOLS.md
