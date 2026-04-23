"""测试要闻-总书记关键字"""
from collector.browser_agent import MacroCollector
from datetime import datetime

url = "https://www.gov.cn/yaowen/liebiao/"
keywords = ["总书记"]
start_date = datetime(2026, 4, 18)
end_date = datetime(2026, 4, 24)
max_count = 50  # 多采集一些

collector = MacroCollector()
results = collector._collect_gov(url, start_date, end_date, keywords, max_count)

print(f"关键字：{keywords}")
print(f"时间范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
print(f"采集到 {len(results)} 条\n")

for i, r in enumerate(results, 1):
    print(f"{i}. [{r['date']}] {r['title'][:60]}")
    print(f"   {r['link']}")
