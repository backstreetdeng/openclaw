"""
配置模块 - 定义8大领域、URL、关键字过滤规则
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# ========== 8大领域配置 ==========
DOMAINS = {
    "行业动态": {
        "id": "industry",
        "urls": [
            "https://auto.gasgoo.com/auto-news/C-103",   # 行业
            "https://auto.gasgoo.com/auto-news/C-106",   # 车企
            "https://auto.gasgoo.com/auto-news/C-107",   # 供应链
            "https://auto.gasgoo.com/auto-news/C-108",   # 智能网联
            "https://auto.gasgoo.com/auto-news/C-109",   # 新能源
            "https://auto.gasgoo.com/auto-news/C-110",   # 新技术
            "https://auto.gasgoo.com/auto-news/C-303",   # 销量
            "https://auto.gasgoo.com/auto-news/C-409",   # 高端访谈
            "https://auto.gasgoo.com/auto-news/C-501",   # 内参
            "https://auto.gasgoo.com/auto-news/C-601",   # 上市公司
        ],
        "include_keywords": ["税", "电池", "锂矿", "原材料", "油"],  # 必须包含的关键字
        "exclude_keywords": [],      # 排除关键字（空=无要求）
        "max_count": 10,
    },
    "企业要闻": {
        "id": "enterprise",
        "urls": [
            "https://auto.gasgoo.com/automaker/C-109",
        ],
        "include_keywords": [],
        "exclude_keywords": ["交付", "召回", "营收", "销量榜", "什么", "推荐", "同比", "环比", "财报"],
        "max_count": 10,
        "brand_categories": ["豪华品牌车企", "合资品牌车企", "自主品牌车企", "造车新势力及其他"],
        # 品牌分类明细
        "brands": {
            "豪华品牌车企": ["阿斯顿·马丁", "奥迪", "宝马", "迷你", "DS", "保时捷", "奔驰", "讴歌", "宾利", "斯玛特", "英菲尼迪", "法拉利", "雷克萨斯", "林肯", "捷豹", "劳斯莱斯", "路虎", "莲花", "玛莎拉蒂", "摩根", "帕加尼", "迈巴赫", "世爵", "凯迪拉克", "沃尔沃", "红旗", "特斯拉", "悍马", "泰卡特", "菲斯科", "阿尔法·罗密欧", "KTM", "巴博斯", "光冈", "ALPINA", "极星", "捷尼赛思", "英力士", "AUDI"],
            "合资品牌车企": ["北京现代", "起亚", "双龙", "福特", "克莱斯勒", "吉普", "道奇", "雪佛兰", "别克", "通用", "吉姆西", "赛麟", "松散", "标致", "雪铁龙", "大众", "菲亚特", "雷诺", "萨博", "斯柯达", "西雅特", "宝腾", "罗孚", "拉达", "瓦滋", "捷达", "莲花", "奔驰", "奥迪", "本田", "铃木", "马自达", "日产", "三菱", "丰田", "斯巴鲁", "五十铃", "宝马", "保时捷"],
            "自主品牌车企": ["观致", "北京汽车", "绅宝", "威旺", "北汽福田", "比亚迪", "昌河", "长安汽车", "欧尚", "凯程", "长城汽车", "哈弗", "成功汽车", "东风风行", "启辰", "纳智捷", "东南汽车", "福迪", "启腾", "理念汽车", "传祺", "吉奥汽车", "哈飞汽车", "之诺", "金杯", "华泰", "黄海", "吉利汽车", "安驰", "江淮汽车", "瑞风", "陆风汽车", "卡威", "九龙汽车", "凯翼汽车", "康迪电动车", "力帆汽车", "猎豹汽车", "奇瑞汽车", "开瑞汽车", "青年莲花", "东风小康", "东风风光", "通家福", "名爵", "荣威", "上汽大通", "宝骏", "五菱", "腾势", "一汽轿车", "夏利", "英致", "金旅", "新凯", "野马汽车", "奔腾轿车", "一汽红旗", "东风风神", "永源汽车", "东风汽车", "知豆", "中兴汽车", "江南汽车", "众泰汽车", "东风风度", "江铃轻卡", "华骐", "华颂", "美亚车业", "御捷马", "东风商用车", "迈迪", "首望", "领志", "宝沃汽车", "欧联卡车", "汉腾汽车", "斯威汽车", "比速汽车", "裕路汽车", "魏牌", "埃安", "国金汽车", "东风御风", "领克", "君马", "云度新能源", "LITE", "电咖", "天越", "小鹏汽车", "祺智", "蔚来", "威马汽车", "全界", "捷途", "欧拉", "哪吒汽车", "思皓", "大乘汽车", "莱姆斯特", "开沃汽车", "前途汽车", "恒润汽车", "新特", "长江汽车", "广汽乘用车", "金康", "东风富康", "世锐", "领途", "国能", "道达", "奇点", "星途", "吉利几何", "零跑", "悦界", "速达", "天马", "大运", "雷丁", "智骏", "爱驰", "汉龙", "潍柴新能源", "赛力斯", "比德文", "东风纳米", "凌宝", "睿蓝", "合创", "朋克", "科莱威", "天际", "LEVC", "敏安", "创维", "华凯", "极狐", "飞凡", "坦克", "高合", "新日", "钇为", "广汽埃安", "国新", "羿驰", "岚图", "摩登", "重汽", "极氪", "瑞翔", "华梓", "问界", "电动屋", "博腾", "智己", "启源", "恒驰", "深蓝", "阿维塔", "蓝电", "东风氢舟", "银河", "江南", "未奥", "曹操出行", "昊铂", "猛士", "远航", "极石", "仰望", "极越", "方程豹", "iCAR", "智界", "小米汽车", "东风奕派", "颐驰", "享界", "212", "乐道", "予风", "灵悉", "智行盒子", "烨", "萤火虫", "吉祥", "尊界", "骏驰", "示界", "尚界", "埃尚"],
            "造车新势力及其他": ["理想", "蔚来", "小鹏", "零跑", "小米", "问界", "极氪", "哪吒", "高合", "智己", "阿维塔", "岚图", "极狐"]
        }
    },
    "高层动态": {
        "id": "executive",
        "urls": [
            "https://auto.gasgoo.com/interview/C-303",
        ],
        "include_keywords": [],
        "exclude_keywords": [],
        "max_count": 10,
    },
    "零部件": {
        "id": "parts",
        "urls": [
            "https://auto.gasgoo.com/parts-news/C-103",
        ],
        "include_keywords": [],
        "exclude_keywords": [],
        "max_count": 10,
    },
    "新技术/新趋势": {
        "id": "tech",
        "sub_domains": {
            "新能源技术": {
                "url": "https://auto.gasgoo.com/nev/C-501",
                "max_count": 5,
            },
            "智能网联技术": {
                "url": "https://auto.gasgoo.com/smart-connected/C-601",
                "max_count": 5,
            },
            "其他关键技术": {
                "url": "https://auto.gasgoo.com/new-tech/C-409",
                "max_count": 5,
            },
        },
    },
    "新车上市": {
        "id": "newcar",
        "urls": [
            "https://auto.gasgoo.com/new-cars/C-107",   # 盖世汽车（6.1）
            # 太平洋汽车（6.2）不在这里，在gui.py单独用PcautoCollector处理
        ],
        "include_keywords": ["上市", "预售"],  # 盖世汽车用
        "exclude_keywords": [],
        "max_count": 10,
    },
    "宏观经济政策": {
        "id": "macro",
        "urls": [
            "https://www.gov.cn/yaowen/liebiao/",     # 要闻
            "https://www.gov.cn/zhengce/zuixin/",     # 政策
            "https://finance.eastmoney.com/a/cgnjj.html",  # 国内经济
            "https://finance.eastmoney.com/a/cgjjj.html",  # 国际经济
        ],
        "sub_domains": {
            "要闻": {
                "url": "https://www.gov.cn/yaowen/liebiao/",
                "include_keywords": ["国务院常务会", "国务院常务会议", "政治局会议"],
                "max_count": 3,
            },
            "政策": {
                "url": "https://www.gov.cn/zhengce/zuixin/",
                "include_keywords": ["消费", "投资", "外贸", "出口", "进口", "民生", "就业", "大市场"],
                "max_count": 3,
            },
            "国内经济": {
                "url": "https://finance.eastmoney.com/a/cgnjj.html",
                "include_keywords": ["部"],
                "max_count": 3,
            },
            "国际经济": {
                "url": "https://finance.eastmoney.com/a/cgjjj.html",
                "include_keywords": ["美联储"],
                "max_count": 3,
            },
        },
    },
    "政策法规": {
        "id": "policy",
        "urls": [
            "https://www.autoinfo.org.cn/#/policy/dynamic/index",
        ],
        "include_keywords": ["消费", "促销费", "以旧换新", "补贴", "购车", "购车补贴", "补贴细则"],
        "exclude_keywords": [],
        "max_count": 10,
        "require_national_tag": True,  # 必须带红色"国家"标签
        "api_url": "https://www.autoinfo.org.cn/prod-api/api/policy/ttPolicy/newPolicy",
    },
}

# ========== 时间范围选项 ==========
# 注意："近一周"已改为固定周六→周五周期，不在使用delta天数
TIME_RANGE_OPTIONS = {
    "近一周（周六→周五）": "week",   # 上周六 → 本周五
    "近两周": "two_weeks",            # 上上周六 → 本周五
    "近一个月": "month",              # 上月初 → 本周五
    "自定义": "custom",               # 用户自定义天数
}

# ========== 默认配置 ==========
DEFAULT_OUTPUT_DIR = "E:\\openclaw\\workspace\\auto_news_collector\\output"
DEFAULT_CACHE_DIR = "E:\\openclaw\\workspace\\auto_news_collector\\data\\cache"

# ========== Word文档样式 ==========
DOC_STYLE = {
    "title_font": "微软雅黑",
    "title_size": 16,
    "heading_font": "微软雅黑",
    "heading_size": 14,
    "body_font": "微软雅黑",
    "body_size": 11,
    "line_spacing": 1.5,
}
