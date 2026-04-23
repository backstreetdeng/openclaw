"""
测试Playwright是否正常工作
"""
from playwright.sync_api import sync_playwright

print("Testing Playwright...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://auto.gasgoo.com/news/202604/22I70454721C601.shtml", timeout=30000)
    page.wait_for_load_state('networkidle')
    
    content = page.evaluate('''() => {
        const el = document.getElementById("ArticleContent");
        return el ? el.innerText.length : -1;
    }''')
    
    print(f"Article content length: {content}")
    browser.close()

print("Playwright test complete")
