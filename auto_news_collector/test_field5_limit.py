"""
测试新能源技术max_count=5
"""
import sys
sys.path.insert(0, r'E:\openclaw\workspace\auto_news_collector')
from collector.browser_agent import GasgooCollector
from datetime import datetime, timedelta

today = datetime.now()
days_until_friday = (4 - today.weekday()) % 7
this_friday = today + timedelta(days=days_until_friday)
last_saturday = this_friday - timedelta(days=6)

print("测试max_count=5限制")
collector = GasgooCollector('https://auto.gasgoo.com/nev/C-501')
news = collector.collect(
    start_date=last_saturday,
    end_date=this_friday,
    max_count=5,
    fetch_content=False
)
print(f'获取: {len(news)} 条')
for n in news[:8]:
    title = n.get('title', 'N/A')
    print(f'  - {title[:40]}')
