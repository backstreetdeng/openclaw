"""测试gov采集"""
from collector.browser_agent import MacroCollector
from datetime import datetime

collector = MacroCollector()

# 测试要闻
print("=== 测试要闻 ===")
yaowen_results = collector._collect_gov(
    "https://www.gov.cn/yaowen/liebiao/",
    datetime(2026, 4, 18),
    datetime(2026, 4, 24),
    ["总书记"],
    10
)
print(f"要闻: {len(yaowen_results)} 条")

# 测试政策
print("\n=== 测试政策 ===")
zhengce_results = collector._collect_gov(
    "https://www.gov.cn/zhengce/zuixin/",
    datetime(2026, 4, 18),
    datetime(2026, 4, 24),
    ["消费", "投资", "外贸", "出口", "进口", "民生", "就业", "大市场"],
    10
)
print(f"政策: {len(zhengce_results)} 条")
for r in zhengce_results[:3]:
    print(f"  [{r['date']}] {r['title'][:40]}")
