"""
直接测试collector
"""
import sys
sys.path.insert(0, 'E:\\openclaw\\workspace\\auto_news_collector')

from collector.browser_agent import GasgooCollector
from datetime import datetime, timedelta

today = datetime.now()
days_until_friday = (4 - today.weekday()) % 7
this_friday = today + timedelta(days=days_until_friday)
last_saturday = this_friday - timedelta(days=6)

print("Starting collector test...")
collector = GasgooCollector('https://auto.gasgoo.com/auto-news/C-601')
news = collector.collect(start_date=last_saturday, end_date=this_friday, max_count=3, fetch_content=True)

print(f"Got {len(news)} news items")
for n in news[:3]:
    print(f"{n['title'][:30]}... content_len={len(n['content'])}")
