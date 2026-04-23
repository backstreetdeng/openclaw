"""测试MacroCollector完整流程"""
from collector.browser_agent import MacroCollector
from datetime import datetime

collector = MacroCollector()

# 测试国内经济
print("=== 国内经济 ===")
results = collector._collect_eastmoney(
    "https://finance.eastmoney.com/",
    datetime(2026, 4, 18),
    datetime(2026, 4, 24),
    ["部"],
    10
)
print(f"获取 {len(results)} 条")
for r in results:
    print(f"  [{r['date']}] {r['title'][:50]}")

# 测试国际经济
print("\n=== 国际经济 ===")
results2 = collector._collect_eastmoney(
    "https://finance.eastmoney.com/guoji.html",
    datetime(2026, 4, 18),
    datetime(2026, 4, 24),
    ["美联储", "美国", "欧洲", "G7", "OPEC"],
    10
)
print(f"获取 {len(results2)} 条")
for r in results2:
    print(f"  [{r['date']}] {r['title'][:50]}")
