"""测试gov.cn是否支持翻页"""
from playwright.sync_api import sync_playwright

url = "https://www.gov.cn/yaowen/liebiao/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 第1页
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    lis1 = page.query_selector_all(".list li")
    print(f"第1页: {len(lis1)} 条")
    if lis1:
        a = lis1[0].query_selector("a")
        print(f"第1条: {a.inner_text()[:40]}...")
    
    # 第2页
    page2_url = f"{url}index.htm?page=2"  # gov.cn常用分页格式
    try:
        page.goto(page2_url, timeout=15000)
        page.wait_for_load_state("networkidle", timeout=10000)
        lis2 = page.query_selector_all(".list li")
        print(f"\n第2页: {len(lis2)} 条")
        if lis2:
            a = lis2[0].query_selector("a")
            print(f"第1条: {a.inner_text()[:40]}...")
    except Exception as e:
        print(f"第2页加载失败: {e}")
    
    browser.close()
