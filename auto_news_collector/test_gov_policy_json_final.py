"""测试政策的JSON API"""
import requests

url = "https://www.gov.cn/zhengce/zuixin/"
base_url = url.rstrip('/')
path_part = base_url.replace('https://www.gov.cn', '').strip('/')
parts = path_part.split('/')
json_path = ''.join(reversed(parts)).upper()
json_url = f"{base_url}/{json_path}.json"

print(f"政策JSON URL: {json_url}")

resp = requests.get(json_url, timeout=30)
print(f"状态: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"返回 {len(data)} 条")
    if data:
        print(f"第一条: {data[0].get('TITLE', '')[:50]}")
