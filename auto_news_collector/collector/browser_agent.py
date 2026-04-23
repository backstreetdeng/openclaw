from datetime import datetime
from typing import List, Dict

class MacroCollector:
    """宏观经济政策采集器 - 支持gov.cn和eastmoney.com"""

    def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        sub_domains: Dict[str, Dict] = None
    ) -> Dict[str, List[Dict]]:
        """
        采集宏观经济政策

        Args:
            start_date: 开始日期
            end_date: 结束日期
            sub_domains: 分领域配置 {
                "要闻": {"url": "...", "keywords": [...], "max_count": 3},
                "政策": {...},
                ...
            }

        Returns:
            Dict[str, List[Dict]] - {分领域名称: [新闻列表]}
        """
        if not sub_domains:
            return {}

        results = {}

        for sub_name, sub_config in sub_domains.items():
            url = sub_config.get("url", "")
            keywords = sub_config.get("keywords", [])
            max_count = sub_config.get("max_count", 3)

            try:
                if "gov.cn" in url:
                    news = self._collect_gov(url, start_date, end_date, keywords, max_count)
                elif "eastmoney.com" in url:
                    news = self._collect_eastmoney(url, start_date, end_date, keywords, max_count)
                else:
                    news = []
            except Exception as e:
                print(f"MacroCollector采集失败 {sub_name}: {e}")
                news = []

            results[sub_name] = news
            print(f"  {sub_name}: {len(news)}条")

        return results

    def _collect_gov(
        self,
        url: str,
        start_date: datetime,
        end_date: datetime,
        keywords: List[str],
        max_count: int
    ) -> List[Dict]:
        """采集gov.cn文章 - 使用JSON API + 正文抓取"""
        import requests
        import re
        import time

        results = []

        try:
            # JSON URL格式：
            # 要闻: /yaowen/liebiao/ -> YAOWENLIEBIAO.json (正序)
            # 政策: /zhengce/zuixin/ -> ZUIXINZHENGCE.json (反序)
            base_url = url.rstrip('/')
            path_part = base_url.replace('https://www.gov.cn', '').strip('/')
            parts = path_part.split('/')

            # 根据路径决定是否反转
            if path_part.startswith('yaowen'):
                # 要闻：正序
                json_path = path_part.upper().replace('/', '')
            else:
                # 其他（如政策）：反序
                json_path = ''.join(reversed(parts)).upper()

            json_url = f"{base_url}/{json_path}.json"

            resp = requests.get(json_url, timeout=30)
            data = resp.json()

            for item in data:
                if len(results) >= max_count:
                    break

                title = item.get('TITLE', '')
                article_url = item.get('URL', '')
                date_str = (item.get('DOCRELPUBTIME', '') or
                           item.get('DOC_REL_PUBTIME', '') or
                           item.get('TIME', '') or
                           item.get('date', ''))

                # 解析日期
                pub_date = None
                if date_str:
                    try:
                        pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    except:
                        pass

                # 日期过滤
                if pub_date and not (start_date <= pub_date <= end_date):
                    continue

                # 关键字过滤
                if keywords and not any(k in title for k in keywords):
                    continue

                if title and article_url:
                    # 抓取正文
                    content = self._fetch_gov_article(article_url)

                    results.append({
                        "title": title,
                        "link": article_url if article_url.startswith("http") else f"https://www.gov.cn{article_url}",
                        "date": date_str[:10] if date_str else (pub_date.strftime("%Y-%m-%d") if pub_date else ""),
                        "content": content,
                        "source": "gov.cn"
                    })

                    # 延时避免请求过快
                    time.sleep(1)

        except Exception as e:
            print(f"_collect_gov失败: {e}")

        return results[:max_count]

    def _fetch_gov_article(self, url: str) -> str:
        """抓取gov.cn文章正文"""
        import requests
        from bs4 import BeautifulSoup

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            resp = requests.get(url, headers=headers, timeout=15)
            resp.encoding = 'utf-8'

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 移除脚本和样式
            for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()

            # 查找文章主体 - gov.cn通常在div.detail或div.article里
            article = soup.find('div', class_='detail') or \
                     soup.find('div', class_='article') or \
                     soup.find('div', id='zoom')

            if article:
                # 提取所有段落
                paragraphs = article.find_all('p')
                if paragraphs:
                    text = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                    return text

                # 直接获取文本
                return article.get_text(separator='\n', strip=True)

            # 备选：查找最大的文本块
            body = soup.find('body')
            if body:
                return body.get_text(separator='\n', strip=True)[:5000]

        except Exception as e:
            print(f"_fetch_gov_article失败: {e}")

        return ""

    def _collect_eastmoney(
        self,
        url: str,
        start_date: datetime,
        end_date: datetime,
        keywords: List[str],  # 传入关键字列表，国内经济用DEPARTMENT_PATTERNS，国际经济用["美联储"]
        max_count: int
    ) -> List[Dict]:
        """采集eastmoney.com文章 - 使用API"""
        import time
        import re
        import requests as req

        results = []

        # 国内经济部门正则匹配
        DEPARTMENT_PATTERNS = [
            (r"国家发展改革委|国家发展和改革委员会|发改委", "发改委"),
            (r"财政部", "财政部"),
            (r"商务部", "商务部"),
            (r"工业和信息化部|工信部", "工信部"),
            (r"科学技术部|科技部", "科技部"),
            (r"中国人民银行|央行", "央行"),
            (r"银行保险监督管理委员会|银保监会|银保监", "银保监会"),
            (r"证券监督管理委员会|证监会|证监", "证监会"),
            (r"国家外汇管理局|外汇管理局|外汇局", "外汇管理局"),
            (r"住房和城乡建设部|住建部|住房城乡建设部", "住建部"),
            (r"交通运输部|交通部", "交通运输部"),
            (r"农业农村部|农业部", "农业部"),
            (r"自然资源部", "自然资源部"),
            (r"生态环境部|环境保护部|环保部", "生态环境部"),
            (r"教育部", "教育部"),
            (r"文化和旅游部|文旅部", "文旅部"),
            (r"国家卫生健康委员会|卫生健康委|卫健委", "卫健委"),
            (r"公安部", "公安部"),
            (r"民政部", "民政部"),
            (r"司法部", "司法部"),
            (r"人力资源和社会保障部|人力资源社会保障部|人社部", "人社部"),
            (r"退役军人事务部|退役军人部", "退役军人部"),
            (r"应急管理部|应急部", "应急管理部"),
            (r"国家市场监督管理总局|市场监管总局|市场监督管理", "市场监管总局"),
            (r"国有资产监督管理委员会|国资委|国资", "国资委"),
            (r"国家能源局|能源局", "能源局"),
            (r"水利部", "水利部"),
            (r"审计署", "审计署"),
            (r"国家统计局|统计局", "统计局"),
            (r"海关总署|海关", "海关总署"),
            (r"国家税务总局|税务总局|税务", "税务总局"),
            (r"国家烟草专卖局|烟草专卖局", "烟草专卖局"),
            (r"国家知识产权局|知识产权局", "知识产权局"),
            (r"国家药品监督管理局|药监局|药品监管", "药监局"),
            (r"外交部", "外交部"),
            (r"国防部", "国防部"),
            (r"国家互联网信息办公室|网信办|互联网信息办", "网信办"),
            (r"国家安全部|安全部", "国家安全部"),
            (r"国务院港澳事务办公室|港澳办", "港澳办"),
            (r"国务院台湾事务办公室|台办", "台办"),
            (r"人民银行", "人民银行"),
            (r"国际发展合作署", "国际发展合作署"),
            (r"国家医疗保障局|医保局|医疗保障局", "医保局"),
            (r"国家信访局|信访局", "信访局"),
            (r"国家粮食和物资储备局|粮食储备局|粮储局", "粮食储备局"),
            (r"国家林业和草原局|林草局|林业和草原局", "林草局"),
            (r"国家铁路局|铁路局", "铁路局"),
            (r"中国民用航空局|民航局|民用航空局", "民航局"),
            (r"国家邮政局|邮政局", "邮政局"),
            (r"国家文物局|文物局", "文物局"),
            (r"国家中医药管理局|中医药局", "中医药局"),
            (r"国家疾病预防控制局|疾控局|疾病预防控制局", "疾控局"),
            (r"国家移民管理局|移民局", "移民局"),
            (r"国家消防救援局|消防救援局", "消防救援局"),
            (r"国家矿山安全监察局|矿山安监局", "矿山安监局"),
            (r"国家保密局|保密局", "保密局"),
            (r"国家密码管理局|密码局", "密码管理局"),
            (r"国家档案局|档案局", "档案局"),
        ]

        try:
            # 判断是国内经济还是国际经济
            # 国内经济: column=350, URL包含cgnjj
            # 国际经济: column=351, URL包含cgjjj
            column = "350"
            if "cgjjj" in url.lower():
                column = "351"

            api_url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
            params = {
                'client': 'web',
                'biz': 'web_news_col',
                'column': column,
                'order': '1',
                'needInteractData': '0',
                'page_index': '1',
                'page_size': str(max_count * 3),  # 多获取一些用于过滤
                'req_trace': str(int(time.time() * 1000)),
                'fields': 'code,showTime,title,mediaName,summary,image,url,uniqueUrl,Np_dst',
                'types': '1,20',
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': url,
            }

            resp = req.get(api_url, params=params, headers=headers, timeout=30)
            data = resp.json()
            news_list = data.get('data', {}).get('list', [])

            for n in news_list:
                if len(results) >= max_count:
                    break

                title = n.get('title', '')
                showtime = n.get('showTime', '')[:10] if n.get('showTime') else ''
                article_url = n.get('url', '') or n.get('uniqueUrl', '')

                # 解析日期
                pub_date = None
                if showtime:
                    try:
                        pub_date = datetime.strptime(showtime[:10], "%Y-%m-%d")
                    except:
                        pass

                # 日期过滤
                if pub_date and not (start_date <= pub_date <= end_date):
                    continue

                # 关键字过滤
                if column == "350":
                    # 国内经济：使用DEPARTMENT_PATTERNS正则匹配
                    matched = False
                    for pattern, dept_name in DEPARTMENT_PATTERNS:
                        if re.search(pattern, title):
                            matched = True
                            break
                    if not matched:
                        continue
                else:
                    # 国际经济：标题包含关键字（只有"美联储"）
                    if keywords and not any(k in title for k in keywords):
                        continue

                if title:
                    results.append({
                        "title": title,
                        "link": article_url if article_url.startswith("http") else f"https://finance.eastmoney.com{article_url}",
                        "date": showtime,
                        "content": title,
                        "source": "eastmoney"
                    })

        except Exception as e:
            print(f"_collect_eastmoney失败: {e}")

        return results[:max_count]