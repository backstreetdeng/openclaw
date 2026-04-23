"""
测试垃圾信息过滤效果
"""
import sys
sys.path.insert(0, 'E:\\openclaw\\workspace\\auto_news_collector')

from collector.browser_agent import fetch_article_content

url = 'https://auto.gasgoo.com/news/202604/22I70454745C103.shtml'

print("Testing article content cleaning:")
content = fetch_article_content(url, 15)
print(f"Content length: {len(content)}")
print(f"\nContent:\n{content}")
