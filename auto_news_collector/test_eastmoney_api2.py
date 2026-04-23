"""测试东方财富API获取国内经济新闻"""
import requests
from datetime import datetime

url = "https://newsapi.eastmoney.com/kuaixun/v2/api/list?column=102&limit=50&p=1"
headers = {'User-Agent': 'Mozilla/5.0'}

resp = requests.get(url, headers=headers, timeout=30)
data = resp.json()

news_list = data.get('news', [])
print(f"返回 {len(news_list)} 条新闻\n")

# 查找包含"部"的新闻
keywords = ["工信部", "发改委", "财政部", "商务部", "农业农村部", "公安部", "教育部"]

print("包含'部'的新闻:")
for n in news_list:
    title = n.get('title', '')
    if any(k in title for k in keywords):
        print(f"- {title}")
