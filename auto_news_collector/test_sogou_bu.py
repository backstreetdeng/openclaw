"""用搜狗搜索"部"相关新闻"""
import requests
import re
from datetime import datetime

# 搜索"XX部"相关政策新闻
queries = [
    "工信部 最新政策",
    "发改委 最新政策", 
    "财政部 最新政策",
    "商务部 最新政策",
]

for query in queries:
    url = f"https://www.sogou.com/web?query={requests.utils.quote(query)}&ie=utf8"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        # 提取摘要
        snippets = re.findall(r'<!--摘要开始-->([^<]+)<!--摘要结束-->', resp.text)
        print(f"\n【{query}】找到 {len(snippets)} 条")
        for s in snippets[:2]:
            print(f"  {s[:60]}...")
    except Exception as e:
        print(f"\n【{query}】失败: {e}")
