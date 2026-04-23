"""
AutoinfoCollector - 政策法规API采集器
调用 autoinfo.org.cn 的 API 获取政策法规数据
"""

import requests
from datetime import datetime
from typing import List, Dict


class AutoinfoCollector:
    """政策法规API采集器"""

    def __init__(self):
        self.api_url = "https://www.autoinfo.org.cn/prod-api/api/policy/ttPolicy/newPolicy"

    def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        max_count: int = 10,
        include_keywords: List[str] = None
    ) -> List[Dict]:
        """
        采集政策法规新闻

        Args:
            start_date: 开始日期
            end_date: 结束日期
            max_count: 最大条数
            include_keywords: 关键字过滤

        Returns:
            List[Dict] - 新闻列表
        """
        results = []
        include_keywords = include_keywords or []

        try:
            # 调用API
            params = {
                'pageNum': 1,
                'pageSize': max_count * 3,  # 多获取一些用于过滤
                'policyName': '',
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.autoinfo.org.cn/',
            }

            response = requests.get(self.api_url, params=params, headers=headers, timeout=30)
            data = response.json()

            # 解析返回数据
            records = data.get('data', {}).get('rows', []) if isinstance(data, dict) else []

            for record in records:
                if len(results) >= max_count:
                    break

                try:
                    title = record.get('policyName', '') or record.get('title', '')
                    article_url = record.get('id', '')
                    if article_url:
                        article_url = f"https://www.autoinfo.org.cn/#/policy/dynamic/index?id={article_url}"

                    # 获取日期
                    date_str = record.get('publishTime', '') or record.get('createTime', '')
                    pub_date = None
                    if date_str:
                        try:
                            if isinstance(date_str, int):
                                # 时间戳
                                pub_date = datetime.fromtimestamp(date_str / 1000)
                            else:
                                pub_date = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
                        except:
                            pass

                    # 日期过滤
                    if pub_date and not (start_date <= pub_date <= end_date):
                        continue

                    # 关键字过滤
                    if include_keywords:
                        if not any(k in title for k in include_keywords):
                            continue

                    # 检查是否带"国家"标签（用于领域8要求）
                    tag = record.get('tag', '') or record.get('policyType', '')

                    results.append({
                        "title": title,
                        "link": article_url,
                        "date": date_str[:10] if date_str else (pub_date.strftime("%Y-%m-%d") if pub_date else ""),
                        "content": title,  # API只返回标题，正文需要另外获取
                        "tag": tag,
                        "source": "autoinfo"
                    })

                except Exception as e:
                    print(f"处理记录失败: {e}")
                    continue

        except Exception as e:
            print(f"AutoinfoCollector采集失败: {e}")

        return results[:max_count]
