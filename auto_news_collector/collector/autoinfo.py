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

            # 实际返回格式：{"total":..., "data": [...], "code":..., "msg":...}
            if not isinstance(data, dict):
                print(f"_collect_new_policy: 返回数据类型是 {type(data)}，不是dict")
                return []

            records = data.get('data', [])  # 直接是list，不是 {'rows': [...]}

            for record in records:
                try:
                    title = record.get('title', '')
                    province = record.get('province', '')  # 省份字段
                    public_date_str = record.get('publicDate', '') or record.get('publishDate', '')
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

            # 实际返回格式：{"total":..., "data": [...], "code":..., "msg":...}
            if not isinstance(data, dict):
                print(f"_collect_policy_report: 返回数据类型是 {type(data)}，不是dict")
                return []

            records = data.get('data', [])  # 直接是list

            for record in records:
                try:
                    title = record.get('title', '')
                    public_date_str = record.get('publicDate', '') or record.get('publishDate', '')
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
        """使用Playwright抓取SPA网站的文章正文"""
        if not url:
            return ""

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                try:
                    page.goto(url, timeout=30000)
                    # 等待内容加载
                    page.wait_for_load_state("networkidle", timeout=15000)
                    # 等待文章主体出现
                    page.wait_for_selector("div.policy-content, div.article-content, div.detail, #ContentBody", timeout=10000)

                    # 获取正文
                    article = page.query_selector("div.policy-content") or \
                            page.query_selector("div.article-content") or \
                            page.query_selector("div.detail") or \
                            page.query_selector("#ContentBody")

                    if article:
                        # 提取所有段落
                        paragraphs = article.query_selector_all("p")
                        if paragraphs:
                            texts = [p.inner_text().strip() for p in paragraphs if p.inner_text().strip()]
                            return "\n".join(texts)

                        return article.inner_text()

                    # 备选：获取body文本
                    body = page.query_selector("body")
                    if body:
                        return body.inner_text()[:5000]

                finally:
                    browser.close()

        except Exception as e:
            print(f"_fetch_article_content失败: {e}")

        return ""
