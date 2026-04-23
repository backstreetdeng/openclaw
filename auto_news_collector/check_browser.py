"""
用Playwright检查文章完整内容
"""
from playwright.sync_api import sync_playwright

url = 'https://auto.gasgoo.com/news/202604/22I70454703C601.shtml'
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=30000)
    page.wait_for_load_state('networkidle')
    
    # 获取完整正文
    content = page.evaluate('''() => {
        const el = document.getElementById("ArticleContent");
        if (el) return el.innerText;
        return "NOT FOUND";
    }''')
    
    print(f'Content length: {len(content)}')
    print(f'Content preview:')
    print(content[:800])
    browser.close()
