"""详细测试column=350 API"""
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
    'page_size': '20',
    'req_trace': str(int(time.time() * 1000)),
    'fields': 'code,showTime,title,mediaName,summary,image,url,uniqueUrl,Np_dst',
    'types': '1,20',
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.eastmoney.com/a/cgnjj.html'
}

resp = requests.get(url, params=params, headers=headers, timeout=30)
print(f"状态: {resp.status_code}")

data = resp.json()
news_list = data.get('data', {}).get('list', [])

print(f"返回 {len(news_list)} 条新闻\n")

# 显示前10条
for i, n in enumerate(news_list[:10], 1):
    title = n.get('title', '')[:50]
    media = n.get('mediaName', '')
    showtime = n.get('showTime', '')
    print(f"{i}. [{showtime}] {title}")
    print(f"   来源: {media}")
    print()
