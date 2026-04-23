"""监控cgnjj.html的实际API请求"""
from playwright.sync_api import sync_playwright
import requests

url = "https://finance.eastmoney.com/a/cgnjj.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    api_urls = []
    
    def handle_request(request):
        url = request.url
        if 'np-listapi' in url or 'eastmoney' in url:
            api_urls.append(url)
    
    page.on("request", handle_request)
    
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(5000)
    except Exception as e:
        print(f"超时: {e}")
    
    print("找到的API请求:")
    for url in api_urls[:20]:
        print(f"  {url}")
    
    browser.close()
