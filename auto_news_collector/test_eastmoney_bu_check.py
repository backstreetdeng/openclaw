"""检查国内经济API中的"部"新闻"""
import requests
import time
from datetime import datetime

url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
params = {
    'client': 'web',
    'biz': 'web_news_col',
    'column': '350',
    'order': '1',
    'needInteractData': '0',
    'page_index': '1',
    'page_size': '50',
    'req_trace': str(int(time.time() * 1000)),
    'fields': 'code,showTime,title,mediaName,summary,image,url,uniqueUrl,Np_dst',
    'types': '1,20',
}
headers = {'User-Agent': 'Mozilla/5.0'}

resp = requests.get(url, params=params, headers=headers, timeout=30)
data = resp.json()
news_list = data.get('data', {}).get('list', [])

print(f"总共 {len(news_list)} 条新闻\n")

# 查找包含"部"的新闻
bu_keywords = ["部", "工信部", "发改委", "财政部", "商务部", "农业部", "教育部"]
found = []
for n in news_list:
    title = n.get('title', '')
    showtime = n.get('showTime', '')
    if any(k in title for k in bu_keywords):
        found.append(n)
        print(f"✅ [{showtime}] {title}")

print(f"\n包含'部'的新闻: {len(found)} 条")

# 没有"部"的，检查其他关键字
print("\n其他热门新闻:")
for n in news_list[:10]:
    print(f"- {n.get('title', '')[:50]}")
