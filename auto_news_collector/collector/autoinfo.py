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
        self._engine_index = 0  # 轮询计数器

    def collect(self, start_date: datetime, end_date: datetime, max_count: int = 10) -> List[Dict]:
        """
        统一采集逻辑：
        1. 获取所有数据（newPolicy + policyReport）
        2. 统一做时间范围过滤
        3. 统一做 province="国家" OR 关键字 过滤
        4. 去重
        5. 补充正文（通过搜索引擎）
        """
        all_results = []
        seen_titles = set()

        # 1. 获取newPolicy数据（已做时间过滤）
        new_policy_results = self._collect_new_policy(start_date, end_date, max_count)
        all_results.extend(new_policy_results)

        # 2. 获取policyReport数据（已做时间过滤）
        if len(all_results) < max_count * 2:
            report_results = self._collect_policy_report(start_date, end_date, max_count * 2)
            all_results.extend(report_results)

        # 3. 统一做 province="国家" OR 关键字 过滤
        filtered = []
        for item in all_results:
            title = item['title']
            province = item.get('province', '')

            cond1 = (province == "国家")
            cond2 = any(k in title for k in self.include_keywords)

            if cond1 or cond2:
                if title not in seen_titles:
                    filtered.append(item)
                    seen_titles.add(title)

        # 4. 截取max_count
        filtered = filtered[:max_count]

        # 5. 通过搜索引擎补充正文
        for item in filtered:
            search_result = self._fetch_content_via_search(item['title'])

            # 优先用搜索结果的URL和正文
            if search_result.get("url"):
                item['link'] = search_result.get("url")
            if search_result.get("content") and len(search_result.get("content", "")) > 30:
                item['content'] = search_result.get("content")

        return filtered

    def _collect_new_policy(self, start_date: datetime, end_date: datetime, max_count: int) -> List[Dict]:
        """只做时间范围过滤，其他筛选在collect()里统一处理"""
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

                    # 只做时间范围过滤
                    if not (pub_date and (start_date <= pub_date <= end_date)):
                        continue

                    results.append({
                        "title": title,
                        "link": f"https://www.autoinfo.org.cn/#/policy/dynamic/index?id={article_id}" if article_id else "",
                        "date": public_date_str[:10] if public_date_str else "",
                        "content": title,  # 先用标题占位
                        "source": "autoinfo",
                        "province": province,
                        "article_id": article_id,
                    })
                except Exception as e:
                    print(f"处理newPolicy记录失败: {e}")
                    continue

        except Exception as e:
            print(f"_collect_new_policy失败: {e}")

        return results[:max_count]

    def _collect_policy_report(self, start_date: datetime, end_date: datetime, max_count: int) -> List[Dict]:
        """只做时间范围过滤，其他筛选在collect()里统一处理"""
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
                    summary = record.get('summary', '') or ''

                    pub_date = None
                    if public_date_str:
                        try:
                            pub_date = datetime.strptime(str(public_date_str)[:10], "%Y-%m-%d")
                        except:
                            pass

                    # 只做时间范围过滤
                    if pub_date and not (start_date <= pub_date <= end_date):
                        continue

                    results.append({
                        "title": title,
                        "link": f"https://www.autoinfo.org.cn/#/policy/dynamic/index?id={article_id}" if article_id else "",
                        "date": public_date_str[:10] if public_date_str else "",
                        "content": summary if summary else title,  # 优先用摘要
                        "source": "autoinfo",
                        "province": "",  # policyReport没有province字段
                        "article_id": article_id,
                    })
                except Exception as e:
                    print(f"处理policyReport记录失败: {e}")
                    continue

        except Exception as e:
            print(f"_collect_policy_report失败: {e}")

        return results[:max_count]

    def _fetch_content_via_search(self, title: str) -> dict:
        """用标题在一个搜索引擎搜索（轮询分配），获取正文和URL，总超时25秒"""
        if not title:
            return {"content": "", "url": ""}

        start_time = time.time()
        max_total_time = 25  # 总超时25秒

        # 轮询分配引擎：每条新闻只用1个引擎，避免重复请求
        engines = [
            ("百度", self._search_baidu),
            ("360", self._search_360),
            ("搜狗", self._search_sogou),
            ("必应", self._search_bing),
        ]

        idx = self._engine_index % len(engines)
        self._engine_index += 1

        engine_name = engines[idx][0]
        search_func = engines[idx][1]

        try:
            result = search_func(title)
            if result and result.get("content") and len(result.get("content", "")) > 30:
                print(f"  [Autoinfo] {engine_name}获取成功")
                return result
        except Exception as e:
            print(f"  [Autoinfo] {engine_name}失败: {e}")

        return {"content": "", "url": ""}

    def _search_bing(self, query: str) -> dict:
        time.sleep(random.uniform(1, 2))

        url = f"https://cn.bing.com/search?q={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'

        if self._is_blocked(resp.text):
            return {"content": "", "url": ""}

        return self._extract_bing_content(resp.text)

    def _extract_bing_content(self, html: str) -> dict:
        """从必应搜索结果提取正文和URL（必应使用li.b_algo结构）"""
        if len(html) < 10000:
            return {"content": "", "url": ""}

        soup = BeautifulSoup(html, 'html.parser')

        # 必应使用 li.b_algo 选择器
        results = []
        for item in soup.select('li.b_algo'):
            a = item.select_one('h2 a') or item.select_one('a')
            if not a:
                continue
            href = a.get('href', '')
            if href.startswith('http') and 'baidu.com' not in href:
                results.append({'url': href})

        if not results:
            return {"content": "", "url": ""}

        # 尝试前2个URL
        for result in results[:2]:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                resp = requests.get(result['url'], headers=headers, timeout=8)
                resp.encoding = 'utf-8'

                soup = BeautifulSoup(resp.text, 'html.parser')
                for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()

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
                        if len(text) > 30:
                            return {"content": text, "url": result['url']}
                    text = article.get_text(separator='\n', strip=True)
                    if len(text) > 30:
                        return {"content": text, "url": result['url']}
            except:
                continue

        return {"content": "", "url": ""}

    def _search_baidu(self, query: str) -> dict:
        time.sleep(random.uniform(1, 2))

        url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.baidu.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
