"""测试政策页面的JSON - 多种格式"""
import requests

url_base = "https://www.gov.cn/zhengce/zuixin/"
json_urls = [
    url_base + "ZHENGCEZUIXIN.json",
    url_base + "zuixin.json",
    url_base + "ZHENGCE.json",
]

for json_url in json_urls:
    try:
        resp = requests.get(json_url, timeout=10)
        print(f"{json_url}: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"  返回 {len(data)} 条")
    except Exception as e:
        print(f"{json_url}: 失败 - {str(e)[:50]}")
