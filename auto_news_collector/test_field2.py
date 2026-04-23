"""
领域2：企业要闻 - 采集测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from collector.browser_agent import GasgooCollector

# 当前周期
today = datetime.now()
days_until_friday = (4 - today.weekday()) % 7
this_friday = today + timedelta(days=days_until_friday)
last_saturday = this_friday - timedelta(days=6)

start_date = last_saturday
end_date = this_friday

print(f"时间范围: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
print("="*60)

# 品牌分类
brand_categories = {
    "豪华品牌车企": [
        "阿斯顿·马丁", "奥迪", "宝马", "迷你", "DS", "保时捷", "奔驰", "讴歌", "宾利", "斯玛特",
        "英菲尼迪", "法拉利", "雷克萨斯", "林肯", "捷豹", "劳斯莱斯", "路虎", "莲花", "玛莎拉蒂",
        "摩根", "帕加尼", "迈巴赫", "世爵", "凯迪拉克", "沃尔沃", "红旗", "特斯拉", "悍马",
        "泰卡特", "菲斯科", "阿尔法·罗密欧", "KTM", "巴博斯", "光冈", "ALPINA", "极星",
        "捷尼赛思", "英力士"
    ],
    "合资品牌车企": [
        "北京现代", "起亚", "双龙", "福特", "克莱斯勒", "吉普", "道奇", "雪佛兰", "别克", "通用",
        "吉姆西", "赛麟", "松散", "标致", "雪铁龙", "大众", "菲亚特", "雷诺", "萨博", "斯柯达",
        "西雅特", "宝腾", "罗孚", "拉达", "瓦滋", "捷达", "莲花", "奔驰", "奥迪", "本田",
        "铃木", "马自达", "日产", "三菱", "丰田", "斯巴鲁", "五十铃", "宝马", "保时捷"
    ],
    "自主品牌车企": [
        "观致", "北京汽车", "绅宝", "威旺", "北汽福田", "比亚迪", "昌河", "长安汽车", "欧尚", "凯程",
        "长城汽车", "哈弗", "成功汽车", "东风风行", "启辰", "纳智捷", "东南汽车", "福迪", "启腾",
        "理念汽车", "传祺", "吉奥汽车", "哈飞汽车", "之诺", "金杯", "华泰", "黄海", "吉利汽车",
        "安驰", "江淮汽车", "瑞风", "陆风汽车", "卡威", "九龙汽车", "凯翼汽车", "康迪电动车",
        "力帆汽车", "猎豹汽车", "奇瑞汽车", "开瑞汽车", "青年莲花", "东风小康", "东风风光",
        "通家福", "名爵", "荣威", "上汽大通", "宝骏", "五菱", "腾势", "一汽轿车", "夏利",
        "英致", "金旅", "新凯", "野马汽车", "奔腾轿车", "一汽红旗", "东风风神", "永源汽车",
        "东风汽车", "知豆", "中兴汽车", "江南汽车", "众泰汽车", "东风风度", "江铃轻卡", "华骐",
        "华颂", "美亚车业", "御捷马", "东风商用车", "迈迪", "首望", "领志", "宝沃汽车",
        "欧联卡车", "汉腾汽车", "斯威汽车", "比速汽车", "裕路汽车", "魏牌", "埃安", "国金汽车",
        "东风御风", "领克", "君马", "云度新能源", "LITE", "电咖", "天越", "小鹏汽车", "祺智",
        "蔚来", "威马汽车", "全界", "捷途", "欧拉", "哪吒汽车", "思皓", "大乘汽车", "莱姆斯特",
        "开沃汽车", "前途汽车", "恒润汽车", "新特", "长江汽车", "广汽乘用车", "金康", "东风富康",
        "世锐", "领途", "国能", "道达", "奇点", "星途", "吉利几何", "零跑", "悦界", "速达",
        "天马", "大运", "雷丁", "智骏", "爱驰", "汉龙", "潍柴新能源", "赛力斯", "比德文",
        "东风纳米", "凌宝", "睿蓝", "合创", "朋克", "科莱威", "天际", "LEVC", "敏安", "创维",
        "华凯", "极狐", "飞凡", "坦克", "高合", "新日", "钇为", "广汽埃安", "国新", "羿驰",
        "岚图", "摩登", "重汽", "极氪", "瑞翔", "华梓", "问界", "电动屋", "博腾", "智己",
        "启源", "恒驰", "深蓝", "阿维塔", "蓝电", "东风氢舟", "银河", "江南", "未奥", "曹操出行",
        "昊铂", "猛士", "远航", "极石", "仰望", "极越", "方程豹", "iCAR", "智界", "小米汽车",
        "东风奕派", "颐驰", "享界", "212", "乐道", "予风", "灵悉", "智行盒子", "烨", "萤火虫",
        "吉祥", "尊界", "骏驰", "示界", "尚界", "埃尚"
    ],
    "造车新势力及其他": [
        "理想", "蔚来", "小鹏", "零跑", "小米", "问界", "极氪", "哪吒", "高合", "智己",
        "阿维塔", "岚图", "极狐"
    ]
}

# 排除关键字
exclude_keywords = ["交付", "召回", "营收", "销量榜", "什么", "推荐", "同比", "环比", "财报"]

# 采集新闻
url = "https://auto.gasgoo.com/automaker/C-109"
print(f"采集: {url}")

collector = GasgooCollector(url)
news = collector.collect(
    start_date=start_date,
    end_date=end_date,
    max_count=10,
    exclude_keywords=exclude_keywords,
    fetch_content=True
)

print(f"获取到 {len(news)} 条新闻")

# 按时间排序，取前10
news.sort(key=lambda x: x.get('date', ''), reverse=True)
news = news[:10]

print(f"\n前10条新闻:")
for i, n in enumerate(news, 1):
    print(f"{i}. [{n.get('date')}] {n.get('title')[:40]}...")

# 根据品牌分配到分领域
categorized = {
    "豪华品牌车企": [],
    "合资品牌车企": [],
    "自主品牌车企": [],
    "造车新势力及其他": []
}

for n in news:
    title = n.get('title', '')
    content = n.get('content', '')
    text = title + content
    
    assigned = False
    for category, brands in brand_categories.items():
        for brand in brands:
            if brand in text:
                categorized[category].append(n)
                assigned = True
                break
        if assigned:
            break
    
    if not assigned:
        # 未匹配到任何品牌，归入"造车新势力及其他"
        categorized["造车新势力及其他"].append(n)

print(f"\n分类结果:")
total = 0
for cat, items in categorized.items():
    print(f"  {cat}: {len(items)} 条")
    total += len(items)

print(f"  总计: {total} 条")
