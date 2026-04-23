"""检查cgnjj.html页面中的新闻列表"""
from playwright.sync_api import sync_playwright

url = "https://finance.eastmoney.com/a/cgnjj.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(5000)
        
        # 获取页面文本
        content = page.content()
        
        # 查找包含"部"的文本
        import re
        # 匹配新闻标题
        titles = re.findall(r'<h3[^>]*>([^<]+)</h3>', content)
        print(f"找到 {len(titles)} 个标题")
        for t in titles[:10]:
            print(f"  {t.strip()}")
        
        # 查找iframe或动态加载的内容
        iframes = page.query_selector_all('iframe')
        print(f"\n找到 {len(iframes)} 个iframe")
        
        # 查找script中的API请求
        scripts = re.findall(r'https?://[^\s"\']+', content)
        apis = [s for s in scripts if 'api' in s.lower() or 'json' in s.lower()]
        print(f"\n找到 {len(apis)} 个API相关链接")
        for a in apis[:10]:
            print(f"  {a}")
            
    except Exception as e:
        print(f"错误: {e}")
    
    browser.close()
