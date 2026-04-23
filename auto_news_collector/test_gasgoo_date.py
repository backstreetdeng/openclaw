"""测试盖世汽车日期提取"""
from playwright.sync_api import sync_playwright
import re

def parse_gasgoo_date(date_str):
    if not date_str:
        return None
    patterns = [
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
        (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'),
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日', '%Y年%m月%d日'),
    ]
    for pattern, fmt in patterns:
        m = re.match(pattern, date_str.strip())
        if m:
            try:
                if fmt == '%Y年%m月%d日':
                    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                else:
                    return datetime.strptime(date_str.strip(), fmt)
            except:
                pass
    return None

url = "https://auto.gasgoo.com/new-cars/C-107"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 滚动加载
    for _ in range(2):
        page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
    
    bigtitles = page.query_selector_all("h2.bigtitle")
    
    print(f"找到 {len(bigtitles)} 个新闻\n")
    
    # 检查第一个的详细结构
    bt = bigtitles[0]
    print("=== 第一个新闻的完整HTML ===")
    html = bt.inner_html()
    print(html[:500])
    
    print("\n=== 检查日期span ===")
    # 查找所有的span
    all_spans = bt.query_selector_all("span")
    print(f"找到 {len(all_spans)} 个span")
    for i, span in enumerate(all_spans):
        text = span.inner_text().strip()
        print(f"  span[{i}]: '{text}'")
    
    print("\n=== parentElement的innerHTML ===")
    parent = bt.evaluate("el => el.parentElement ? el.parentElement.innerHTML.substring(0, 800) : 'no parent'")
    print(parent)
    
    browser.close()
