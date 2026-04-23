"""
检查领域6配置
"""
import sys
sys.path.insert(0, r'E:\openclaw\workspace\auto_news_collector')
from config import DOMAINS

cfg = DOMAINS.get('新车上市', {})
print('新车上市配置:')
print('urls:', cfg.get('urls', []))
print('include_keywords:', cfg.get('include_keywords', []))
print('exclude_keywords:', cfg.get('exclude_keywords', []))
print('max_count:', cfg.get('max_count', 10))
print('pcauto_check_date:', cfg.get('pcauto_check_date', False))
