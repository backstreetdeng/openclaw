"""检查JSON数据结构"""
import requests

url = 'https://www.gov.cn/yaowen/liebiao/YAOWENLIEBIAO.json'
resp = requests.get(url, timeout=30)
data = resp.json()

# 查看第一条的所有字段
print("第一条数据的所有字段:")
for item in data[:1]:
    for k, v in item.items():
        print(f"  {k}: {str(v)[:80]}")
