"""
检查领域5配置
"""
import sys
sys.path.insert(0, r'E:\openclaw\workspace\auto_news_collector')
from config import DOMAINS

cfg = DOMAINS.get('新技术/新趋势', {})
subs = cfg.get('sub_domains', {})
print('新技术/新趋势配置:')
print(f'  子领域数: {len(subs)}')
for name, sub in subs.items():
    print(f'    {name}:')
    print(f'      url: {sub.get("url")}')
    print(f'      max_count: {sub.get("max_count")}')
