"""测试国际经济column值"""
import requests
import time

# 测试不同的column
for col in ["351", "352", "353", "354", "355"]:
    url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
    params = {
        'client': 'web',
        'biz': 'web_news_col',
        'column': col,
        'order': '1',
        'needInteractData': '0',
        'page_index': '1',
        'page_size': '5',
        'req_trace': str(int(time.time() * 1000)),
        'fields': 'code,showTime,title,mediaName,summary,image,url,uniqueUrl,Np_dst',
        'types': '1,20',
    }
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        news_list = data.get('data', {}).get('list', [])
        if news_list:
            title = news_list[0].get('title', '')[:40]
            print(f"column={col}: {len(news_list)}条, 示例: {title}")
        else:
            print(f"column={col}: 无数据")
    except Exception as e:
        print(f"column={col}: 错误")
