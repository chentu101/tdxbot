"""
文件名: config.py
描述: 强势股首次回调战法 - 配置文件
说明: 所有策略参数在此集中配置，方便调整优化
"""


class StrategyConfig:
    """策略参数配置类"""

    # ========== 一、选股条件 ==========

    # 1. 强势股条件
    UP_LIMIT_LOOKBACK_DAYS = 10  # 10日内寻找涨停板
    UP_LIMIT_CONSECUTIVE = 2  # 2连板及以上
    BAND_RISE_THRESHOLD = 30.0  # 波段涨幅 ≥30%
    BAND_DAYS = 20  # 波段计算周期(20日)

    # 2. 主线人气股条件
    HOT_SECTOR_COUNT = 5  # 取前N个热点板块
    HOT_SECTOR_DAYS = 5  # 板块热度计算周期(5日)

    # 3. 趋势线条件
    MA_TREND_DAYS = 20  # 20日线作为趋势线
    MA_TREND_UP_DAYS = 5  # 判断均线向上所比较的天数差

    # ========== 二、入场条件 ==========

    # 1. 回调天数范围
    PULLBACK_DAYS_MIN = 2  # 最小回调天数(2天)
    PULLBACK_DAYS_MAX = 5  # 最大回调天数(5天)

    # 2. 缩量条件
    VOLUME_SHRINK_PCT = 30.0  # 量能比上涨时缩小30%以上

    # 3. 企稳信号参数
    DOJI_BODY_RATIO = 0.1  # 十字星实体占振幅比例(≤10%)
    SMALL_UP_PCT = 2.0  # 小阳线最大涨幅(≤2%)
    LONG_LOWER_SHADOW_RATIO = 2.0  # 长下影线长度与实体比例(≥2倍)

    # 4. 支撑位容差
    SUPPORT_TOLERANCE_PCT = 2.0  # 回踩均线容差百分比(±2%)

    # ========== 三、仓位管理 ==========

    # 仓位配置
    SINGLE_POSITION_PCT = 20  # 单只票仓位(20% = 2成)
    TOTAL_POSITION_MAX_PCT = 50  # 总仓位上限(50% = 5成)
    WEAK_MARKET_POSITION_PCT = 10  # 大盘弱时仓位(10% = 1成)

    # ========== 四、止损条件 ==========

    STOP_LOSS_PCT = 5.0  # 亏损-5%无条件止损
    STOP_LOSS_MA = 10  # 有效跌破10日线直接走

    # ========== 五、止盈条件 ==========

    # 止盈策略参数
    PROFIT_TAKING_DAYS = 3  # 反弹1-3天不创新高则止盈
    VOLUME_STAGNATION_RATIO = 1.5  # 放量滞涨阈值(量能放大1.5倍但涨幅小)

    # ========== 六、数据配置 ==========

    KLINE_PERIOD = '1d'  # K线周期: 1d=日线, 5m=5分钟, 15m=15分钟
    DIVIDEND_TYPE = 'front'  # 复权类型: front=前复权, back=后复权, none=不复权
    HISTORY_DAYS = 60  # 获取历史数据天数(最少20天，建议60-120)

    # ========== 七、扫描配置 ==========

    MAX_SCAN_STOCKS = 500  # 最大扫描股票数量(测试时可减少，实盘可增加)
    SCAN_BATCH_SIZE = 50  # 每批处理的股票数量(用于进度显示)
    ENABLE_DEBUG = False  # 是否启用调试模式
    SAVE_RESULTS = True  # 是否保存选股结果到文件

    # ========== 八、TQ接口配置 ==========

    TQ_CONNECT_TIMEOUT = 30  # TQ连接超时时间(秒)
    TQ_RETRY_TIMES = 3  # 失败重试次数
    AUTO_REFRESH_DATA = True  # 是否自动刷新数据缓存

    # ========== 九、板块配置 ==========

    # 预定义热点板块(当无法自动识别时使用)
    DEFAULT_HOT_SECTORS = [
        '880001.SH',  # 行业板块
        '880002.SH',  # 概念板块
        '880003.SH',  # 地域板块
        '880005.SH',  # 风格板块
    ]

    # 重点关注的板块代码(用于快速筛选)
    FOCUS_SECTORS = [
        '880506.SH',  # 锂电池
        '880534.SH',  # 新能源汽车
        '880952.SH',  # 人工智能
        '880985.SH',  # 芯片
        '880330.SH',  # 医药
    ]


class MarketConfig:
    """市场参数配置类"""

    # 交易时间配置
    TRADE_DAYS_PER_YEAR = 240  # 年交易天数
    TRADE_HOURS_PER_DAY = 4  # 日交易小时数

    # 大盘状态判断参数
    MARKET_WEAK_THRESHOLD = -2.0  # 大盘弱势阈值(指数跌幅≥2%)
    MARKET_STRONG_THRESHOLD = 1.0  # 大盘强势阈值(指数涨幅≥1%)

    # 成交量基准
    VOLUME_BASELINE_DAYS = 20  # 成交量基准计算周期


class StockFilterConfig:
    """股票筛选配置类"""

    # 股票池过滤条件
    MIN_PRICE = 3.0  # 最低股价(元)
    MAX_PRICE = 500.0  # 最高股价(元)
    MIN_VOLUME = 1000000  # 最低成交量(手)
    MIN_MARKET_CAP = 20.0  # 最低市值(亿元)

    # 排除的股票类型
    EXCLUDE_ST = True  # 是否排除ST股票
    EXCLUDE_SUSPENDED = True  # 是否排除停牌股票
    EXCLUDE_NEW = True  # 是否排除新股(上市<60天)


class PerformanceConfig:
    """性能优化配置类"""

    # 并行处理配置
    USE_PARALLEL = False  # 是否使用并行处理(多线程/多进程)
    MAX_WORKERS = 4  # 最大工作线程数

    # 缓存配置
    ENABLE_CACHE = True  # 是否启用数据缓存
    CACHE_EXPIRE_HOURS = 6  # 缓存过期时间(小时)

    # 日志配置
    LOG_LEVEL = 'INFO'  # 日志级别: DEBUG, INFO, WARNING, ERROR
    LOG_TO_FILE = True  # 是否记录日志到文件


# ========== 参数说明 ==========
"""
【使用说明】
1. 调整策略参数后，无需修改主程序代码
2. 参数分类说明：
   - 选股条件：控制强势股、主线、趋势的判断标准
   - 入场条件：控制回调买点的具体条件
   - 仓位管理：控制仓位分配和风险控制
   - 止损止盈：控制退出条件
   - 数据配置：控制数据获取方式
   - 扫描配置：控制程序运行参数
   - 板块配置：定义热点板块
   - 市场参数：控制大盘状态判断
   - 筛选配置：控制股票池过滤
   - 性能配置：控制程序运行效率

【调参建议】
1. 初级阶段：先调整BAND_RISE_THRESHOLD(30→20)、VOLUME_SHRINK_PCT(30→20)降低选股要求
2. 中级阶段：调整PULLBACK_DAYS_MIN(2→1)、PULLBACK_DAYS_MAX(5→7)扩大回调范围
3. 高级阶段：结合大盘状态动态调整仓位和止损参数

【注意事项】
1. 修改参数后建议先用小规模股票池测试
2. 实盘前需充分回测验证参数有效性
3. 不同市场环境(牛市/熊市)可能需要不同的参数设置
"""