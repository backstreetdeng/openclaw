"""测试东方财富不同column"""
import requests

columns = ["101", "102", "103", "104", "105", "106"]

for col in columns:
    url = f"https://newsapi.eastmoney.com/kuaixun/v2/api/list?column={col}&limit=5&p=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            news = data.get('news', [])
            if news:
                title = news[0].get('title', '')[:40]
                print(f"column={col}: {len(news)}条, 示例: {title}")
    except Exception as e:
        print(f"column={col}: 错误")
