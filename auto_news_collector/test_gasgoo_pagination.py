"""测试盖世汽车分页机制"""
from playwright.sync_api import sync_playwright
import re

url = "https://auto.gasgoo.com/new-cars/C-107"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 滚动到底部
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    
    # 查找所有分页相关元素
    result = page.evaluate("""
        () => {
            // 查找所有分页相关元素
            const results = [];
            const elements = document.querySelectorAll('a, button, div, span');
            for (let el of elements) {
                const text = el.innerText.trim();
                // 匹配页码格式：1, 2, 3... 或者 上一页, 下一页
                if (/^\\d+$/.test(text) || text.includes('下一页') || text.includes('上一页') || text.includes('尾页') || text.includes('首页')) {
                    results.push({
                        tag: el.tagName,
                        class: el.className,
                        text: text.substring(0, 50),
                        href: el.tagName === 'A' ? el.href : null
                    });
                }
            }
            return results;
        }
    """)
    
    print("找到分页相关元素:")
    for r in result[:20]:  # 只显示前20个
        print(f"  {r}")
    
    # 检查URL是否支持分页参数
    print("\n检查URL模式:")
    print(f"当前URL: {page.url}")
    
    # 尝试直接访问第2页
    page2_url = "https://auto.gasgoo.com/new-cars/C-107?page=2"
    page.goto(page2_url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    bigtitles = page.query_selector_all("h2.bigtitle")
    print(f"\n直接访问第2页: {len(bigtitles)} 个新闻")
    
    # 检查第一个新闻的日期
    if bigtitles:
        first = bigtitles[0]
        href = first.query_selector("a").get_attribute("href")
        print(f"第一个新闻URL: {href}")
        date_match = re.search(r'/news/(\d{4})(\d{2})(\d{2})', href)
        if date_match:
            print(f"日期: {date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}")
    
    browser.close()
