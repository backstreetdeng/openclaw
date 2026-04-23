"""
测试企业要闻采集
"""
import sys
sys.path.insert(0, r'E:\openclaw\workspace\auto_news_collector')

from collector.browser_agent import GasgooCollector
from datetime import datetime, timedelta

today = datetime.now()
days_until_friday = (4 - today.weekday()) % 7
this_friday = today + timedelta(days=days_until_friday)
last_saturday = this_friday - timedelta(days=6)

print(f"Testing: https://auto.gasgoo.com/automaker/C-109")
print(f"Date range: {last_saturday} to {this_friday}")

collector = GasgooCollector('https://auto.gasgoo.com/automaker/C-109')
try:
    news = collector.collect(
        start_date=last_saturday,
        end_date=this_friday,
        max_count=5,
        exclude_keywords=['交付', '召回', '营收', '销量榜', '什么', '推荐', '同比', '环比', '财报'],
        fetch_content=False
    )
    print(f"Success: {len(news)} news")
    for n in news[:3]:
        title = n.get('title', 'N/A')
        print(f"  - {title[:50]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
