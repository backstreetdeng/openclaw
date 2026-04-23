"""测试国内经济和国际经济采集"""
from collector.browser_agent import MacroCollector
from datetime import datetime

collector = MacroCollector()

start = datetime(2026, 4, 18)
end = datetime(2026, 4, 24)

# 国内经济
print("=== 国内经济 ===")
guonei = collector._collect_eastmoney(
    "https://finance.eastmoney.com/a/cgnjj.html",
    start, end,
    ["部"],
    5
)
print(f"获取 {len(guonei)} 条")
for r in guonei:
    print(f"  [{r['date']}] {r['title'][:50]}")

# 国际经济
print("\n=== 国际经济 ===")
guoji = collector._collect_eastmoney(
    "https://finance.eastmoney.com/a/cgjjj.html",
    start, end,
    ["美联储", "美国", "欧洲", "G7", "OPEC"],
    5
)
print(f"获取 {len(guoji)} 条")
for r in guoji:
    print(f"  [{r['date']}] {r['title'][:50]}")
