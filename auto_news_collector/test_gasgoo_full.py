"""完整测试盖世汽车翻页采集"""
from collector.browser_agent import GasgooCollector
from datetime import datetime

collector = GasgooCollector("https://auto.gasgoo.com/new-cars/C-107")
start_date = datetime(2026, 4, 18)
end_date = datetime(2026, 4, 24)

print("开始测试...")
results = collector.collect(
    start_date=start_date,
    end_date=end_date,
    max_count=10,
    include_keywords=["上市", "预售"],
    exclude_keywords=[],
    fetch_content=False  # 先不获取正文，只测试翻页
)

print(f"\n采集结果: {len(results)} 条")
for i, r in enumerate(results, 1):
    print(f"{i}. [{r['date']}] {r['title'][:50]}")

if len(results) < 10:
    print(f"\n警告：只采集到 {len(results)} 条，可能没有翻到足够多的页面")
