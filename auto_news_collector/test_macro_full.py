"""完整测试MacroCollector"""
from collector.browser_agent import MacroCollector
from datetime import datetime

sub_domains = {
    "要闻": {
        "url": "https://www.gov.cn/yaowen/liebiao/",
        "keywords": ["国务院常务会", "国务院常务会议", "政治局会议", "总书记"],
        "max_count": 3,
    },
    "政策": {
        "url": "https://www.gov.cn/zhengce/zuixin/",
        "keywords": ["消费", "投资", "外贸", "出口", "进口", "民生", "就业", "大市场"],
        "max_count": 3,
    },
    "国内经济": {
        "url": "https://finance.eastmoney.com/",
        "keywords": ["部"],
        "max_count": 3,
    },
    "国际经济": {
        "url": "https://finance.eastmoney.com/",
        "keywords": ["美联储"],
        "max_count": 3,
    },
}

start_date = datetime(2026, 4, 18)
end_date = datetime(2026, 4, 24)

collector = MacroCollector()
results = collector.collect(start_date, end_date, sub_domains)

print("\n=== 测试结果 ===")
for sub_name, news in results.items():
    print(f"\n【{sub_name}】({len(news)}条)")
    for i, n in enumerate(news[:3], 1):
        print(f"  {i}. [{n['date']}] {n['title'][:40]}")
