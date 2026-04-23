"""测试gov.cn滚动加载更多"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto("https://www.gov.cn/yaowen/liebiao/", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 初始数量
    lis1 = page.query_selector_all(".list li")
    print(f"初始加载: {len(lis1)} 条")
    
    # 滚动3次，每次等待加载
    for i in range(3):
        page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        
        lis = page.query_selector_all(".list li")
        print(f"滚动{i+1}次后: {len(lis)} 条")
    
    # 查找目标文章
    target = "7066458"
    lis = page.query_selector_all(".list li")
    for li in lis:
        a = li.query_selector("a")
        if a:
            href = a.get_attribute("href") or ""
            if target in href:
                print(f"\n找到目标: {a.inner_text().strip()[:50]}")
                break
    else:
        print("\n未找到目标文章")
    
    browser.close()
