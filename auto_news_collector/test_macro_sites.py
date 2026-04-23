"""测试宏观经济政策相关网站的页面结构"""
from playwright.sync_api import sync_playwright

def test_gov():
    print("=== 测试 gov.cn 要闻 ===")
    url = "https://www.gov.cn/yaowen/liebiao/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        
        # 查找文章列表
        # 尝试常见选择器
        selectors = ["li", ".list-item", "a.title", ".article", ".news"]
        for sel in selectors:
            elems = page.query_selector_all(sel)
            if len(elems) > 0:
                print(f"选择器 '{sel}': {len(elems)} 个")
                if elems:
                    text = elems[0].inner_text()[:80].replace("\n", " ")
                    print(f"  示例: {text}")
        
        # 获取页面HTML片段
        html = page.inner_html("body")
        print(f"\n页面长度: {len(html)}")
        
        browser.close()

def test_eastmoney():
    print("\n=== 测试 eastmoney.com ===")
    url = "https://finance.eastmoney.com/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        
        # 查找文章列表
        selectors = ["li", ".list-item", "a.title", ".article", ".news", "h3", "h2"]
        for sel in selectors:
            elems = page.query_selector_all(sel)
            if len(elems) > 0:
                print(f"选择器 '{sel}': {len(elems)} 个")
                if elems:
                    text = elems[0].inner_text()[:80].replace("\n", " ")
                    print(f"  示例: {text}")
        
        browser.close()

test_gov()
test_eastmoney()
