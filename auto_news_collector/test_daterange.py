"""测试日期范围计算"""
import sys
sys.path.insert(0, "E:\\openclaw\\workspace\\auto_news_collector")

from datetime import datetime, timedelta

# 模拟MainWindow的日期计算逻辑
def get_week_range():
    """计算当前周的时间范围：上周六 → 本周五"""
    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    this_friday = today + timedelta(days=days_until_friday)
    last_saturday = this_friday - timedelta(days=6)
    return last_saturday, this_friday

def get_two_week_range():
    """计算近两周的时间范围：上上周六 → 本周五"""
    last_saturday, this_friday = get_week_range()
    two_weeks_ago = last_saturday - timedelta(days=7)
    return two_weeks_ago, this_friday

def get_month_range():
    """计算近一个月的时间范围：上月初 → 本周五"""
    from datetime import timedelta
    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    this_friday = today + timedelta(days=days_until_friday)
    first_day_this_month = today.replace(day=1)
    if first_day_this_month.weekday() == 6:
        first_day_this_month = first_day_this_month - timedelta(days=1)
    last_month_start = first_day_this_month - timedelta(days=first_day_this_month.weekday() + 1)
    return last_month_start, this_friday

today = datetime.now()
weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

print("=" * 60)
print(f"当前日期: {today.strftime('%Y-%m-%d')} {weekday_names[today.weekday()]}")
print("=" * 60)

print("\n[1] 近一周（周六→周五）")
start, end = get_week_range()
print(f"    {start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}")

print("\n[2] 近两周")
start, end = get_two_week_range()
print(f"    {start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}")

print("\n[3] 近一个月")
start, end = get_month_range()
print(f"    {start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}")

print("\n" + "=" * 60)
print("验证：当前周期应该是 2026-04-18 至 2026-04-24")
print("=" * 60)
