"""详细诊断新闻结构"""
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("https://auto.gasgoo.com/auto-news/C-103", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=10000)

    # 获取新闻链接
    news_links = page.query_selector_all("a[href*='/news/']")

    print(f"找到 {len(news_links)} 个新闻链接\n")

    # 分析第一个有标题的新闻
    for link in news_links[:20]:
        href = link.get_attribute("href")
        text = link.inner_text().strip()
        if text and len(text) > 10:
            print(f"链接: {href}")
            print(f"文本: {text[:80]}")
            print("---")

            # 查找父元素
            parent = link.evaluate("""el => {
                let parent = el.parentElement;
                let result = [];
                for(let i=0; i<3 && parent; i++) {
                    result.push(parent.tagName + '.' + parent.className.substring(0,50));
                    parent = parent.parentElement;
                }
                return result;
            }""")
            print(f"父元素: {parent}")
            break

    # 检查日期元素
    print("\n--- 查找日期 ---")
    time_elements = page.query_selector_all("time, span[class*='time'], i[class*='time']")
    print(f"日期元素数量: {len(time_elements)}")

    for t in time_elements[:5]:
        text = t.inner_text().strip()
        dt = t.get_attribute("datetime")
        print(f"  text: {text}, datetime: {dt}")

    browser.close()
