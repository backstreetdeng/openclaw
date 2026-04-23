"""诊断太平洋汽车页面结构 - 找车型列表"""
from playwright.sync_api import sync_playwright

url = "https://price.pcauto.com.cn/cars/6/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 滚动加载
    page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)
    
    # 尝试各种可能的选择器
    selectors = [
        ".car-list", ".car-list .item", ".car-list li",
        ".model-list", ".model-list .item",
        ".brand-list", ".brand-list .item",
        "[class*='car']", "[class*='model']",
        ".pcauto-list", ".article-list",
        ".new-car-list", ".new-car-list .item",
        "div[class*='list']", 
    ]
    
    print("=== 选择器测试 ===")
    for sel in selectors:
        try:
            elems = page.query_selector_all(sel)
            if len(elems) > 0:
                print(f"{sel}: {len(elems)} 个")
                # 打印第一个的文本
                if elems:
                    text = elems[0].inner_text()[:60].replace("\n", " ")
                    print(f"  示例: {text}")
        except Exception as e:
            pass
    
    # 尝试查找包含"上市"文本的元素
    print("\n=== 搜索包含'上市'的元素 ===")
    try:
        elems = page.query_selector_all("text=上市")
        print(f"text=上市 找到 {len(elems)} 个")
        for i, e in enumerate(elems[:3]):
            text = e.inner_text()[:60].replace("\n", " ")
            print(f"  {i+1}: {text}")
    except:
        pass
    
    # 查看页面中的h3, h4, .title等
    print("\n=== 标题类元素 ===")
    for sel in ["h2", "h3", "h4", ".title", ".name"]:
        try:
            elems = page.query_selector_all(sel)
            if len(elems) > 0:
                text = elems[0].inner_text()[:50].replace("\n", " ")
                print(f"{sel}: {len(elems)} 个, 示例: {text}")
        except:
            pass
    
    browser.close()
