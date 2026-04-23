"""
调试：直接测试fetch_article_content函数
"""
import sys
sys.path.insert(0, '.')

from collector.browser_agent import fetch_article_content

url = 'https://auto.gasgoo.com/news/202604/22I70454721C601.shtml'

print("Testing fetch_article_content...")
content = fetch_article_content(url, timeout=15)

print(f"Result length: {len(content)}")
print(f"Content:")
print(content)
