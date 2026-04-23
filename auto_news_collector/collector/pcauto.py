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

                # 查找车辆条目
                # 选择器: li, .car-item, .list-item 或包含 car's 类的元素
                items = page.query_selector_all("li, .car-item, .list-item")
                if not items:
                    # 备选：查找所有包含 car 的 class 的 div
                    items = page.query_selector_all("[class*='car']")

                print(f"PcautoCollector: 找到 {len(items)} 个元素")

                for item in items:
                    if len(results) >= max_count:
                        break

                    try:
                        # 提取车型名称 - 通常在标题位置
                        title_elem = item.query_selector("a, .tit, .title, h3, h4")
                        if not title_elem:
                            continue
                        title = title_elem.inner_text().strip()

                        # 提取日期
                        date_elem = item.query_selector("span, i, .date, .time")
                        date_str = ""
                        if date_elem:
                            date_str = date_elem.inner_text().strip()

                        # 解析日期
                        pub_date = None
                        if date_str:
                            try:
                                # 尝试匹配 YYYY-MM-DD 或 YYYY/MM/DD 格式
                                match = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", date_str)
                                if match:
                                    pub_date = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                            except:
                                pass

                        # 日期过滤
                        if pub_date and not (start_date <= pub_date <= end_date):
                            continue

                        # 关键词过滤：只要"上市"或"预售"
                        if not any(kw in title for kw in ["上市", "预售"]):
                            continue

                        # 提取链接
                        link_elem = item.query_selector("a")
                        link = ""
                        if link_elem:
                            href = link_elem.get_attribute("href") or ""
                            link = href if href.startswith("http") else f"https://price.pcauto.com.cn{href}"

                        # 判断类型
                        car_type = "新车"
                        if "改款" in title:
                            car_type = "改款"
                        elif "预售" in title:
                            car_type = "预售"

                        results.append({
                            "title": f"{car_type}-{title}",
                            "link": link,
                            "date": date_str if date_str else (pub_date.strftime("%Y-%m-%d") if pub_date else ""),
                            "content": f"太平洋汽车：{title}",  # 暂时用标题作为content
                            "source": "pcauto"
                        })

                    except Exception as e:
                        print(f"处理条目失败: {e}")
                        continue

                browser.close()

        except Exception as e:
            print(f"PcautoCollector采集失败: {e}")

        return results[:max_count]
