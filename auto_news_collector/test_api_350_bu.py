"""检查column=350是否包含'部'关键字"""
import requests
import time

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
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.eastmoney.com/a/cgnjj.html'
}

resp = requests.get(url, params=params, headers=headers, timeout=30)
data = resp.json()
news_list = data.get('data', {}).get('list', [])

print(f"返回 {len(news_list)} 条国内经济新闻\n")

# 检查包含"部"的新闻
bu_keywords = ["部", "工信部", "发改委", "财政部", "商务部", "农业部", "教育部", "公安部", "科技部"]
found_bu = []
for n in news_list:
    title = n.get('title', '')
    if any(k in title for k in bu_keywords):
        found_bu.append(n)
        print(f"✅ [{n.get('showTime', '')}] {title}")

print(f"\n包含'部'的新闻: {len(found_bu)} 条")

# 显示总数
print(f"\n总条数: {len(news_list)}")
