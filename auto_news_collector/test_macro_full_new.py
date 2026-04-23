"""测试完整MacroCollector"""
from collector.browser_agent import MacroCollector
from datetime import datetime

collector = MacroCollector()

start = datetime(2026, 4, 18)
end = datetime(2026, 4, 24)

print("=== 要闻 ===")
yaowen = collector._collect_gov(
    "https://www.gov.cn/yaowen/liebiao/",
    start, end,
    ["国务院常务会", "国务院常务会议", "政治局会议"],
    3
)
print(f"要闻: {len(yaowen)} 条")
for r in yaowen:
    print(f"  [{r['date']}] {r['title'][:40]}")

print("\n=== 政策 ===")
zhengce = collector._collect_gov(
    "https://www.gov.cn/zhengce/zuixin/",
    start, end,
    ["消费", "投资", "外贸", "出口", "进口", "民生", "就业", "大市场"],
    3
)
print(f"政策: {len(zhengce)} 条")

print("\n=== 国内经济 ===")
guonei = collector._collect_eastmoney(
    "https://finance.eastmoney.com/",
    start, end,
    ["部"],
    3
)
print(f"国内经济: {len(guonei)} 条")
for r in guonei:
    print(f"  [{r['date']}] {r['title'][:40]}")

print("\n=== 国际经济 ===")
guoji = collector._collect_eastmoney(
    "https://finance.eastmoney.com/guoji.html",
    start, end,
    ["美联储", "美国", "欧洲", "G7", "OPEC"],
    3
)
print(f"国际经济: {len(guoji)} 条")
for r in guoji:
    print(f"  [{r['date']}] {r['title'][:40]}")
