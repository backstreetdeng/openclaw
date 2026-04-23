"""测试PcautoCollector基本逻辑"""
from datetime import datetime

# 测试导入
try:
    from collector.browser_agent import PcautoCollector
    print("✓ PcautoCollector导入成功")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    exit(1)

# 测试实例化
collector = PcautoCollector()
print(f"✓ 实例化成功，URL: {collector.url}")

# 检查类方法
print(f"✓ collect方法存在: {hasattr(collector, 'collect')}")
print(f"✓ _fetch_article_content方法存在: {hasattr(collector, '_fetch_article_content')}")

# 检查collect方法签名
import inspect
sig = inspect.signature(collector.collect)
print(f"✓ collect签名: {sig}")

print("\n=== 语法检查通过 ===")
print("接下来需要实际运行GUI来测试太平洋汽车采集")
