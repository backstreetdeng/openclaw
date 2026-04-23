"""分析gov.cn的文章列表结构"""
from playwright.sync_api import sync_playwright

url = "https://www.gov.cn/yaowen/liebiao/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 获取所有li元素
    lis = page.query_selector_all("li")
    print(f"总共 {len(lis)} 个 li 元素\n")
    
    # 分析前5个li的结构
    for i, li in enumerate(lis[:5]):
        print(f"=== li[{i}] ===")
        html = li.inner_html()[:200]
        print(f"HTML: {html}")
        
        # 查找a标签
        a = li.query_selector("a")
        if a:
            text = a.inner_text()[:80].replace("\n", " ")
            href = a.get_attribute("href")
            print(f"链接文本: {text}")
            print(f"链接地址: {href}")
        print()
    
    browser.close()
