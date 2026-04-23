"""直接检查目标文章是否在列表中"""
from playwright.sync_api import sync_playwright

target = "7066458"  # content_7066458.htm

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 第1页
    print("=== 检查第1页 ===")
    page.goto("https://www.gov.cn/yaowen/liebiao/", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    lis = page.query_selector_all(".list li")
    found = False
    for li in lis:
        a = li.query_selector("a")
        if a:
            href = a.get_attribute("href") or ""
            if target in href:
                print(f"找到: {a.inner_text().strip()[:50]}")
                found = True
    if not found:
        print("第1页未找到")
    
    # 第2页 - 用page/2.htm
    print("\n=== 检查第2页 (page/2.htm) ===")
    page.goto("https://www.gov.cn/yaowen/liebiao/page/2.htm", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    lis = page.query_selector_all(".list li")
    print(f"第2页有 {len(lis)} 条")
    found = False
    for li in lis:
        a = li.query_selector("a")
        if a:
            href = a.get_attribute("href") or ""
            if target in href:
                print(f"找到: {a.inner_text().strip()[:50]}")
                found = True
    if not found:
        print("第2页未找到")
    
    browser.close()
