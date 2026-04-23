"""
GasgooCollector - 盖世汽车新闻采集器
支持分页采集，直到最旧日期 < 开始日期才停止
"""

import re
import time
import requests
from datetime import datetime
from typing import List, Dict, Optional


class GasgooCollector:
    """盖世汽车新闻采集器 - 支持分页"""

    def __init__(self, url: str):
        self.url = url

    def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        max_count: int = 10,
        include_keywords: List[str] = None,
        exclude_keywords: List[str] = None,
        fetch_content: bool = False,
        stop_if_enough: bool = False,
        current_total: int = 0,
        brand_categories: Dict[str, List[str]] = None,
        # 分页新增参数
        max_pages: int = 10,
    ) -> List[Dict]:
        """
        采集盖世汽车新闻（支持分页）

        核心分页逻辑：
        1. 从第1页开始，逐页遍历
        2. 每页完整加载后，提取该页所有文章的日期
        3. 判断该页最旧日期是否 < 开始日期
           - 是 → 停止翻页（后续页面更旧，无需继续）
           - 否 → 继续翻下一页
        4. 最多翻 max_pages 页（防死循环）

        Args:
            start_date: 开始日期
            end_date: 结束日期
            max_count: 最大条数（整个采集过程的有效结果上限）
            include_keywords: 必须包含的关键字
            exclude_keywords: 要排除的关键字
            fetch_content: 是否采集正文
            stop_if_enough: 是否在够数后停止（单页内有效）
            current_total: 当前已采集数量（跨URL累加）
            brand_categories: 品牌分类配置
            max_pages: 最多翻页数（默认10页防死循环）

        Returns:
            List[Dict] - 新闻列表
        """
        results = []
        include_keywords = include_keywords or []
        exclude_keywords = exclude_keywords or []

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page_num = 1
                continue_pagination = True  # 是否继续翻页

                while continue_pagination and page_num <= max_pages:
                    # 构建分页URL: /C-103/2, /C-103/3 ... (盖世汽车用 /N 格式)
                    if page_num == 1:
                        current_url = self.url
                    else:
                        base = self.url.rstrip('/')
                        current_url = f"{base}/{page_num}"

                    print(f"  [GasgooCollector] 第{page_num}页: {current_url[-60:]}")

                    try:
                        page.goto(current_url, timeout=30000)
                        page.wait_for_load_state("networkidle", timeout=15000)
                    except Exception as e:
                        print(f"  [GasgooCollector] 第{page_num}页访问失败: {e}")
                        break

                    # 滚动加载（有些页面需要滚动才完整）
                    for _ in range(2):
                        page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                        page.wait_for_timeout(800)

                    # 提取当前页所有文章
                    bigtitles = page.query_selector_all("h2.bigtitle")

                    if not bigtitles:
                        print(f"  [GasgooCollector] 第{page_num}页无内容，停止")
                        break

                    print(f"  [GasgooCollector] 第{page_num}页找到 {len(bigtitles)} 条")

                    # 用于判断该页最旧日期
                    page_oldest_date: Optional[datetime] = None

                    for bt in bigtitles:
                        try:
                            # 提取标题和链接
                            title_link = bt.query_selector("a")
                            if not title_link:
                                continue

                            title = title_link.inner_text().strip()
                            href = title_link.get_attribute("href") or ""

                            # 构建完整链接
                            if href and not href.startswith("http"):
                                href = f"https://auto.gasgoo.com{href}"
                            elif not href:
                                continue

                            # 提取日期
                            date_str = ""
                            try:
                                parent = bt.evaluate_handle("element => element.parentElement")
                                if parent:
                                    spans = parent.query_selector_all("span")
                                    for span in spans:
                                        span_text = span.inner_text().strip()
                                        if re.match(r"\d{4}-\d{2}-\d{2}", span_text):
                                            date_str = span_text
                                            break
                            except:
                                pass

                            # 解析日期
                            pub_date = None
                            if date_str:
                                try:
                                    pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                                except:
                                    pass

                            # 追踪当前页最旧日期（从所有条目中采集，用于翻页决策）
                            if pub_date:
                                if page_oldest_date is None or pub_date < page_oldest_date:
                                    page_oldest_date = pub_date

                            # 日期区间过滤
                            if pub_date and not (start_date <= pub_date <= end_date):
                                continue

                            # include_keywords过滤
                            if include_keywords:
                                if not any(k in title for k in include_keywords):
                                    continue

                            # exclude_keywords过滤
                            if exclude_keywords:
                                if any(k in title for k in exclude_keywords):
                                    continue

                            # ===== max_count 控制逻辑 =====
                            current_count = len(results) + current_total
                            if current_count >= max_count:
                                if stop_if_enough:
                                    # stop_if_enough=True: 跳过加入结果，但继续遍历完当前页
                                    # 目的：确保看到完整页的所有日期，再决定是否翻页
                                    continue
                                else:
                                    # stop_if_enough=False: 立即停止，不看剩余条目
                                    break

                            # 构建结果
                            result = {
                                "title": title,
                                "link": href,
                                "date": date_str if date_str else (pub_date.strftime("%Y-%m-%d") if pub_date else ""),
                                "content": "",
                                "source": "gasgoo"
                            }

                            # 可选：采集正文
                            if fetch_content:
                                result["content"] = self._fetch_article_content(href)

                            results.append(result)

                        except Exception as e:
                            print(f"处理标题失败: {e}")
                            continue

                    # ===== max_count + stop_if_enough 控制：够数后停止翻页 =====
                    if stop_if_enough and len(results) + current_total >= max_count:
                        print(f"  [GasgooCollector] 已采集够{max_count}条，停止翻页")
                        continue_pagination = False

                    # ===== 核心分页判断：看完完整页再决定 =====
                    # 判断条件：该页最旧日期 < 开始日期 → 停止翻页
                    elif page_oldest_date is not None and page_oldest_date < start_date:
                        print(f"  [GasgooCollector] 第{page_num}页最旧日期 {page_oldest_date.date()} < 开始日期 {start_date.date()}，停止翻页")
                        continue_pagination = False
                    elif page_num >= max_pages:
                        print(f"  [GasgooCollector] 已达最大页数限制({max_pages}页)，停止")
                        continue_pagination = False
                    else:
                        page_num += 1

                browser.close()

        except Exception as e:
            print(f"GasgooCollector采集失败: {e}")

        return results

    def _fetch_article_content(self, url: str) -> str:
        """从详情页提取正文"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            html = response.text

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            article = soup.find(id='ArticleContent')
            if article:
                return article.get_text(separator=' ', strip=True)

            for div in soup.find_all('div'):
                if 'content' in div.get('class', []) or 'article' in div.get('class', []):
                    text = div.get_text(separator=' ', strip=True)
                    if len(text) > 100:
                        return text

        except Exception as e:
            print(f"_fetch_article_content失败: {e}")

        return ""
