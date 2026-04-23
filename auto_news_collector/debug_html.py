"""
分析为什么requests获取的HTML内容被截断
"""
import requests
import re

url = 'https://auto.gasgoo.com/news/202604/22I70454721C601.shtml'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print("=== requests获取 ===")
resp = requests.get(url, headers=headers, timeout=10)
resp.encoding = 'utf-8'
html = resp.text

# 找到ArticleContent
idx = html.find('ArticleContent')
print(f"ArticleContent位置: {idx}")

# 提取ArticleContent div的内容
# 问题：嵌套的div导致正则提前结束
article_start = html.find('>', idx) + 1
# 找ArticleContent div的结束 - 这是关键问题
# 由于HTML中嵌套了<div class="viewImg">，导致</div>匹配到了错误的位置

# 正确的做法：找到ArticleContent div的真正结束位置
# 方法：计算div的嵌套层次

depth = 0
start_idx = idx
i = start_idx

# 找到开始tag的结束
while i < len(html) and html[i] != '>':
    i += 1
content_start = i + 1

# 计算到下一个</div>时是否匹配
# 这很复杂，因为HTML结构可能不规则

# 简单方法：找所有<p>标签内的文本
ps = re.findall(r'<p[^>]*>(.*?)</p>', html[idx:idx+10000], re.DOTALL)
full_text = ''
for p in ps:
    # 清理标签但保留结构
    text = re.sub(r'<[^>]+>', '', p)
    text = text.strip()
    if text and len(text) > 20:
        full_text += text + '\n\n'

print(f"\n提取的<p>段落文本长度: {len(full_text)}")
print(f"文本内容:\n{full_text[:500]}")

# 另一种方法：使用innerHTML方式
print("\n=== 使用Playwright获取的完整HTML ===")
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=30000)
    page.wait_for_load_state('networkidle')
    
    # 获取页面完整HTML
    page_html = page.content()
    browser.close()
    
    idx2 = page_html.find('ArticleContent')
    print(f"ArticleContent在Playwright HTML中的位置: {idx2}")
