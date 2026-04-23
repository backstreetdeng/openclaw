"""测试采集器 - 验证修复"""
import sys
sys.path.insert(0, "E:\\openclaw\\workspace\\auto_news_collector")

from datetime import datetime, timedelta
from collector.browser_agent import GasgooCollector, AutoinfoCollector

# 测试参数
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print("=" * 60)
print("测试采集器 - 近7天数据")
print(f"时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
print("=" * 60)

# 测试1: 行业动态
print("\n[1] 行业动态 (C-103)")
collector = GasgooCollector("https://auto.gasgoo.com/auto-news/C-103")
news = collector.collect(start_date, end_date, max_count=5)
print(f"  采集到 {len(news)} 条")
for n in news[:3]:
    print(f"  - {n['date']} {n['title'][:40]}...")

# 测试2: 新能源技术
print("\n[2] 新能源技术 (nev/C-501)")
collector = GasgooCollector("https://auto.gasgoo.com/nev/C-501")
news = collector.collect(start_date, end_date, max_count=5)
print(f"  采集到 {len(news)} 条")
for n in news[:3]:
    print(f"  - {n['date']} {n['title'][:40]}...")

# 测试3: 企业要闻
print("\n[3] 企业要闻 (automaker/C-109)")
collector = GasgooCollector("https://auto.gasgoo.com/automaker/C-109")
news = collector.collect(start_date, end_date, max_count=5)
print(f"  采集到 {len(news)} 条")
for n in news[:3]:
    print(f"  - {n['date']} {n['title'][:40]}...")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
