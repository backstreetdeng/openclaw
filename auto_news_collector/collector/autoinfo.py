"""
AutoinfoCollector - 政策法规API采集器
调用 autoinfo.org.cn 的 API 获取政策法规数据

需求：
1. API接口1（最新政策）：https://www.autoinfo.org.cn/prod-api/api/policy/ttPolicy/newPolicy
   - province字段="国家"
   - title含关键字（消费/促销费/以旧换新/补贴/购车/购车补贴/补贴细则）
   - publicDate在监测时间范围内
   - 并集关系：满足任一即采集

2. API接口2（政策报道）：https://www.autoinfo.org.cn/prod-api/api/policy/ttPolicyReport/policyReport
   - publicDate在监测时间范围内

3. pageSize必须=30，禁止用其他值
"""

import requests
from datetime import datetime
from typing import List, Dict


class AutoinfoCollector:
    """政策法规API采集器"""

    def __init__(self):
        # API接口
        self.api_new_policy = "https://www.autoinfo.org.cn/prod-api/api/policy/ttPolicy/newPolicy"
        self.api_policy_report = "https://www.autoinfo.org.cn/prod-api/api/policy/ttPolicyReport/policyReport"
        # 关键字
        self.include_keywords = ["消费", "促销费", "以旧换新", "补贴", "购车", "购车补贴", "补贴细则"]

    def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        max_count: int = 10
    ) -> List[Dict]:
        """
        采集政策法规新闻

        Args:
            start_date: 开始日期
            end_date: 结束日期
            max_count: 最大条数

        Returns:
            List[Dict] - 新闻列表
        """
        results = []
        seen_titles = set()  # 去重

        # 1. 调用最新政策API
        new_policy_results = self._collect_new_policy(start_date, end_date, max_count)
        for item in new_policy_results:
            if item['title'] not in seen_titles:
                results.append(item)
                seen_titles.add(item['title'])

        # 2. 调用政策报道API
        if len(results) < max_count:
            report_results = self._collect_policy_report(start_date, end_date, max_count)
            for item in report_results:
                if item['title'] not in seen_titles and len(results) < max_count:
                    results.append(item)
                    seen_titles.add(item['title'])

        return results[:max_count]

    def _collect_new_policy(
        self,
        start_date: datetime,
        end_date: datetime,
        max_count: int
    ) -> List[Dict]:
        """采集最新政策（API接口1）"""
        results = []

        try:
            params = {
                'pageNum': 1,
                'pageSize': 30,  # 必须=30
                'flag': '0',
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.autoinfo.org.cn/',
            }

            response = requests.get(self.api_new_policy, params=params, headers=headers, timeout=30)
            data = response.json()

            records = data.get('data', {}).get('rows', []) if isinstance(data, dict) else []

            for record in records:
                try:
                    title = record.get('title', '') or record.get('policyName', '')
                    province = record.get('province', '')  # 省份字段
                    public_date_str = record.get('publicDate', '') or record.get('publishTime', '')
                    article_id = record.get('id', '')

                    # 解析日期
                    pub_date = None
                    if public_date_str:
                        try:
                            pub_date = datetime.strptime(str(public_date_str)[:10], "%Y-%m-%d")
                        except:
                            pass

                    # 判断是否满足采集条件
                    # 条件3（时间要求）：强制的，所有采集都必须满足
                    if not (pub_date and (start_date <= pub_date <= end_date)):
                        continue

                    # 条件1 OR 条件2（并集关系）：满足任一即采集
                    cond1 = (province == "国家")
                    cond2 = any(k in title for k in self.include_keywords)

                    # 满足(条件1 OR 条件2) AND 条件3
                    if not (cond1 or cond2):
                        continue

                    # 构建URL
                    article_url = f"https://www.autoinfo.org.cn/#/policy/dynamic/index?id={article_id}" if article_id else ""

                    # 抓取正文
                    content = self._fetch_article_content(article_url) if article_url else ""

                    results.append({
                        "title": title,
                        "link": article_url,
                        "date": public_date_str[:10] if public_date_str else (pub_date.strftime("%Y-%m-%d") if pub_date else ""),
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

    def _collect_policy_report(
        self,
        start_date: datetime,
        end_date: datetime,
        max_count: int
    ) -> List[Dict]:
        """采集政策报道（API接口2）"""
        results = []

        try:
            params = {
                'pageNum': 1,
                'pageSize': 30,  # 必须=30
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.autoinfo.org.cn/',
            }

            response = requests.get(self.api_policy_report, params=params, headers=headers, timeout=30)
            data = response.json()

            records = data.get('data', {}).get('rows', []) if isinstance(data, dict) else []

            for record in records:
                try:
                    title = record.get('title', '') or record.get('policyName', '')
                    public_date_str = record.get('publicDate', '') or record.get('publishTime', '')
                    article_id = record.get('id', '')

                    # 解析日期
                    pub_date = None
                    if public_date_str:
                        try:
                            pub_date = datetime.strptime(str(public_date_str)[:10], "%Y-%m-%d")
                        except:
                            pass

                    # 时间过滤
                    if pub_date and not (start_date <= pub_date <= end_date):
                        continue

                    # 构建URL
                    article_url = f"https://www.autoinfo.org.cn/#/policy/dynamic/index?id={article_id}" if article_id else ""

                    # 抓取正文
                    content = self._fetch_article_content(article_url) if article_url else ""

                    results.append({
                        "title": title,
                        "link": article_url,
                        "date": public_date_str[:10] if public_date_str else (pub_date.strftime("%Y-%m-%d") if pub_date else ""),
                        "content": content if content else title,
                        "source": "autoinfo",
                    })

                except Exception as e:
                    print(f"处理policyReport记录失败: {e}")
                    continue

        except Exception as e:
            print(f"_collect_policy_report失败: {e}")

        return results[:max_count]

    def _fetch_article_content(self, url: str) -> str:
        """抓取文章正文"""
        if not url:
            return ""

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': 'https://www.autoinfo.org.cn/',
            }
            resp = requests.get(url, headers=headers, timeout=15)
            resp.encoding = 'utf-8'

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 移除脚本和样式
            for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()

            # 查找文章主体
            article = soup.find('div', class_='article-content') or \
                     soup.find('div', class_='policy-content') or \
                     soup.find('div', id='ContentBody') or \
                     soup.find('div', class_='detail')

            if article:
                paragraphs = article.find_all('p')
                if paragraphs:
                    text = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                    return text
                return article.get_text(separator='\n', strip=True)

            body = soup.find('body')
            if body:
                return body.get_text(separator='\n', strip=True)[:5000]

        except Exception as e:
            print(f"_fetch_article_content失败: {e}")

        return ""
