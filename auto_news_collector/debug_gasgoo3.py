"""完整诊断新闻条目结构"""
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("https://auto.gasgoo.com/auto-news/C-103", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=10000)

    print("=== 完整新闻条目分析 ===\n")

    # 查找包含新闻标题的容器
    # 根据前面分析，结构是: H2.bigtitle > DD > DL
    bigtitles = page.query_selector_all("h2.bigtitle")

    print(f"找到 {len(bigtitles)} 个bigtitle\n")

    for i, bt in enumerate(bigtitles[:3]):
        print(f"--- 新闻 {i+1} ---")

        # 标题
        title_link = bt.query_selector("a")
        if title_link:
            print(f"标题: {title_link.inner_text().strip()}")
            print(f"链接: {title_link.get_attribute('href')}")

        # 日期 - 查找同级的DD下的span
        parent = bt.evaluate("el => el.parentElement.parentElement")
        date_spans = bt.evaluate("""el => {
            let dl = el.parentElement;
            let spans = dl.querySelectorAll('span');
            return Array.from(spans).map(s => s.innerText.trim()).slice(0,3);
        }""")
        print(f"日期信息: {date_spans}")

        print()

    # 测试提取前10条新闻
    print("\n=== 提取前10条新闻 ===")
    results = []

    for bt in bigtitles[:10]:
        try:
            title_link = bt.query_selector("a")
            if not title_link:
                continue

            title = title_link.inner_text().strip()
            link = title_link.get_attribute("href")
            link = f"https://auto.gasgoo.com{link}" if link.startswith("/") else link

            # 日期
            date_info = bt.evaluate("""el => {
                let dl = el.parentElement;
                let spans = dl.querySelectorAll('span');
                return Array.from(spans).map(s => s.innerText.trim()).slice(0,2);
            }""")

            date_str = date_info[0] if date_info else ""
            pub_date = None
            if date_str:
                try:
                    pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                except:
                    pass

            print(f"{len(results)+1}. {title[:40]}... | {date_str[:10] if date_str else '无日期'}")

            results.append({
                "title": title,
                "link": link,
                "date": date_str[:10] if date_str else "未知日期",
                "content": "",
                "source": "gasgoo"
            })

        except Exception as e:
            print(f"  错误: {e}")
            continue

    print(f"\n共提取 {len(results)} 条新闻")

    browser.close()
