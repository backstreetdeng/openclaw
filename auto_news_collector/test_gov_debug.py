"""调试gov.cn采集"""
from collector.browser_agent import MacroCollector
from datetime import datetime

url = "https://www.gov.cn/yaowen/liebiao/"
keywords = ["国务院常务会", "国务院常务会议", "政治局会议"]
max_count = 3
start_date = datetime(2026, 4, 18)
end_date = datetime(2026, 4, 24)

collector = MacroCollector()
results = collector._collect_gov(url, start_date, end_date, keywords, max_count)

print(f"采集到 {len(results)} 条")
for i, r in enumerate(results, 1):
    print(f"{i}. [{r['date']}] {r['title'][:60]}")
