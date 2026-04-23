"""
检查哪个browser_agent.py被加载
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collector.browser_agent
print(f"Module file: {collector.browser_agent.__file__}")

# 检查函数是否存在
print(f"fetch_article_content exists: {hasattr(collector.browser_agent, 'fetch_article_content')}")
print(f"GasgooCollector exists: {hasattr(collector.browser_agent, 'GasgooCollector')}")

# 检查函数是否是同一个
from collector.browser_agent import fetch_article_content as fa1
from collector.browser_agent import GasgooCollector

# 创建一个collector实例并检查
print(f"\n检查collector调用的fetch_article_content:")
import inspect
# 看看GasgooCollector.collect方法的源码
source = inspect.getsource(GasgooCollector.collect)
# 找到fetch_article_content那一行
for line in source.split('\n'):
    if 'fetch_article_content' in line:
        print(f"  Found: {line.strip()}")
