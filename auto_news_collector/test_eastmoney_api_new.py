"""测试东方财富国内经济API"""
import requests

url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns?client=web&biz=web_news_col&column=350&order=1&needInteractData=0&page_index=1&page_size=20&fields=code,showTime,title,mediaName,summary,image,url,uniqueUrl,Np_dst&types=1,20"
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    resp = requests.get(url, headers=headers, timeout=30)
    print(f"状态: {resp.status_code}")
    data = resp.json()
    print(f"返回数据: {str(data)[:500]}")
except Exception as e:
    print(f"错误: {e}")
