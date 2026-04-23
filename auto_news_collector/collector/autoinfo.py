"""
AutoinfoCollector - 政策法规API采集器
"""

import requests
import time
import random
import urllib.parse
from datetime import datetime
from typing import List, Dict
from bs4 import BeautifulSoup


class AutoinfoCollector:
    """政策法规API采集器"""

    def __init__(self):
        self.api_new_policy = "https://www.autoinfo.org.cn/prod-api/api/policy/ttPolicy/newPolicy"
        self.api_policy_report = "https://www.autoinfo.org.cn/prod-api/api/policy/ttPolicyReport/policyReport"
        self.include_keywords = ["消费", "促销费", "以旧换新", "补贴", "购车", "购车补贴", "补贴细则"]

    def collect(self, start_date: datetime, end_date: datetime, max_count: int = 10) -> List[Dict]:
        results = []
        seen_titles = set()

        new_policy_results = self._collect_new_policy(start_date, end_date, max_count)
        for item in new_policy_results:
            if item['title'] not in seen_titles:
                results.append(item)
                seen_titles.add(item['title'])

        if len(results) < max_count:
            report_results = self._collect_policy_report(start_date, end_date, max_count)
            for item in report_results:
                if item['title'] not in seen_titles and len(results) < max_count:
                    results.append(item)
                    seen_titles.add(item['title'])

        return results[:max_count]

    def _collect_new_policy(self, start_date: datetime, end_date: datetime, max_count: int) -> List[Dict]:
        results = []
        try:
            params = {'pageNum': 1, 'pageSize': 30, 'flag': '0'}
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.autoinfo.org.cn/'}
            response = requests.get(self.api_new_policy, params=params, headers=headers, timeout=30)
            data = response.json()

            if not isinstance(data, dict):
                return []

            records = data.get('data', [])

            for record in records:
                try:
                    title = record.get('title', '')
                    province = record.get('province', '')
                    public_date_str = record.get('publicDate', '') or record.get('publishDate', '')
                    article_id = record.get('id', '')

                    pub_date = None
                    if public_date_str:
                        try:
                            pub_date = datetime.strptime(str(public_date_str)[:10], "%Y-%m-%d")
                        except:
                            pass

                    if not (pub_date and (start_date <= pub_date <= end_date)):
                        continue

                    cond1 = (province == "国家")
                    cond2 = any(k in title for k in self.include_keywords)

                    if not (cond1 or cond2):
                        continue

                    # 优先用搜索引擎获取正文和URL（如果搜索失败则用autoinfo链接+标题）
                    search_result = self._fetch_content_via_search(title)

                    article_url = search_result.get("url") or f"https://www.autoinfo.org.cn/#/policy/dynamic/index?id={article_id}" if article_id else ""

                    # 如果搜索返回了有效正文（>30字符），则使用；否则尝试API摘要
                    content = search_result.get("content", "")
                    if not content or len(content) < 30:
                        summary = record.get('summary', '') or record.get('description', '') or ''
                        content = summary if len(summary) > 20 else title

                    results.append({
                        "title": title,
                        "link": article_url,
                        "date": public_date_str[:10] if public_date_str else "",
                        "content": content,
                        "source": "autoinfo",
                        "province": province,
                    })
                except Exception as e:
                    print(f"处理newPolicy记录失败: {e}")
                    continue

        except Exception as e:
            print(f"_collect_new_policy失败: {e}")

        return results[:max_count]

    def _collect_policy_report(self, start_date: datetime, end_date: datetime, max_count: int) -> List[Dict]:
        results = []
        try:
            params = {'pageNum': 1, 'pageSize': 30}
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.autoinfo.org.cn/'}
            response = requests.get(self.api_policy_report, params=params, headers=headers, timeout=30)
            data = response.json()

            if not isinstance(data, dict):
                return []

            records = data.get('data', [])

            for record in records:
                try:
                    title = record.get('title', '')
                    public_date_str = record.get('publicDate', '') or record.get('publishDate', '')
                    article_id = record.get('id', '')

                    pub_date = None
                    if public_date_str:
                        try:
                            pub_date = datetime.strptime(str(public_date_str)[:10], "%Y-%m-%d")
                        except:
                            pass

                    if pub_date and not (start_date <= pub_date <= end_date):
                        continue

                    # 优先用搜索引擎获取正文和URL（如果搜索失败则用autoinfo链接+标题）
                    search_result = self._fetch_content_via_search(title)

                    article_url = search_result.get("url") or f"https://www.autoinfo.org.cn/#/policy/dynamic/index?id={article_id}" if article_id else ""

                    # 如果搜索返回了有效正文（>50字符），则使用；否则用标题
                    content = search_result.get("content", "")
                    if not content or len(content) < 50:
                        # 搜索失败时，尝试从API摘要获取有价值的内容
                        summary = record.get('summary', '') or record.get('description', '') or ''
                        content = summary if len(summary) > 50 else title

                    results.append({
                        "title": title,
                        "link": article_url,
                        "date": public_date_str[:10] if public_date_str else "",
                        "content": content,
                        "source": "autoinfo",
                    })
                except Exception as e:
                    print(f"处理policyReport记录失败: {e}")
                    continue

        except Exception as e:
            print(f"_collect_policy_report失败: {e}")

        return results[:max_count]

    def _fetch_content_via_search(self, title: str) -> dict:
        """用标题在多个搜索引擎搜索，获取正文和URL，总超时30秒"""
        if not title:
            return {"content": "", "url": ""}

        start_time = time.time()
        max_total_time = 30  # 总超时30秒

        # 搜索引勤列表（不限网站，广撒网）
        engines = [
            ("百度", self._search_baidu),
            ("360", self._search_360),
            ("搜狗", self._search_sogou),
            ("必应", self._search_bing),
        ]

        for engine_name, search_func in engines:
            # 检查总超时
            if time.time() - start_time > max_total_time:
                print(f"  [Autoinfo] 总超时，放弃搜索")
                break

            try:
                result = search_func(title)
                if result and result.get("content") and len(result.get("content", "")) > 50:
                    print(f"  [Autoinfo] {engine_name}获取成功")
                    return result
            except Exception as e:
                print(f"  [Autoinfo] {engine_name}失败: {e}")
                continue

        return {"content": "", "url": ""}

    def _search_bing(self, query: str) -> dict:
        time.sleep(random.uniform(1, 2))

        url = f"https://cn.bing.com/search?q={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'

        if self._is_blocked(resp.text):
            return {"content": "", "url": ""}

        return self._extract_content(resp.text)

    def _search_baidu(self, query: str) -> dict:
        time.sleep(random.uniform(1, 2))

        url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.baidu.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'

        if self._is_blocked(resp.text):
            return {"content": "", "url": ""}

        return self._extract_content(resp.text)

    def _search_360(self, query: str) -> dict:
        time.sleep(random.uniform(1, 2))

        url = f"https://www.so.com/s?q={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.360.cn/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'

        if self._is_blocked(resp.text):
            return {"content": "", "url": ""}

        return self._extract_content(resp.text)

    def _search_sogou(self, query: str) -> dict:
        time.sleep(random.uniform(1, 2))

        url = f"https://www.sogou.com/web?query={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.sogou.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'

        if self._is_blocked(resp.text):
            return {"content": "", "url": ""}

        return self._extract_content(resp.text)

    def _is_blocked(self, text: str) -> bool:
        if len(text) < 10000:  # 太小可能是安全页面
            return True
        return any(p in text for p in ['验证码', '请协助验证', '自动程序', 'SourceVerifyCode', '安全验证', '人身认证'])

    def _extract_content(self, html: str) -> dict:
        """从搜索结果提取正文和URL，不限制特定网站"""
        # 太小可能是安全页面，直接返回空
        if len(html) < 10000:
            return {"content": "", "url": ""}

        soup = BeautifulSoup(html, 'html.parser')

        # 查找所有可能的链接
        results = []
        for h3 in soup.find_all('h3'):
            a = h3.find('a', href=True)
            if not a:
                continue

            href = a.get('href', '')

            if href.startswith('/link?url='):
                try:
                    resp = requests.get(href, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5, allow_redirects=True)
                    real_url = resp.url
                except:
                    continue
            elif href.startswith('http'):
                real_url = href
            else:
                continue

            if real_url and len(real_url) > 10:
                results.append({'url': real_url})

        if not results:
            return {"content": "", "url": ""}

        # 只尝试前3个URL，减少时间
        for result in results[:3]:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                resp = requests.get(result['url'], headers=headers, timeout=8)
                resp.encoding = 'utf-8'

                soup = BeautifulSoup(resp.text, 'html.parser')
                for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()

                # 查找文章主体
                article = (soup.find('div', class_='article-content') or
                          soup.find('div', class_='news-content') or
                          soup.find('div', id='ContentBody') or
                          soup.find('article') or
                          soup.find('div', class_='detail') or
                          soup.find('div', class_='content'))

                if article:
                    paragraphs = article.find_all('p')
                    if paragraphs:
                        text = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        if len(text) > 100:
                            return {"content": text, "url": result['url']}
                    text = article.get_text(separator='\n', strip=True)
                    if len(text) > 100:
                        return {"content": text, "url": result['url']}
            except:
                continue

        return {"content": "", "url": ""}
