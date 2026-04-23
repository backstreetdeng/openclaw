"""
测试连续两次调用fetch_article_content
"""
import sys
sys.path.insert(0, 'E:\\openclaw\\workspace\\auto_news_collector')

from collector.browser_agent import fetch_article_content

url = 'https://auto.gasgoo.com/news/202604/22I70454721C601.shtml'

print("第一次调用:")
content1 = fetch_article_content(url, 15)
print(f"  结果长度: {len(content1)}")

print("\n第二次调用:")
content2 = fetch_article_content(url, 15)
print(f"  结果长度: {len(content2)}")

print(f"\n两次结果相同? {content1 == content2}")
