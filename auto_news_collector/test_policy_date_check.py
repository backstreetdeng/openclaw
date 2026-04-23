"""检查政策日期"""
import requests
from datetime import datetime

url = "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json"
resp = requests.get(url, timeout=30)
data = resp.json()

# 检查前5条的日期
for i, item in enumerate(data[:5]):
    title = item.get('TITLE', '')[:30]
    date_str = item.get('DOC_REL_PUBTIME', '') or item.get('DOCRELPUBTIME', '')
    print(f"{i+1}. [{date_str}] {title}")
