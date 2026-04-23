"""搜索"工信部等七部门"新闻"""
import requests

# 用必应收索
url = "https://cn.bing.com/search?q=工信部等七部门+统筹利用+两新+石化化工+2026"
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    resp = requests.get(url, headers=headers, timeout=30)
    print(f"状态: {resp.status_code}")
    if "工信部" in resp.text:
        print("✅ 搜索结果包含'工信部'")
except Exception as e:
    print(f"错误: {e}")
