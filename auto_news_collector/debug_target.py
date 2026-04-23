"""
检查目标新闻的完整内容
"""
import sys
sys.path.insert(0, 'E:\\openclaw\\workspace\\auto_news_collector')

from collector.browser_agent import GasgooCollector
from datetime import datetime, timedelta

today = datetime.now()
days_until_friday = (4 - today.weekday()) % 7
this_friday = today + timedelta(days=days_until_friday)
last_saturday = this_friday - timedelta(days=6)

collector = GasgooCollector('https://auto.gasgoo.com/auto-news/C-601')
news = collector.collect(start_date=last_saturday, end_date=this_friday, max_count=20, fetch_content=True)

for n in news:
    if '地平线与北斗' in n.get('title', ''):
        print(f"标题: {n['title']}")
        print(f"正文长度: {len(n['content'])}")
        print(f"正文内容:\n{n['content']}")
