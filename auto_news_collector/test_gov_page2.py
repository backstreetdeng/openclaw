"""测试gov.cn分页格式"""
from playwright.sync_api import sync_playwright

url = "https://www.gov.cn/yaowen/liebiao/"

# 尝试不同的分页URL格式
page_formats = [
    f"{url}?page=2",
    f"{url}index.htm?page=2",
    f"{url}page/2.htm",
    f"{url}list_2.htm",
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    for fmt in page_formats:
        print(f"尝试: {fmt}")
        try:
            page.goto(fmt, timeout=10000)
            page.wait_for_load_state("networkidle", timeout=8000)
            lis = page.query_selector_all(".list li")
            print(f"  成功! {len(lis)} 条")
            if lis:
                a = lis[0].query_selector("a")
                print(f"  第1条: {a.inner_text()[:40]}...")
            break
        except Exception as e:
            print(f"  失败: {str(e)[:50]}")
    
    browser.close()
