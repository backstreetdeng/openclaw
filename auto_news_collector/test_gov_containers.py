"""检查gov.cn页面所有容器"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto("https://www.gov.cn/yaowen/liebiao/", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 检查所有可能包含新闻的容器
    containers = [
        ".list",
        ".news",
        ".article",
        "[class*=list]",
        "[class*=news]",
        "ul",
        ".main",
        ".content",
    ]
    
    for c in containers:
        elems = page.query_selector_all(c)
        if len(elems) > 0:
            print(f"{c}: {len(elems)} 个")
    
    # 搜索目标URL
    content = page.content()
    if "7066458" in content:
        print("\n页面HTML中包含 7066458")
        # 找到它在哪里
        idx = content.find("7066458")
        print(f"周围内容: {content[max(0,idx-100):idx+100]}")
    else:
        print("\n页面HTML中不包含 7066458")
    
    browser.close()
