"""监控政策页面的网络请求"""
from playwright.sync_api import sync_playwright

url = "https://www.gov.cn/zhengce/zuixin/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 监听网络请求
    json_urls = []
    
    def handle_response(response):
        if 'json' in response.url.lower() or 'api' in response.url.lower():
            json_urls.append(response.url)
    
    page.on("response", handle_response)
    
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    print("政策页面加载的JSON/API请求:")
    for url in json_urls[:20]:
        print(f"  {url}")
    
    browser.close()
