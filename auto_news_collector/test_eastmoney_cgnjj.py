"""监控国内经济页面的实际API请求"""
from playwright.sync_api import sync_playwright

url = "https://finance.eastmoney.com/a/cgnjj.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    api_requests = []
    
    def handle_response(response):
        url = response.url
        # 筛选API请求
        if 'json' in url.lower() or 'api' in url.lower() or 'data' in url.lower():
            api_requests.append(url)
            print(f"找到API: {url}")
    
    page.on("response", handle_response)
    
    try:
        page.goto(url, timeout=10000)
        page.wait_for_timeout(5000)  # 等待JS加载
    except Exception as e:
        print(f"超时: {e}")
    
    print(f"\n总共找到 {len(api_requests)} 个API请求")
    for url in api_requests[:20]:
        print(f"  {url}")
    
    browser.close()
