# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## 工作目录

- **主工作目录**: `E:\openclaw\workspace` （C盘空间有限，所有执行任务和结果都放在这里）
- **OpenClaw系统目录**: `C:\Users\11489\.openclaw` （系统文件，不放执行产物）
- **知识库**: `E:\openclaw\knowledge\MyVault` （Obsidian笔记，长期保存的任务产出）
- **临时脚本**: 所有Python、JavaScript等脚本文件必须放在 `E:\openclaw\workspace` 下，禁止写入C盘

## 文件生成规则

- **新脚本存放**: 统一放在 `E:\openclaw\workspace\note\` 子目录
- **旧临时文件**: 已整理到 `E:\openclaw\workspace\draft\`
- **Agent配置**: 带有SOUL.md的Agent配置已迁移到 `E:\openclaw\knowledge\MyVault\文档\工作区配置\`
- **任务产出**: 重要产出（报告、资讯等）必须保存到 Obsidian 知识库
- 如果不确定生成的文件放哪里，**先询问用户**

## Workspace 目录结构（2026-04-02整理）

```
E:\openclaw\workspace\
├── note\              # 🆕 新脚本统一存放目录
├── draft\             # 已清理的旧临时文件
├── local_kb\          # 知识库索引（正在使用）
├── memory\            # 记忆文件
├── weekly_news\       # 本周资讯任务
├── (旧任务文件夹)      # 保留不动
│   ├── AI_Trends_2026\
│   ├── car_matching\
│   ├── daily-chat\
│   ├── ppt_analysis\
│   ├── research\
│   └── wechat_output\
└── read_docx.py       # 读取docx工具脚本

E:\openclaw\knowledge\MyVault\文档\工作区配置\   # Agent配置备份
E:\openclaw\knowledge\MyVault\文档\每日简报\     # 任务产出归档
```

## 原则

1. **草稿纸 vs 课本**: 脚本是"草稿纸"（用完可删），知识库是"课本"（长期保留）
2. **任务完成标准**: 产出已存入 Obsidian 知识库 = 任务完成
3. **workspace 清理时机**: 产出归档后，workspace 过程文件可清理

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## PPT/Office 文档处理

### python-pptx 图表数据提取
```python
from pptx import Presentation
prs = Presentation('file.pptx')
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_chart:
            chart = shape.chart
            cats = [str(c) for c in chart.plots[0].categories]  # 分类轴
            for ser in chart.plots[0].series:
                vals = [round(float(v)*100, 1) for v in ser.values]  # 数值
```

### PPT 文本框写入（摘要条）
- 位置：y=0.95英寸（横线下方、图表上方）
- 文本框：left=0.3in, width=15.4in, height=0.6in
- 字体：微软雅黑，11pt，黑色，加粗

### PPT工作流（已验证）
1. python-pptx提取图表数据 → 主会话推理模型生成驱动型摘要
2. 子进程负责：复制文件 + 写入文本框 + 管理位置
3. 注意：子进程内不要依赖AI生成高质量摘要（环境限制）

---

Add whatever helps you do your job. This is your cheat sheet.
