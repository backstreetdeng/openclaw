"""
PcautoCollector - 太平洋汽车新车上市采集器
按设计方案实现：https://price.pcauto.com.cn/cars/6/
"""

import re
import time
import requests
from datetime import datetime
from typing import List, Dict


class PcautoCollector:
    """太平洋汽车新车上市采集器"""

    def __init__(self):
        self.url = "https://price.pcauto.com.cn/cars/6/"

    def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        max_count: int = 10
    ) -> List[Dict]:
        """
        采集太平洋汽车新车上市新闻

        Args:
            start_date: 开始日期
            end_date: 结束日期
            max_count: 最大条数

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

                        results.append({
                            "title": f"{car_type}-{title}",
                            "link": link,
                            "date": pub_date.strftime("%Y-%m-%d") if pub_date else date_str,
                            "content": f"太平洋汽车：{title}",
                            "source": "pcauto"
                        })

                    except Exception as e:
                        print(f"处理条目失败: {e}")
                        continue

                browser.close()

        except Exception as e:
            print(f"PcautoCollector采集失败: {e}")

        return results[:max_count]
