"""
直接测试fetch_article_content并打印中间结果
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collector.browser_agent import fetch_article_content, fetch_article_content_by_browser
import requests
import re

url = 'https://auto.gasgoo.com/news/202604/22I70454721C601.shtml'

# 1. 先看requests获取的原始HTML
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
resp = requests.get(url, headers=headers, timeout=10)
resp.encoding = 'utf-8'
html = resp.text

# 找ArticleContent
idx = html.find('ArticleContent')
if idx >= 0:
    chunk = html[idx:idx+300]
    print("HTML around ArticleContent:")
    print(chunk[:200])
    print("...")

# 2. 测试extract_article_content
from collector.browser_agent import extract_article_content
content = extract_article_content(html, url)
print(f"\nextract_article_content result: {len(content)} chars")
print(content[:200] if content else "EMPTY")

# 3. 测试fetch_article_content_by_browser
print("\nTesting Playwright fallback...")
browser_content = fetch_article_content_by_browser(url, 15)
print(f"Playwright result: {len(browser_content)} chars")
print(browser_content[:200] if browser_content else "EMPTY")

# 4. 测试完整fetch_article_content
print("\nTesting full fetch_article_content...")
full_content = fetch_article_content(url, 15)
print(f"Full result: {len(full_content)} chars")
print(full_content[:200] if full_content else "EMPTY")
