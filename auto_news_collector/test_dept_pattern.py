"""测试国内经济（部门正则）和国际经济（美联储）"""
from collector.browser_agent import MacroCollector
from datetime import datetime

collector = MacroCollector()

start = datetime(2026, 4, 18)
end = datetime(2026, 4, 24)

# 国内经济 - 使用部门正则
print("=== 国内经济（XX部正则） ===")
guonei = collector._collect_eastmoney(
    "https://finance.eastmoney.com/a/cgnjj.html",
    start, end,
    ["部"],  # 传入什么不重要，代码内部用DEPARTMENT_PATTERNS
    5
)
print(f"获取 {len(guonei)} 条")
for r in guonei:
    print(f"  [{r['date']}] {r['title'][:60]}")

# 国际经济 - 只匹配"美联储"
print("\n=== 国际经济（只有美联储） ===")
guoji = collector._collect_eastmoney(
    "https://finance.eastmoney.com/a/cgjjj.html",
    start, end,
    ["美联储"],
    5
)
print(f"获取 {len(guoji)} 条")
for r in guoji:
    print(f"  [{r['date']}] {r['title'][:60]}")
