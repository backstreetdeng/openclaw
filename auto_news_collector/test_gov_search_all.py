"""搜索gov.cn全部政策"""
import requests

url = "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json"
resp = requests.get(url, timeout=30)
data = resp.json()

print(f"政策JSON总共 {len(data)} 条")

# 搜索包含"工信部"或"七部门"的
found = []
for item in data:
    title = item.get('TITLE', '')
    if '工信部' in title or '七部门' in title:
        found.append(item)
        print(f"找到: {title}")
        print(f"URL: {item.get('URL', '')}")
        print()

print(f"总共找到 {len(found)} 条")
