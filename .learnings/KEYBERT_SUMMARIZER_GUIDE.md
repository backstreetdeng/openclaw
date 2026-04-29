# KeyBERT中文摘要工具 - 大管家使用指南
更新时间：2026-04-24

## 一、工具位置

```
C:\Users\11489\openclaw_tools\
├── keybert_summarizer.py    # KeyBERT方案（推荐）
└── chinese_summarizer.py    # jieba方案（备用）
```

## 二、调用方法

### 方式1：命令行
```bash
python keybert_summarizer.py <文本> [输出文件]
```

### 方式2：Python代码
```python
import sys
sys.path.insert(0, r'C:\Users\11489\openclaw_tools')

from keybert_summarizer import summarize, summarize_with_info

# 简单摘要
summary = summarize(text, max_len=250)

# 带详细信息
result = summarize_with_info(text)
# 返回字典：
# {
#     'summary': '摘要文本...',
#     'original_len': 332,
#     'summary_len': 238,
#     'keywords': [('关键词1', 0.6554), ...],
#     'reduction': 28.3
# }
```

## 三、返回值

| 字段 | 类型 | 说明 |
|------|------|------|
| summary | str | 摘要文本（约200-250字） |
| original_len | int | 原文长度 |
| summary_len | int | 摘要长度 |
| keywords | list | 关键词列表 |
| reduction | float | 压缩率(%) |

## 四、注意事项

1. **离线可用**：不需要网络连接
2. **文本长度**：原文<=200字直接返回，>200字提炼至200-250字
3. **备用方案**：如果KeyBERT加载失败，使用 chinese_summarizer.py

## 五、环境变量（如果需要）
```python
import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HOME'] = r'C:\Users\11489\.cache\huggingface'
```