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
                        news_url = link  # 默认用列表页链接
                        if fetch_content:
                            result = self._fetch_content_via_search(title, car_type, pub_date)
                            if result:
                                content = result.get('content', '')
                                # 如果搜索引擎找到了真实新闻URL，用它替换列表页链接
                                if result.get('url'):
                                    news_url = result['url']

                        results.append({
                            "title": f"{car_type}-{title}",
                            "link": news_url,
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
    ) -> Dict:
        """
        通过搜索引擎获取车型上市/改款新闻正文

        搜索策略：
        - 新车：搜索"车型名 上市" → "车型名"
        - 改款：搜索"车型名 改款 上市" → "车型名 最新消息" → "车型名 上市"
        搜索引擎：必应 → 百度 → 简化正文（标题+日期+车型）
        时间校验：2026年以前的新闻会被标记为不可靠

        Args:
            car_name: 车型名称
            car_type: "新车" 或 "改款"
            pub_date: 发布日期

        Returns:
            Dict: {"content": str, "url": str} 或 None
        """
        # 生成搜索关键词：多站点轮询（汽车之家/太平洋/易车/懂车帝/有驾/爱卡）
        # 优先搜太平洋，如果没有好结果，尝试其他权威网站
        sites = [
            "site:pcauto.com.cn",
            "site:autohome.com.cn",
            "site:bitauto.com",
            "site:dongchedi.com",
            "site:yoojia.com",
            "site:ijia360.com",
        ]

        queries = []
        if car_type == "新车":
            for site in sites:
                queries.append(f"{car_name} 上市 {site}")
                queries.append(f"{car_name} {site}")
            # 最后用无限制搜索
            queries.append(f"{car_name} 上市")
            queries.append(car_name)
        else:  # 改款
            for site in sites:
                queries.append(f"{car_name} 改款 上市 {site}")
                queries.append(f"{car_name} 最新消息 {site}")
            queries.append(f"{car_name} 改款 上市")
            queries.append(f"{car_name} 最新消息")
            queries.append(f"{car_name} 上市")

        # 搜索引擎列表（去掉搜狗，容易触发验证）
        engines = [
            ("必应", self._search_bing),
            ("百度", self._search_baidu),
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
        return {"content": f"车型：{car_name}", "url": ""}

    def _search_sogou(self, query: str, car_name: str, pub_date: Optional[datetime]) -> Optional[str]:
        """搜狗搜索"""
        import urllib.parse
        import time
        time.sleep(2)  # 避免触发验证

        url = f"https://www.sogou.com/web?query={urllib.parse.quote(query)}&ie=utf8"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.sogou.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)

        # 检测编码
        resp = self._fix_encoding(resp)

        # 检查是否被拦截
        if self._is_blocked(resp.text):
            print(f"  [Pcauto] 搜狗触发验证，跳过")
            return None

        return self._extract_content_from_search_resp(resp.text, car_name, pub_date)

    def _search_baidu(self, query: str, car_name: str, pub_date: Optional[datetime]) -> Optional[Dict]:
        """百度搜索"""
        import urllib.parse
        import time
        time.sleep(2)

        url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp = self._fix_encoding(resp)

        if self._is_blocked(resp.text):
            print(f"  [Pcauto] 百度触发验证，跳过")
            return None

        return self._extract_content_from_search_resp(resp.text, car_name, pub_date)

    def _search_bing(self, query: str, car_name: str, pub_date: Optional[datetime]) -> Optional[Dict]:
        """必应搜索"""
        import urllib.parse
        import time
        time.sleep(2)

        url = f"https://cn.bing.com/search?q={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp = self._fix_encoding(resp)

        if self._is_blocked(resp.text):
            print(f"  [Pcauto] 必应触发验证，跳过")
            return None

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
        1. 从h3标签提取搜索结果（更准确）
        2. 解析 /link?url= 重定向获取真实URL
        3. 优先选择权威汽车媒体
        4. 访问第一个有效链接获取正文
        5. 校验日期：2026年以前的标记为"不可靠"
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        # 权威汽车媒体域名
        trusted_domains = [
            'autohome.com.cn',      # 汽车之家
            'pcauto.com.cn',         # 太平洋汽车
            'bitauto.com',           # 易车
            'che168.com',            # 二手车之家
            'ijia360.com',           # 爱卡汽车
            'dongchedi.com',         # 懂车帝
            'yoojia.com',            # 有驾
            'gasgoo.com',            # 盖世汽车
            'sohu.com/autohome',     # 搜狐汽车
            'sina.com.cn/auto',      # 新浪汽车
            'ifeng.com/auto',        # 凤凰汽车
        ]

        # 查找搜索结果：从h3标签提取
        results = []
        for h3 in soup.find_all('h3'):
            a = h3.find('a', href=True)
            if not a:
                continue

            href = a.get('href', '')

            # 处理重定向链接：/link?url=xxx -> 需要访问获取真实URL
            if href.startswith('/link?url='):
                real_url = self._resolve_sogou_redirect(href)
            elif href.startswith('http'):
                real_url = href
            else:
                continue

            if not real_url:
                continue

            # 检查是否来自权威媒体
            is_trusted = any(domain in real_url for domain in trusted_domains)
            title = a.get_text(strip=True)[:60]

            results.append({
                'url': real_url,
                'title': title,
                'trusted': is_trusted
            })

        if not results:
            return None

        # 优先选择权威媒体的链接
        results.sort(key=lambda x: x['trusted'], reverse=True)

        # 尝试访问链接获取正文
        for result in results[:5]:
            url = result['url']
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }
                resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)

                # 修复编码
                resp = self._fix_encoding(resp)

                # 检查是否被拦截
                if self._is_blocked(resp.text):
                    print(f"  [Pcauto] 链接触发验证: {url[:50]}")
                    continue

                # 提取正文
                content = self._extract_article_content(resp.text)

                if content and len(content) > 100:
                    # 检查是否为新闻页面（使用真实URL检查）
                    real_url = resp.url  # 使用重定向后的真实URL
                    if not self._is_news_page(real_url, resp.text, len(content)):
                        print(f"  [Pcauto] 非新闻页面跳过: {real_url[:60]}")
                        continue

                    # 时间校验
                    if pub_date and pub_date.year < 2026:
                        content = f"[时间较早，可靠性有限]\n{content}"

                    return {"content": content, "url": real_url}

            except Exception as e:
                print(f"  [Pcauto] 访问链接失败 {url[:50]}: {e}")
                continue

        return None

    def _resolve_sogou_redirect(self, redirect_url: str) -> Optional[str]:
        """解析搜狗重定向链接，获取真实URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.sogou.com/',
            }
            resp = requests.get(redirect_url, headers=headers, timeout=10, allow_redirects=True)
            return resp.url
        except:
            return None

    def _fix_encoding(self, resp: requests.Response) -> requests.Response:
        """修复响应编码问题"""
        # 尝试检测编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']

        # 先尝试chardet
        try:
            import chardet
            detected = chardet.detect(resp.content)
            if detected and detected.get('encoding'):
                encodings.insert(0, detected['encoding'])
        except:
            pass

        # 尝试每种编码
        for enc in encodings:
            try:
                resp.encoding = enc
                test_text = resp.text
                # 检查是否乱码（检查是否有大量不可见字符）
                if '�' not in test_text[:1000] and len(test_text) > 100:
                    return resp
            except:
                continue

        # 最后尝试apparent_encoding
        try:
            resp.encoding = resp.apparent_encoding
        except:
            resp.encoding = 'utf-8'

        return resp

    def _is_blocked(self, text: str) -> bool:
        """检查是否被搜索引擎拦截（验证码页面）"""
        block_patterns = [
            '验证码',
            '请协助验证',
            '自动程序',
            '验证正常行为',
            'SourceVerifyCode',
            '此验证码用于确认',
        ]
        return any(p in text for p in block_patterns)

    def _is_news_page(self, url: str, html: str, content_length: int = 0) -> bool:
        """判断是否为新闻页面（非车型说明页）"""
        from bs4 import BeautifulSoup

        url_lower = url.lower()

        # 非新闻页面的明显特征（URL级别）
        bad_url_patterns = [
            'price.pcauto.com.cn/sg',    # 太平洋车型/报价页（sg开头）
            'price.pcauto.com.cn/cars/',  # 太平洋车型列表
            '/cars/',                     # 车型列表页
            '/photo/',                    # 图片页
            '/video/',                    # 视频页
            '/config/',                   # 配置页
            '/param/',                    # 参数页
            '/serie/',                    # 系列页
            '/guide/',                    # 购车指南页
        ]

        for pattern in bad_url_patterns:
            if pattern in url_lower:
                return False

        # 内容检查
        soup = BeautifulSoup(html, 'html.parser')
        title_elem = soup.find('title')
        title_text = title_elem.get_text() if title_elem else ""

        # 标题短且含这些词，大概率是车型页
        if len(title_text) < 20:
            bad_title_patterns = ['报价', '图片', '参数', '配置', '车型', '文章', '视频']
            for p in bad_title_patterns:
                if p in title_text:
                    return False

        # 正文长度检查：如果正文太短，可能不是新闻
        body_text = soup.get_text()
        if len(body_text) < 500:
            return False

        # 结合正文长度：如果URL是价格相关但正文短，也过滤
        if 'price' in url_lower and content_length < 1000:
            return False

        return True

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
