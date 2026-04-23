"""调试太平洋汽车日期解析"""
import re
from datetime import datetime

# 模拟解析"2026年04月28日上市"格式
test_dates = [
    "2026年04月28日上市",
    "2026年04月10日上市",
    "2021年05月10日上市",
]

for date_str in test_dates:
    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
    if match:
        pub_date = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        print(f"'{date_str}' -> {pub_date.strftime('%Y-%m-%d')}")
    else:
        print(f"'{date_str}' -> 解析失败")
