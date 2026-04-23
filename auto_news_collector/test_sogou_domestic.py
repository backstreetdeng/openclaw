"""用搜狗搜索采集国内经济新闻"""
import requests
import re
from datetime import datetime

keywords = ["部"]
start_date = datetime(2026, 4, 18)
end_date = datetime(2026, 4, 24)

# 搜索"国内经济 部"相关新闻
query = "国内经济 工信部 OR 发改委 OR 财政部 OR 商务部 OR 农业农村部"
url = f"https://www.sogou.com/web?query={requests.utils.quote(query)}&ie=utf8"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"搜索: {query}\n")

resp = requests.get(url, headers=headers, timeout=30)
print(f"状态: {resp.status_code}")

# 提取搜狗结果
# 格式：<!--摘要开始-->...<!--摘要结束-->
snippets = re.findall(r'<!--摘要开始-->([^<]+)<!--摘要结束-->', resp.text)
print(f"找到 {len(snippets)} 条结果\n")

for i, snippet in enumerate(snippets[:10], 1):
    print(f"{i}. {snippet[:80]}...")
