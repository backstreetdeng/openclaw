"""
测试新的extract_article_content
"""
import sys
sys.path.insert(0, 'E:\\openclaw\\workspace\\auto_news_collector')

from collector.browser_agent import extract_article_content
import requests

url = 'https://auto.gasgoo.com/news/202604/22I70454721C601.shtml'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

resp = requests.get(url, headers=headers, timeout=10)
resp.encoding = 'utf-8'
html = resp.text

print("Testing new extract_article_content:")
content = extract_article_content(html, url)
print(f"Length: {len(content)}")
print(f"Content preview:\n{content[:500]}")
