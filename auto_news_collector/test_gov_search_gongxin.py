"""在gov.cn政策JSON中搜索工信部新闻"""
import requests

url = "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json"
resp = requests.get(url, timeout=30)
data = resp.json()

print(f"政策JSON总共 {len(data)} 条\n")

# 搜索"工信部"
print("包含'工信部'的政策新闻:")
found = []
for item in data:
    title = item.get('TITLE', '')
    if '工信部' in title:
        date = item.get('DOCRELPUBTIME', '')[:10] if item.get('DOCRELPUBTIME') else ''
        found.append((date, title))
        print(f"[{date}] {title}")

print(f"\n总共找到 {len(found)} 条")

# 搜索"七部门"
print("\n包含'七部门'的政策新闻:")
for item in data[:200]:
    title = item.get('TITLE', '')
    if '七部门' in title:
        date = item.get('DOCRELPUBTIME', '')[:10] if item.get('DOCRELPUBTIME') else ''
        print(f"[{date}] {title}")
