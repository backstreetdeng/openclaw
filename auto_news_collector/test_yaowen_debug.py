"""调试要闻采集"""
import requests
from datetime import datetime

url = "https://www.gov.cn/yaowen/liebiao/YAOWENLIEBIAO.json"
resp = requests.get(url, timeout=30)
data = resp.json()

print(f"JSON总共 {len(data)} 条\n")

# 打印前10条的标题和日期
for i, item in enumerate(data[:10], 1):
    title = item.get('TITLE', '')[:40]
    date = item.get('DOCRELPUBTIME', '')[:10] if item.get('DOCRELPUBTIME') else ''
    print(f"{i}. [{date}] {title}")
