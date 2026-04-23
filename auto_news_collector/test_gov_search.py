"""在gov.cn政策JSON中搜索目标新闻"""
import requests

url = "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json"
resp = requests.get(url, timeout=30)
data = resp.json()

print(f"政策JSON总共 {len(data)} 条")

# 搜索包含"工信部"或"七部门"的
for item in data[:100]:
    title = item.get('TITLE', '')
    if '工信部' in title or '七部门' in title:
        print(f"找到: {title}")
        print(f"URL: {item.get('URL', '')}")
