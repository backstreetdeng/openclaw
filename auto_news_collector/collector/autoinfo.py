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

                    article_url = f"https://www.autoinfo.org.cn/#/policy/dynamic/index?id={article_id}" if article_id else ""
                    content = self._fetch_content_via_search(title)

                    results.append({
                        "title": title,
                        "link": article_url,
                        "date": public_date_str[:10] if public_date_str else "",
                        "content": content if content else title,
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

                    article_url = f"https://www.autoinfo.org.cn/#/policy/dynamic/index?id={article_id}" if article_id else ""
                    content = self._fetch_content_via_search(title)

                    results.append({
                        "title": title,
                        "link": article_url,
                        "date": public_date_str[:10] if public_date_str else "",
                        "content": content if content else title,
                        "source": "autoinfo",
                    })
                except Exception as e:
                    print(f"处理policyReport记录失败: {e}")
                    continue

        except Exception as e:
            print(f"_collect_policy_report失败: {e}")

        return results[:max_count]

    def _fetch_content_via_search(self, title: str) -> str:
        if not title:
            return ""

        engines = [("必应", self._search_bing), ("百度", self._search_baidu)]

        for engine_name, search_func in engines:
            try:
                result = search_func(title)
                if result:
                    print(f"  [Autoinfo] {engine_name}搜索成功")
                    return result
            except Exception as e:
                print(f"  [Autoinfo] {engine_name}搜索失败: {e}")
                continue

        return title

    def _search_bing(self, query: str) -> str:
        time.sleep(random.uniform(3, 5))

        url = f"https://cn.bing.com/search?q={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        resp = requests.get(url, headers=headers, timeout=20)
        resp.encoding = 'utf-8'

        if self._is_blocked(resp.text):
            return None

        return self._extract_content(resp.text)

    def _search_baidu(self, query: str) -> str:
        time.sleep(random.uniform(3, 6))

        url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.baidu.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        resp = requests.get(url, headers=headers, timeout=20)
        resp.encoding = 'utf-8'

        if self._is_blocked(resp.text):
            return None

        return self._extract_content(resp.text)

    def _is_blocked(self, text: str) -> bool:
        return any(p in text for p in ['验证码', '请协助验证', '自动程序', 'SourceVerifyCode'])

    def _extract_content(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')

        trusted = ['gov.cn', 'people.com.cn', 'xinhuanet.com', 'cctv.com',
                   'autohome.com.cn', 'pcauto.com.cn', 'bitauto.com', 'dongchedi.com']

        results = []
        for h3 in soup.find_all('h3'):
            a = h3.find('a', href=True)
            if not a:
                continue

            href = a.get('href', '')

            if href.startswith('/link?url='):
                try:
                    resp = requests.get(href, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, allow_redirects=True)
                    real_url = resp.url
                except:
                    continue
            elif href.startswith('http'):
                real_url = href
            else:
                continue

            is_trusted = any(t in real_url for t in trusted)
            results.append({'url': real_url, 'trusted': is_trusted})

        if not results:
            return None

        results.sort(key=lambda x: x['trusted'], reverse=True)

        for result in results[:3]:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                resp = requests.get(result['url'], headers=headers, timeout=15)
                resp.encoding = 'utf-8'

                soup = BeautifulSoup(resp.text, 'html.parser')
                for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()

                article = (soup.find('div', class_='article-content') or
                          soup.find('div', class_='news-content') or
                          soup.find('div', id='ContentBody') or
                          soup.find('article') or
                          soup.find('div', class_='detail'))

                if article:
                    paragraphs = article.find_all('p')
                    if paragraphs:
                        text = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        if len(text) > 100:
                            return text
                    text = article.get_text(separator='\n', strip=True)
                    if len(text) > 100:
                        return text
            except:
                continue

        return None
