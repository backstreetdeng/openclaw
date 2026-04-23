"""分析gov.cn的文章列表结构 - 查找新闻容器"""
from playwright.sync_api import sync_playwright

url = "https://www.gov.cn/yaowen/liebiao/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 滚动加载
    page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    
    # 尝试查找新闻容器
    selectors = [
        ".news-box li",
        ".list li", 
        ".article-list li",
        ".policy-list li",
        "[class*='news'] li",
        "[class*='list'] li",
        "ul[class*='] li"
    ]
    
    for sel in selectors:
        elems = page.query_selector_all(sel)
        if len(elems) > 5:
            print(f"找到: {sel} -> {len(elems)} 个")
    
    # 直接查找所有包含日期的a标签
    # gov.cn的日期格式通常是 "2026-04-22"
    import re
    all_links = page.query_selector_all("a")
    news_links = []
    for a in all_links:
        href = a.get_attribute("href") or ""
        text = a.inner_text()[:100].strip()
        if "gov.cn" in href and len(text) > 10 and ("2026" in text or "2025" in text):
            news_links.append((text, href))
    
    print(f"\n找到可能新闻链接: {len(news_links)} 个")
    for text, href in news_links[:5]:
        print(f"  {text[:60]}...")
        print(f"  -> {href}")
    
    browser.close()
