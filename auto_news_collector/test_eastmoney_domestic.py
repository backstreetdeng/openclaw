"""测试东方财富国内经济采集"""
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime

url = "https://finance.eastmoney.com/a/cgnjj.html"
keywords = ["部"]
start_date = datetime(2026, 4, 18)
end_date = datetime(2026, 4, 24)

print(f"测试URL: {url}")
print(f"关键字: {keywords}\n")

# 用Playwright测试
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # 获取页面内容
    content = page.content()
    print(f"页面长度: {len(content)}")
    
    # 搜索包含"部"的内容
    if "工信部" in content:
        print("✅ 找到'工信部'")
    if "七部门" in content:
        print("✅ 找到'七部门'")
    
    # 尝试查找新闻列表
    selectors = ["li", ".news-list li", "[class*=list] li"]
    for sel in selectors:
        items = page.query_selector_all(sel)
        if len(items) > 0:
            print(f"\n选择器 '{sel}': {len(items)} 个")
            for i, item in enumerate(items[:10]):
                text = item.inner_text()[:80].replace("\n", " ")
                print(f"  {i+1}. {text}")
            break
    
    browser.close()
