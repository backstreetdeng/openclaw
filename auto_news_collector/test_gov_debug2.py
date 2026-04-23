"""调试gov.cn采集 - 打印更多详情"""
from playwright.sync_api import sync_playwright
from datetime import datetime
import re

url = "https://www.gov.cn/yaowen/liebiao/"
keywords = ["国务院常务会", "国务院常务会议", "政治局会议"]
start_date = datetime(2026, 4, 18)
end_date = datetime(2026, 4, 24)

print(f"开始日期: {start_date}")
print(f"结束日期: {end_date}")
print(f"关键字: {keywords}\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 滚动
    for _ in range(2):
        page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
    
    # 获取所有li
    lis = page.query_selector_all(".list li")
    print(f"找到 {len(lis)} 个 li 元素\n")
    
    match_count = 0
    date_fail_count = 0
    keyword_fail_count = 0
    
    for i, li in enumerate(lis[:20]):  # 只看前20个
        a = li.query_selector("a")
        if not a:
            continue
            
        title = a.inner_text().strip()
        href = a.get_attribute("href") or ""
        
        # 查找日期
        spans = li.query_selector_all("span")
        date_str = ""
        pub_date = None
        for span in spans:
            t = span.inner_text().strip()
            if re.match(r'\d{4}-\d{2}-\d{2}', t):
                date_str = t
                try:
                    pub_date = datetime.strptime(t, "%Y-%m-%d")
                except:
                    pass
                break
        
        # 检查关键字匹配
        keyword_match = any(k in title for k in keywords)
        
        # 检查日期范围
        date_in_range = pub_date and (start_date <= pub_date <= end_date)
        
        if i < 5:
            print(f"[{i+1}] 日期: {date_str}, 符合范围: {date_in_range}, 关键字匹配: {keyword_match}")
            print(f"     标题: {title[:50]}...")
        
        if not keyword_match:
            keyword_fail_count += 1
            continue
            
        if not date_in_range:
            date_fail_count += 1
            continue
        
        match_count += 1
    
    print(f"\n统计: 关键字不匹配: {keyword_fail_count}, 日期不匹配: {date_fail_count}, 匹配: {match_count}")
    
    browser.close()
