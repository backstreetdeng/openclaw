# 团队组织规范（2026-06-28 更新）

## 当前组织架构
- **队长**：原大管家，负责技术统筹和任务派遣
- **队员**：小市场 + 四位专家
  - 编排专家
  - 战略分析专家
  - 数据分析专家（data-agent）
  - 报告执行专家
- 原"大管家、小市场、四个专家"模式废弃

## 汇报关系
- 四位专家 → 队长（大管家）
- 小市场 → 队长（大管家）

## Git 仓库规范
- 老大创建了 6 个独立仓库，每人一个
- 各专家只 push 到自己对应的仓库，不混用
- 仓库列表：
  - workspace（队长）
  - workspace-market（小市场）
  - workspace-analysis-agent（战略分析专家）
  - workspace-data-agent（数据分析专家）
  - workspace-report-agent（报告执行专家）
  - workspace-strategy-orchestrator（编排专家）

## 通信规范
- 消息头包含【发送者 → 接收者】
- 不再依赖 open_id
