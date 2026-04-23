"""调试JSON URL"""
import requests
import re

url = "https://www.gov.cn/yaowen/liebiao/"

# 构造JSON URL
base_url = url.rstrip('/')
path_parts = base_url.replace('https://www.gov.cn', '')
last_part = path_parts.split('/')[-1]
json_url = f"{base_url}{last_part.upper()}.json"

print(f"原始URL: {url}")
print(f"JSON URL: {json_url}")

# 测试请求
try:
    resp = requests.get(json_url, timeout=30)
    print(f"状态码: {resp.status_code}")
    print(f"响应前100字符: {resp.text[:100]}")
except Exception as e:
    print(f"请求失败: {e}")
