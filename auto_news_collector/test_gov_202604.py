"""测试gov.cn按月份分页"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 测试按月份分页
    url = "https://www.gov.cn/yaowen/liebiao/202604/"
    print(f"测试: {url}")
    
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        
        lis = page.query_selector_all(".list li")
        print(f"找到 {len(lis)} 条\n")
        
        for i, li in enumerate(lis[:25], 1):
            a = li.query_selector("a")
            if a:
                title = a.inner_text().strip()
                href = a.get_attribute("href") or ""
                print(f"{i}. {title[:50]}")
    except Exception as e:
        print(f"失败: {e}")
    
    browser.close()
