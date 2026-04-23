"""用搜狗搜索这篇新闻"""
import requests

query = "工信部等七部门 统筹利用 两新 石化化工行业"
url = f"https://www.sogou.com/web?query={requests.utils.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

resp = requests.get(url, headers=headers, timeout=30)
print(f"状态: {resp.status_code}")
if "工信部" in resp.text:
    print("✅ 搜狗搜索结果包含'工信部'")
    # 查找摘要
    import re
    snippet = re.search(r'<!--摘要开始-->([^<]+)<!--摘要结束-->', resp.text)
    if snippet:
        print(f"摘要: {snippet.group(1)[:200]}")
else:
    print("❌ 搜狗搜索结果不包含'工信部'")
