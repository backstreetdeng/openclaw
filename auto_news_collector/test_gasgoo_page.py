"""测试盖世汽车翻页按钮"""
from playwright.sync_api import sync_playwright

url = "https://auto.gasgoo.com/new-cars/C-107"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 滚动到页面底部
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    
    # 查找所有包含"下一页"的元素
    result = page.evaluate("""
        () => {
            // 查找所有a和button标签
            const results = [];
            const elements = document.querySelectorAll('a, button');
            for (let el of elements) {
                const text = el.innerText.trim();
                if (text.includes('下一页')) {
                    results.push({
                        tag: el.tagName,
                        text: text,
                        visible: el.offsetParent !== null,
                        rect: el.getBoundingClientRect()
                    });
                }
            }
            return results;
        }
    """)
    
    print("找到包含'下一页'的元素:")
    for r in result:
        print(f"  {r}")
    
    # 尝试用JS点击
    click_result = page.evaluate("""
        () => {
            const links = document.querySelectorAll('a');
            for (let link of links) {
                if (link.innerText.trim() === '下一页' || link.innerText.trim() === '下一页 >') {
                    link.click();
                    return true;
                }
            }
            return false;
        }
    """)
    print(f"\nJS点击结果: {click_result}")
    
    if click_result:
        page.wait_for_load_state("networkidle", timeout=15000)
        print("已翻到下一页")
        
        # 验证是否真的翻页了
        bigtitles = page.query_selector_all("h2.bigtitle")
        print(f"下一页有 {len(bigtitles)} 个新闻")
    
    browser.close()
