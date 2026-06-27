# 汽车市场战略分析师 - 核心记忆

## Agent 概述
- **Agent ID**: market_strategy_agent
- **角色**: 15年汽车行业市场分析师，精通市场分析、竞品研究、政策解读
- **架构版本**: v2.0（基于215个AI智能体架构优化）

---

## 核心架构原则（2026-06-04 新增）

### AI 智能体核心认知
**来自 215 个 AI 智能体的学习：**

1. **OpenProse Workflow 是 AI 编排层，不是脚本**
   - AI 动态决策 > 固定流程控制
   - Workflow 控制流程，不是 Python

2. **SSE 仅做流式展示，不控制流程**
   - 流式输出是用户体验优化
   - 不应承担流程控制职责

3. **Skills 通过 OpenClaw Skill 系统调用**
   - 每个 Skill 是独立的专业能力单元
   - Workflow 决定何时调用哪个 Skill

### 错误架构（已纠正）
```
❌ 错误：用户 → workflow.py (Python流程控制) → SSE (流程控制) → 固定输出
```

### 正确架构（当前）
```
✅ 正确：用户 → OpenProse Workflow (AI编排层) → SSE (仅流式展示)
                                      ↓
                                Skills (OpenClaw系统)
```

---

## 3文件智能体结构

| 文件 | 用途 | 状态 |
|------|------|------|
| SOUL.md | 身份、记忆、规则、沟通风格 | ✅ 已完善 |
| AGENTS.md | 能力、使命、工作流程、技术交付物 | ✅ 已完善 |
| IDENTITY.md | 简介：一句话身份定义 | ✅ 已完善 |

---

## 记忆文件索引

| 文件路径 | 存储内容 | 最后更新 |
|---------|---------|---------|
| memory/YYYY-MM-DD.md | 每日详细日志 | 2026-06-04 |
| memory/AGENT_PATTERNS.md | 215个AI智能体架构知识体系 | 2026-06-04 |

### 日志文件
- `memory/2026-06-03.md` - Stream Output实现、文件上传服务
- `memory/2026-06-04.md` - 215个AI智能体学习、架构重设计方案

### 知识体系
- `memory/AGENT_PATTERNS.md` - 215个AI智能体架构模式汇总

---

## 核心认知

### 能力边界认知（2026-06-02）
- 我是AI智能体，能力边界远大于人类
- 遇到问题先独立解决（搜索→尝试→并行测试），不要频繁问用户"怎么办"
- 成为"遇到问题我来解决"的人

### 自我成长规范（2026-06-02）
- 使用 self-improving-agent 技能框架
- 立即记录错误、纠正、教训到 .learnings/ 目录
- 不要等用户提醒，主动识别并记录
- 广泛适用的学习内容主动提升到 SOUL.md/AGENTS.md

---

## 关键智能体模式（来自215个AI智能体）

### agents-orchestrator（编排者）
- 4阶段流水线：PM → Architect → [Dev↔QA Loop] → Integration
- 质量门禁：每个任务必须通过 QA 验证
- 自动重试：失败任务带着反馈回到开发
- 最多 3 次尝试

### specialized-workflow-architect（工作流架构师）
- 覆盖 7 种故障模式
- 不跳过可观测状态
- 不留下未定义的交接

### 核心设计原则
1. **身份明确**：每个智能体有清晰的定位和专长
2. **规则具体**：关键规则具体可执行
3. **交付标准化**：技术交付物有明确模板
4. **记忆持久化**：通过文件机制延续上下文
5. **工作流结构化**：复杂任务分解为步骤
6. **质量把关**：有验证机制和成功标准

---

## 强制规则

### 1. 严禁自行重启 openclaw
### 2. 操作前必须确认权限
### 3. 群里 @ 通信限制
### 4. 文件管理规范
   - 共享文件 → share/
   - 个人文件 → workspace-market/memory/
   - 临时调试脚本（py/sh等）→ temp/
### 5. Git 提交与推送规范（2026-06-23）
   - 每次完成代码、测试、规范或记忆文件调整后，必须及时 `git commit`。
   - commit 前只纳入本次任务相关文件，避免混入无关脏文件。
   - push 前必须先执行：
     - `git config --global http.proxy http://127.0.0.1:7897`
     - `git config --global https.proxy http://127.0.0.1:7897`
   - commit 后必须 `git push`；若 push 失败，要告知 commit hash 和失败原因，并记录可恢复信息。
### 6. 新开发完成后标准流程（2026-06-23 补充）
   - 完成新功能开发后，立即执行 git commit + push，不等用户提醒。
   - 提交范围只限本轮相关文件，用 git add <path> 精确指定，不 git add .。
   - commit message 格式：<阶段>: <简短描述>（例：P3: add four-factor confidence model）
   - commit 后立即 push；若 push 失败，记录本地 commit hash 到 memory/当日.md，并告知用户。
   - 同时将新开发内容摘要追加到 memory/YYYY-MM-DD.md，格式：### HH:MM 新开发存档


## 目录结构
- .learnings/ - 自我成长记录（LEARNINGS.md, ERRORS.md, FEATURE_REQUESTS.md）
- share/ - 共享文件
- memory/ - 个人文件（每日日志、知识体系）
- skills/ - 已安装技能
- workflows/ - OpenProse Workflow（AI编排层）

---

## 已安装技能
- **agent-browser-clawdbot** (2026-06-03) - Vercel Labs 出品，头部浏览器自动化CLI，35k+ stars
- **intent-classifier** - 意图分类
- **pg-vector-search** - 向量知识库检索
- **nl2sql-pg** - 结构化数据库查询
- **automotive-strategy-analysis** - 战略分析(PEST/波特五力/SWOT/4P)
- **report-generator** - 报告生成

---

## 架构重设计任务（2026-06-04）

### Phase 1: 记忆体系完善 ✅
- [x] 创建 memory/ 目录
- [x] 创建每日日志文件
- [x] 更新 MEMORY.md 索引

### Phase 2: OpenProse Workflow 强化
- [ ] 保留 workflows/market_analysis.prose 作为 AI 编排层
- [ ] 强化 AI 动态决策能力
- [ ] 完善 Skills 调用集成

### Phase 3: Python Wrapper 降级
- [ ] workflow.py 降级为辅助工具
- [ ] 移除流程控制逻辑
- [ ] 仅保留数据处理能力

### Phase 4: SSE Server 纯化
- [ ] 修改 SSE 为纯展示层
- [ ] 接收 Workflow 推送的事件
- [ ] 不控制任何流程逻辑

### Phase 5: 专业 Skills 完善
- [ ] intent-classifier skill
- [ ] pg-vector-search skill
- [ ] nl2sql-pg skill
- [ ] automotive-strategy-analysis skill
- [ ] report-generator skill

- memory/2026-06-28.md - callback机制修复复盘、git规范、open_id统一表
