"""测试东方财富API"""
import requests

url = "https://newsapi.eastmoney.com/kuaixun/v2/api/list?column=102&limit=20&p=1"
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    resp = requests.get(url, headers=headers, timeout=30)
    print(f"状态: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"返回数据: {str(data)[:500]}")
except Exception as e:
    print(f"错误: {e}")
