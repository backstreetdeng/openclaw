"""调试JSON API"""
import requests

# 测试要闻
yaowen_url = "https://www.gov.cn/yaowen/liebiao/"
base = yaowen_url.rstrip('/')
path_part = base.replace('https://www.gov.cn', '').strip('/')
parts = path_part.split('/')
json_path = ''.join(reversed(parts)).upper()
yaowen_json_url = f"{base}/{json_path}.json"

print(f"要闻JSON URL: {yaowen_json_url}")
resp = requests.get(yaowen_json_url, timeout=30)
print(f"要闻状态: {resp.status_code}, 前50字符: {resp.text[:50]}")

# 测试政策
zhengce_url = "https://www.gov.cn/zhengce/zuixin/"
base = zhengce_url.rstrip('/')
path_part = base.replace('https://www.gov.cn', '').strip('/')
parts = path_part.split('/')
json_path = ''.join(reversed(parts)).upper()
zhengce_json_url = f"{base}/{json_path}.json"

print(f"\n政策JSON URL: {zhengce_json_url}")
resp = requests.get(zhengce_json_url, timeout=30)
print(f"政策状态: {resp.status_code}, 前50字符: {resp.text[:50]}")
