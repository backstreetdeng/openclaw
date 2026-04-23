"""测试东方财富国内经济API"""
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
headers = {'User-Agent': 'Mozilla/5.0'}

resp = requests.get(url, params=params, headers=headers, timeout=30)
print(f"状态: {resp.status_code}")
data = resp.json()
print(f"code: {data.get('code')}")
if data.get('data'):
    news_list = data['data'].get('list', [])
    print(f"返回 {len(news_list)} 条新闻")
    for n in news_list[:5]:
        print(f"- {n.get('title', '')[:50]}")
else:
    print(f"错误: {data.get('message')}")
