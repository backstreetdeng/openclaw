"""检查特定URL是否在列表中"""
from playwright.sync_api import sync_playwright

target_url = "content_7066458.htm"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    for page_num in range(1, 6):
        if page_num == 1:
            url = "https://www.gov.cn/yaowen/liebiao/"
        else:
            url = f"https://www.gov.cn/yaowen/liebiao/page/{page_num}.htm"
        
        print(f"检查第{page_num}页: {url}")
        try:
            page.goto(url, timeout=20000)
            page.wait_for_load_state("networkidle", timeout=15000)
            
            # 在整个页面搜索目标URL
            content = page.content()
            if target_url in content:
                print(f"  >>> 找到目标URL: {target_url}")
            
            # 也检查所有li
            lis = page.query_selector_all(".list li")
            found = False
            for li in lis:
                a = li.query_selector("a")
                if a:
                    href = a.get_attribute("href") or ""
                    if target_url in href:
                        title = a.inner_text().strip()
                        print(f"  >>> 在li中找到: {title[:40]}")
                        found = True
                        break
            
            if not found:
                print(f"  未找到")
                
        except Exception as e:
            print(f"  加载失败: {str(e)[:50]}")
    
    browser.close()
