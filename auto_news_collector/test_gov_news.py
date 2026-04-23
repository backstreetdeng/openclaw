"""分析gov.cn的文章列表结构"""
from playwright.sync_api import sync_playwright
import re

url = "https://www.gov.cn/yaowen/liebiao/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 滚动加载
    page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    
    # 使用.list li选择器
    lis = page.query_selector_all(".list li")
    print(f".list li 找到 {len(lis)} 个\n")
    
    for i, li in enumerate(lis[:10]):
        # 查找a标签
        a = li.query_selector("a")
        if not a:
            continue
        text = a.inner_text().strip()
        href = a.get_attribute("href") or ""
        
        # 查找日期span
        spans = li.query_selector_all("span")
        date_str = ""
        for span in spans:
            t = span.inner_text().strip()
            if re.match(r'\d{4}-\d{2}-\d{2}', t):
                date_str = t
                break
        
        print(f"{i+1}. [{date_str}] {text[:50]}...")
        print(f"   -> {href}")
    
    browser.close()
