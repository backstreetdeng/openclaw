"""诊断脚本 - 检查网页实际结构"""
import re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    print("=" * 60)
    print("诊断盖世汽车网页结构")
    print("=" * 60)

    # 行业动态
    page.goto("https://auto.gasgoo.com/auto-news/C-103", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=10000)

    print(f"\n页面标题: {page.title()}")
    print(f"页面URL: {page.url}")

    # 获取页面HTML前3000字符
    html = page.content()

    # 打印body下的直接子元素
    print("\n--- 查找文章容器 ---")

    # 方法1：查找所有article标签
    articles = page.query_selector_all("article")
    print(f"article标签数量: {len(articles)}")

    # 方法2：查找包含title的a标签
    titles = page.query_selector_all("a[href*='/news/']")
    print(f"新闻链接数量: {len(titles)}")

    if titles:
        print("\n前5条新闻:")
        for i, t in enumerate(titles[:5]):
            text = t.inner_text()[:50]
            href = t.get_attribute("href")
            print(f"  {i+1}. {text} | {href}")

    # 方法3：查找class包含list的元素
    list_items = page.query_selector_all("[class*='list']")
    print(f"\n包含'list'的元素: {len(list_items)}")

    # 方法4：查找新闻卡片
    cards = page.query_selector_all(".news-card, .article-card, .list-item")
    print(f"新闻卡片元素: {len(cards)}")

    browser.close()
    print("\n诊断完成")
