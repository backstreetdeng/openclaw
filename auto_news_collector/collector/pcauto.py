"""
PcautoCollector - 太平洋汽车新车上市采集器
按设计方案实现：https://price.pcauto.com.cn/cars/6/
"""

import re
import time
import requests
from datetime import datetime
from typing import List, Dict, Optional


class PcautoCollector:
    """太平洋汽车新车上市采集器"""

    def __init__(self):
        self.url = "https://price.pcauto.com.cn/cars/6/"

    def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        max_count: int = 10,
        fetch_content: bool = True
    ) -> List[Dict]:
        """
        采集太平洋汽车新车上市新闻

        Args:
            start_date: 开始日期
            end_date: 结束日期
            max_count: 最大条数
            fetch_content: 是否采集正文（搜索引擎获取）

        Returns:
            List[Dict] - 新闻列表
        """
        results = []

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # 访问太平洋汽车新车页面
                page.goto(self.url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)

                # 滚动加载更多
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1000)

                # 查找车辆条目 - 使用正确的选择器
                items = page.query_selector_all("a.new-car-show-list-item")

                print(f"PcautoCollector: 找到 {len(items)} 个条目")

                for item in items:
                    if len(results) >= max_count:
                        break

                    try:
                        # 获取元素内所有文本，用于判断类型
                        item_text = item.inner_text()

                        # 判断类型：新车 or 改款
                        car_type = "新车"
                        if "改款" in item_text:
                            car_type = "改款"

                        # 提取日期：从 div.date 元素获取
                        date_elem = item.query_selector("div.date")
                        date_str = ""
                        if date_elem:
                            date_str = date_elem.inner_text().strip()  # e.g. "2026年04月28日上市"

                        # 解析日期：格式 "2026年04月28日上市"
                        pub_date = None
                        if date_str:
                            try:
                                match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str)
                                if match:
                                    pub_date = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                            except:
                                pass

                        # 日期过滤（区间过滤）
                        if pub_date and not (start_date <= pub_date <= end_date):
                            continue

                        # 提取车型名称：第一行文本（去掉类型标识）
                        lines = item_text.split('\n')
                        title = lines[1].strip() if len(lines) > 1 else item_text.strip()

                        # 提取链接
                        href = item.get_attribute("href") or ""
                        link = href if href.startswith("http") else f"https://price.pcauto.com.cn{href}"

                        # 采集正文（搜索引擎方式）
                        content = ""
                        if fetch_content:
                            content = self._fetch_content_via_search(title, car_type, pub_date)

                        results.append({
                            "title": f"{car_type}-{title}",
                            "link": link,
                            "date": pub_date.strftime("%Y-%m-%d") if pub_date else date_str,
                            "content": content,
                            "source": "pcauto"
                        })

                    except Exception as e:
                        print(f"处理条目失败: {e}")
                        continue

                browser.close()

        except Exception as e:
            print(f"PcautoCollector采集失败: {e}")

        return results[:max_count]

    def _fetch_content_via_search(
        self,
        car_name: str,
        car_type: str,
        pub_date: Optional[datetime] = None
    ) -> str:
        """
        通过搜索引擎获取车型上市/改款新闻正文

        搜索策略：
        - 新车：搜索"车型名 上市" → "车型名"
        - 改款：搜索"车型名 改款 上市" → "车型名 最新消息" → "车型名 上市"
        搜索引擎：搜狗 → 百度 → 必应 → 简化正文（标题+日期+车型）
        时间校验：2026年以前的新闻会被标记为不可靠

        Args:
            car_name: 车型名称
            car_type: "新车" 或 "改款"
            pub_date: 发布日期

        Returns:
            str: 新闻正文内容
        """
        # 生成搜索关键词
        if car_type == "新车":
            queries = [
                f"{car_name} 上市",
                car_name,
            ]
        else:  # 改款
            queries = [
                f"{car_name} 改款 上市",
                f"{car_name} 最新消息",
                f"{car_name} 上市",
            ]

        # 搜索引擎列表
        engines = [
            ("搜狗", self._search_sogou),
            ("百度", self._search_baidu),
            ("必应", self._search_bing),
        ]

        # 尝试每个搜索引擎
        for engine_name, search_func in engines:
            for query in queries:
                try:
                    result = search_func(query, car_name, pub_date)
                    if result:
                        print(f"  [Pcauto] {engine_name}搜索成功: {car_name}")
                        return result
                except Exception as e:
                    print(f"  [Pcauto] {engine_name}搜索失败: {e}")
                    continue

        # 兜底：返回"车型：xxx"
        print(f"  [Pcauto] 搜索引擎均失败，使用兜底: {car_name}")
        return f"车型：{car_name}"

    def _search_sogou(self, query: str, car_name: str, pub_date: Optional[datetime]) -> Optional[str]:
        """搜狗搜索"""
        import urllib.parse
        url = f"https://www.sogou.com/web?query={urllib.parse.quote(query)}&ie=utf8"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.sogou.com/'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        return self._extract_content_from_search_resp(resp.text, car_name, pub_date)

    def _search_baidu(self, query: str, car_name: str, pub_date: Optional[datetime]) -> Optional[str]:
        """百度搜索"""
        import urllib.parse
        url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        resp = requests.get(url, headers=headers, timeout=15)
        return self._extract_content_from_search_resp(resp.text, car_name, pub_date)

    def _search_bing(self, query: str, car_name: str, pub_date: Optional[datetime]) -> Optional[str]:
        """必应搜索"""
        import urllib.parse
        url = f"https://cn.bing.com/search?q={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        resp = requests.get(url, headers=headers, timeout=15)
        return self._extract_content_from_search_resp(resp.text, car_name, pub_date)

    def _extract_content_from_search_resp(
        self,
        html: str,
        car_name: str,
        pub_date: Optional[datetime]
    ) -> Optional[str]:
        """
        从搜索引擎响应中提取正文

        策略：
        1. 查找搜索结果中的链接（过滤权威汽车媒体）
        2. 访问第一个有效链接获取正文
        3. 校验日期：2026年以前的标记为"不可靠"
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        # 优先查找的权威汽车媒体域名
        trusted_domains = [
            'autohome.com.cn',      # 汽车之家
            'pcauto.com.cn',         # 太平洋汽车
            'bitauto.com',           # 易车
            'che168.com',            # 二手车之家
            'ijia360.com',           # 爱卡汽车
            'qichemall.com',         # 懂车帝
        ]

        # 查找所有搜索结果链接
        links = []
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if href and ('http://' in href or 'https://' in href):
                # 检查是否来自权威媒体
                is_trusted = any(domain in href for domain in trusted_domains)
                links.append((href, is_trusted, a.get_text(strip=True)[:100]))

        if not links:
            return None

        # 优先选择权威媒体的链接
        trusted_links = [l for l in links if l[1]]
        links_to_try = trusted_links[:3] + links[:5]

        # 尝试访问链接获取正文
        for link, _, snippet in links_to_try:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                }
                resp = requests.get(link, headers=headers, timeout=15)
                resp.encoding = resp.apparent_encoding or 'utf-8'

                # 提取正文
                content = self._extract_article_content(resp.text)

                if content and len(content) > 50:
                    # 时间校验
                    if pub_date and pub_date.year < 2026:
                        content = f"[时间较早，可靠性有限]\n{content}"

                    return content

            except Exception as e:
                print(f"  [Pcauto] 访问链接失败 {link[:50]}: {e}")
                continue

        return None

    def _extract_article_content(self, html: str) -> str:
        """从HTML中提取文章正文"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        # 移除脚本和样式
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        # 尝试查找文章主体
        article = None

        # 方法1: 查找 article 或 main 标签
        for tag in ['article', 'main']:
            article = soup.find(tag)
            if article:
                break

        # 方法2: 查找含content/article/text的class/id
        if not article:
            for selector in ['.article-content', '.article-body', '.content', '#article-content']:
                article = soup.select_one(selector)
                if article:
                    break

        # 方法3: 查找最大的文本块
        if not article:
            # 找出包含最多段落的div
            best_div = None
            max_paragraphs = 0
            for div in soup.find_all('div'):
                ps = div.find_all('p')
                if len(ps) > max_paragraphs:
                    max_paragraphs = len(ps)
                    best_div = div
            article = best_div

        if article:
            # 提取文本
            paragraphs = article.find_all('p')
            if paragraphs:
                text = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                return text

            # 直接获取所有文本
            return article.get_text(separator=' ', strip=True)

        return ""
