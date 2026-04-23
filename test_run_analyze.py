import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'E:\openclaw\workspace')
from ppt_quick_analyze import run

ppt_path = r'D:\2026年度工作日志和备忘录\小龙虾\5. 场景开发\PPT\测试-生成数据分析.pptx'
result = run(ppt_path)

print()
print('Summary:')
print('  Image paths:', len(result['image_paths']))
print('  Image tasks needed:', len(result['image_tasks']))
print('  Report path:', result['report_path'])
