"""调试gov.cn JSON API"""
import requests

# 测试两个URL
urls_to_test = [
    ("要闻", "https://www.gov.cn/yaowen/liebiao/"),
    ("政策", "https://www.gov.cn/zhengce/zuixin/"),
]

for name, url in urls_to_test:
    base_url = url.rstrip('/')
    path_part = base_url.replace('https://www.gov.cn', '').strip('/')
    
    if path_part.startswith('yaowen'):
        json_path = path_part.upper().replace('/', '')
    else:
        parts = path_part.split('/')
        json_path = ''.join(reversed(parts)).upper()
    
    json_url = f"{base_url}/{json_path}.json"
    
    print(f"{name} URL: {json_url}")
    resp = requests.get(json_url, timeout=30)
    print(f"  状态: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  数据: {len(data)} 条")
    print()
