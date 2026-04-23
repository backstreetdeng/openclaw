"""检查gov.cn分页的真实结构"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 访问第1页
    page.goto("https://www.gov.cn/yaowen/liebiao/", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 查看页面URL和内容
    print(f"第1页URL: {page.url}")
    
    # 查找分页相关的链接
    page_links = page.query_selector_all("a")
    page_urls = []
    for link in page_links:
        href = link.get_attribute("href") or ""
        text = link.inner_text().strip()
        if "page" in href or "202604" in href:
            page_urls.append((text, href))
    
    print("\n分页相关链接:")
    for text, href in page_urls[:10]:
        print(f"  {text}: {href}")
    
    # 查看是否有"第2页"的链接
    for link in page_links:
        text = link.inner_text().strip()
        if text == "2" or "下一页" in text:
            href = link.get_attribute("href") or ""
            print(f"\n找到分页: '{text}' -> {href}")
    
    browser.close()
