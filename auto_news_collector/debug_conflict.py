"""
测试：fetch_article_content在Playwright运行时调用
"""
import sys
sys.path.insert(0, 'E:\\openclaw\\workspace\\auto_news_collector')

from collector.browser_agent import fetch_article_content
from playwright.sync_api import sync_playwright

url = 'https://auto.gasgoo.com/news/202604/22I70454721C601.shtml'

print("=== 先启动Playwright浏览器 ===")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://auto.gasgoo.com/auto-news/C-601", timeout=30000)
    page.wait_for_load_state('networkidle')
    
    print("浏览器已打开，调用fetch_article_content:")
    content = fetch_article_content(url, 15)
    print(f"  结果长度: {len(content)}")
    
    browser.close()

print("浏览器已关闭，再次调用fetch_article_content:")
content = fetch_article_content(url, 15)
print(f"  结果长度: {len(content)}")
