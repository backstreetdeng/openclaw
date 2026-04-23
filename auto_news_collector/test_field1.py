"""
领域1采集测试脚本 - 单频道简化版
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from collector.browser_agent import GasgooCollector

# 当前周期
today = datetime.now()
days_until_friday = (4 - today.weekday()) % 7
this_friday = today + timedelta(days=days_until_friday)
last_saturday = this_friday - timedelta(days=6)

start_date = last_saturday
end_date = this_friday

print(f"测试时间范围: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
print("="*60)

# 只测试一个频道
url = "https://auto.gasgoo.com/auto-news/C-103"
print(f"正在采集: 行业频道...")

collector = GasgooCollector(url)
news = collector.collect(
    start_date=start_date,
    end_date=end_date,
    max_count=15,
    exclude_keywords=["税", "电池", "锂矿", "原材料", "油"],
    fetch_content=True
)

print(f"获取到 {len(news)} 条")

# 按日期排序
news.sort(key=lambda x: x.get('date', ''), reverse=True)

for i, n in enumerate(news[:10], 1):
    print(f"\n{i}. [{n.get('date', '')}] {n.get('title', '')[:50]}")
    print(f"   链接: {n.get('link', '')}")
    content = n.get('content', '')
    if content:
        print(f"   正文: {content[:100]}...")

print("\n测试完成")
