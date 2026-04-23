"""采集第1页和第2页的所有新闻标题"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 第1页
    print("=== 第1页 ===")
    page.goto("https://www.gov.cn/yaowen/liebiao/", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    lis = page.query_selector_all(".list li")
    print(f"共 {len(lis)} 条\n")
    
    for i, li in enumerate(lis, 1):
        a = li.query_selector("a")
        if a:
            title = a.inner_text().strip()
            print(f"{i}. {title}")
    
    # 第2页
    print("\n=== 第2页 ===")
    page.goto("https://www.gov.cn/yaowen/liebiao/page/2.htm", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    lis = page.query_selector_all(".list li")
    print(f"共 {len(lis)} 条\n")
    
    for i, li in enumerate(lis, 1):
        a = li.query_selector("a")
        if a:
            title = a.inner_text().strip()
            print(f"{i}. {title}")
    
    browser.close()
