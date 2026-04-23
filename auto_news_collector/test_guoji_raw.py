"""检查国际经济API返回的新闻"""
import requests
import time

url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
params = {
    'client': 'web',
    'biz': 'web_news_col',
    'column': '351',
    'order': '1',
    'needInteractData': '0',
    'page_index': '1',
    'page_size': '20',
    'req_trace': str(int(time.time() * 1000)),
    'fields': 'code,showTime,title,mediaName,summary,image,url,uniqueUrl,Np_dst',
    'types': '1,20',
}
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://finance.eastmoney.com/a/cgjjj.html'
}

resp = requests.get(url, params=params, headers=headers, timeout=30)
data = resp.json()
news_list = data.get('data', {}).get('list', [])

print(f"国际经济API返回 {len(news_list)} 条\n")

# 检查是否包含"美联储"
has_meilian = False
for n in news_list:
    title = n.get('title', '')
    if '美联储' in title:
        has_meilian = True
        print(f"包含美联储: {title}")

if not has_meilian:
    print("没有包含'美联储'的新闻，前10条：")
    for n in news_list[:10]:
        print(f"  - {n.get('title', '')[:50]}")
