"""测试领域1的URL是否支持分页"""
from playwright.sync_api import sync_playwright
import re

# 领域1的某个频道URL
url = "https://auto.gasgoo.com/auto-news/C-103"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print(f"测试URL: {url}")
    
    # 测试第1页
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    bigtitles = page.query_selector_all("h2.bigtitle")
    print(f"第1页: {len(bigtitles)} 条")
    
    if bigtitles:
        first_href = bigtitles[0].query_selector("a").get_attribute("href")
        print(f"第1页第1条: {first_href}")
    
    # 测试第2页
    page2_url = f"{url}?page=2"
    page.goto(page2_url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    bigtitles = page.query_selector_all("h2.bigtitle")
    print(f"\n第2页: {len(bigtitles)} 条")
    
    if bigtitles:
        first_href = bigtitles[0].query_selector("a").get_attribute("href")
        print(f"第2页第1条: {first_href}")
        
        # 提取日期
        date_match = re.search(r'/news/(\d{4})(\d{2})(\d{2})', first_href)
        if date_match:
            print(f"第2页第1条日期: {date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}")
    
    browser.close()
