"""
文件名: strong_stock_main.py
描述: 强势股首次回调战法 - 主程序
注意: 从config.py导入配置参数
"""

import pandas as pd
import numpy as np
import datetime
import warnings
import sys
import os
import re
import json
import time
from typing import List, Dict, Tuple, Optional, Any

# 导入配置文件
try:
    from config import StrategyConfig, MarketConfig, StockFilterConfig

    print("✅ 配置文件加载成功")
except ImportError as e:
    print(f"❌ 配置文件加载失败: {e}")
    sys.exit(1)

# 导入通达信TQ接口
try:
    from tqcenter import tq

    TQ_AVAILABLE = True
except ImportError as e:
    print(f"❌ 导入tqcenter模块失败: {e}")
    TQ_AVAILABLE = False
    sys.exit(1)

warnings.filterwarnings('ignore')


# ==================== 日志记录器 ====================
class Logger:
    """简单的日志记录器"""

    def __init__(self, level='INFO', log_to_file=True):
        self.level = level
        self.log_to_file = log_to_file
        self.levels = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3}

    def log(self, level, message):
        if self.levels[level] >= self.levels[self.level]:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_msg = f"[{timestamp}] [{level}] {message}"
            print(log_msg)

            if self.log_to_file and level in ['ERROR', 'WARNING']:
                with open('strategy_error.log', 'a', encoding='utf-8') as f:
                    f.write(log_msg + '\n')


logger = Logger(level='INFO', log_to_file=True)


# ==================== TQ接口封装函数 ====================
def tq_initialize():
    """初始化TQ连接"""
    try:
        tq.initialize(__file__)
        logger.log('INFO', "TQ接口初始化成功")
        return True
    except Exception as e:
        logger.log('ERROR', f"TQ接口初始化失败: {e}")
        return False


def standardize_stock_code(code: str) -> str:
    """标准化股票代码格式"""
    if not code or not isinstance(code, str):
        return ""

    code = code.strip()

    # 如果已经包含后缀，直接返回
    if '.' in code:
        return code

    # 提取数字部分
    match = re.search(r'(\d{6})', code)
    if match:
        num_code = match.group(1)
        # 根据代码前缀添加后缀
        if num_code.startswith(('600', '601', '603', '605', '688', '689', '900')):
            return f"{num_code}.SH"
        elif num_code.startswith(('000', '001', '002', '003', '300')):
            return f"{num_code}.SZ"
        elif num_code.startswith(('200', '080')):
            return f"{num_code}.SZ"
        elif num_code.startswith(('400', '420', '430', '830', '831', '832')):
            return f"{num_code}.BJ"
        else:
            return f"{num_code}.SH"

    return code


def tq_get_all_astocks() -> List[str]:
    """获取全市场A股列表"""
    all_stock_codes = []

    try:
        logger.log('INFO', "开始获取股票列表...")

        # 尝试多种获取方式
        list_types = [
            ('50', "沪深A股"),
            ('5', "所有A股"),
            ('0', "自选股")
        ]

        for list_type, description in list_types:
            try:
                stocks_result = tq.get_stock_list(list_type, list_type=1)

                if stocks_result and isinstance(stocks_result, list):
                    logger.log('INFO', f"从{description}获取到{len(stocks_result)}条数据")

                    for item in stocks_result:
                        if isinstance(item, dict):
                            # 尝试从字典中提取股票代码
                            for key in ['Code', 'code', 'symbol', '证券代码']:
                                if key in item:
                                    code = str(item[key]).strip()
                                    if code:
                                        standardized_code = standardize_stock_code(code)
                                        if standardized_code and standardized_code not in all_stock_codes:
                                            all_stock_codes.append(standardized_code)
                                        break
                        elif isinstance(item, str):
                            code = item.strip()
                            if code:
                                standardized_code = standardize_stock_code(code)
                                if standardized_code and standardized_code not in all_stock_codes:
                                    all_stock_codes.append(standardized_code)

            except Exception as e:
                logger.log('WARNING', f"获取{description}失败: {e}")
                continue

        # 过滤股票(根据配置)
        filtered_codes = filter_stocks(all_stock_codes)

        logger.log('INFO', f"获取到{len(all_stock_codes)}只股票，过滤后剩余{len(filtered_codes)}只")

        if filtered_codes:
            logger.log('DEBUG', f"示例股票: {filtered_codes[:5]}")

        return filtered_codes

    except Exception as e:
        logger.log('ERROR', f"获取股票列表失败: {e}")
        return []


def filter_stocks(stock_codes: List[str]) -> List[str]:
    """根据配置过滤股票"""
    if not StockFilterConfig.EXCLUDE_ST and not StockFilterConfig.EXCLUDE_NEW:
        return stock_codes

    filtered = []
    for code in stock_codes:
        # 过滤ST股票
        if StockFilterConfig.EXCLUDE_ST and ('ST' in code or '*ST' in code):
            continue

        # 这里可以添加更多过滤逻辑
        filtered.append(code)

    return filtered


def tq_get_kline_data(stock_code: str, count: int = StrategyConfig.HISTORY_DAYS) -> pd.DataFrame:
    """获取股票K线数据"""
    try:
        if not stock_code or '.' not in stock_code:
            return pd.DataFrame()

        df = tq.get_market_data(
            field_list=[],
            stock_list=[stock_code],
            start_time='',
            end_time=datetime.datetime.now().strftime('%Y%m%d'),
            count=count,
            dividend_type=StrategyConfig.DIVIDEND_TYPE,
            period=StrategyConfig.KLINE_PERIOD,
            fill_data=False
        )

        if df is None or df.empty:
            return pd.DataFrame()

        # 处理MultiIndex数据结构
        if isinstance(df.columns, pd.MultiIndex):
            if stock_code in df.columns.get_level_values(0):
                stock_df = df[stock_code].copy()
            else:
                return pd.DataFrame()
        else:
            stock_df = df.copy()

        # 标准化列名
        column_map = {}
        for col in stock_df.columns:
            col_str = str(col).lower()
            if 'open' in col_str or '开盘' in col:
                column_map[col] = 'open'
            elif 'high' in col_str or '最高' in col:
                column_map[col] = 'high'
            elif 'low' in col_str or '最低' in col:
                column_map[col] = 'low'
            elif 'close' in col_str or '收盘' in col:
                column_map[col] = 'close'
            elif 'volume' in col_str or '成交量' in col:
                column_map[col] = 'volume'
            elif 'time' in col_str or 'date' in col_str or '日期' in col:
                column_map[col] = 'date'

        stock_df.rename(columns=column_map, inplace=True)

        # 设置日期索引
        if 'date' in stock_df.columns:
            try:
                stock_df['date'] = pd.to_datetime(stock_df['date'], errors='coerce')
                stock_df.set_index('date', inplace=True)
            except:
                pass

        # 确保必要的列存在
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in stock_df.columns:
                return pd.DataFrame()
            stock_df[col] = pd.to_numeric(stock_df[col], errors='coerce')

        stock_df = stock_df.dropna(subset=required_cols)

        if len(stock_df) < 20:
            return pd.DataFrame()

        return stock_df.sort_index()

    except Exception as e:
        return pd.DataFrame()


def tq_get_hot_sectors() -> List[str]:
    """获取热点板块"""
    try:
        # 尝试自动获取热点板块
        all_sectors = tq.get_sector_list(list_type=1)

        if all_sectors and isinstance(all_sectors, list) and len(all_sectors) > 0:
            sectors_to_check = all_sectors[:50]  # 检查前50个板块

            sector_scores = []
            for sector in sectors_to_check:
                try:
                    if not isinstance(sector, str):
                        continue

                    sector_kline = tq_get_kline_data(sector, count=StrategyConfig.HOT_SECTOR_DAYS + 5)
                    if sector_kline.empty or len(sector_kline) < StrategyConfig.HOT_SECTOR_DAYS:
                        continue

                    # 计算板块涨幅
                    if len(sector_kline) >= StrategyConfig.HOT_SECTOR_DAYS:
                        start_price = sector_kline['close'].iloc[-StrategyConfig.HOT_SECTOR_DAYS]
                        end_price = sector_kline['close'].iloc[-1]
                        price_change = (end_price / start_price - 1) * 100
                    else:
                        price_change = 0

                    # 获取板块涨停家数(如果有)
                    try:
                        sector_info = tq.get_more_info(sector, field_list=['ZTGPNum'])
                        up_limit_count = 0
                        if sector_info is not None:
                            if isinstance(sector_info, pd.DataFrame) and 'ZTGPNum' in sector_info.columns:
                                up_limit_count = sector_info['ZTGPNum'].iloc[0]
                    except:
                        up_limit_count = 0

                    # 计算综合得分
                    score = price_change + up_limit_count * 5
                    sector_scores.append((sector, score, price_change))

                except:
                    continue

            # 按得分排序
            if sector_scores:
                sector_scores.sort(key=lambda x: x[1], reverse=True)
                hot_sectors = [s[0] for s in sector_scores[:StrategyConfig.HOT_SECTOR_COUNT]]

                logger.log('INFO', f"自动识别热点板块: {len(hot_sectors)}个")
                for i, (sector, score, change) in enumerate(sector_scores[:3]):
                    logger.log('INFO', f"  {i + 1}. {sector} - 涨幅{change:.1f}%，得分{score:.1f}")

                return hot_sectors

    except Exception as e:
        logger.log('WARNING', f"自动识别热点板块失败: {e}")

    # 使用预定义板块
    logger.log('INFO', f"使用预定义热点板块: {len(StrategyConfig.DEFAULT_HOT_SECTORS)}个")
    return StrategyConfig.DEFAULT_HOT_SECTORS


def tq_is_stock_in_sector(stock_code: str, sector_code: str) -> bool:
    """判断股票是否属于指定板块"""
    try:
        constituents = tq.get_stock_list_in_sector(sector_code)
        if constituents and isinstance(constituents, list):
            for item in constituents:
                if isinstance(item, str) and item == stock_code:
                    return True
                elif isinstance(item, dict):
                    for key in ['code', 'symbol', 'Code']:
                        if key in item and str(item[key]) == stock_code:
                            return True
        return False
    except:
        return False


# ==================== 技术指标计算 ====================
def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算技术指标"""
    df = df.copy()

    # 计算均线
    df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean()
    df['ma10'] = df['close'].rolling(window=10, min_periods=1).mean()
    df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean()

    # 计算涨跌幅
    df['pct_chg'] = df['close'].pct_change() * 100

    # 判断涨停
    df['is_up_limit'] = df['pct_chg'] >= 9.5

    # 计算波段涨幅
    lookback = StrategyConfig.BAND_DAYS
    if len(df) >= lookback:
        df['band_high'] = df['high'].rolling(window=lookback, min_periods=1).max()
        df['band_low'] = df['low'].rolling(window=lookback, min_periods=1).min().shift(lookback)
        df['band_rise_pct'] = (df['band_high'] - df['band_low']) / df['band_low'].replace(0, np.nan) * 100
    else:
        df['band_rise_pct'] = 0

    return df


# ==================== 策略条件判断 ====================
def check_strong_stock_condition(df: pd.DataFrame) -> Tuple[bool, str]:
    """条件1: 强势股判断"""
    if len(df) < StrategyConfig.UP_LIMIT_LOOKBACK_DAYS:
        return False, f"数据不足{StrategyConfig.UP_LIMIT_LOOKBACK_DAYS}天"

    recent_data = df.tail(StrategyConfig.UP_LIMIT_LOOKBACK_DAYS)
    consecutive_count = 0
    max_consecutive = 0

    for _, row in recent_data.iterrows():
        if row.get('is_up_limit', False):
            consecutive_count += 1
            max_consecutive = max(max_consecutive, consecutive_count)
        else:
            consecutive_count = 0

    if max_consecutive >= StrategyConfig.UP_LIMIT_CONSECUTIVE:
        return True, f"{max_consecutive}连板"

    latest_band_rise = df['band_rise_pct'].iloc[-1] if 'band_rise_pct' in df.columns else 0
    if not pd.isna(latest_band_rise) and latest_band_rise >= StrategyConfig.BAND_RISE_THRESHOLD:
        return True, f"波段涨幅{latest_band_rise:.1f}%"

    return False, "不满足强势股条件"


def check_mainstream_stock(stock_code: str, hot_sectors: List[str]) -> Tuple[bool, str, str]:
    """条件2: 主线人气股判断"""
    if not hot_sectors:
        return True, "无板块", "无热点板块数据"

    for sector in hot_sectors:
        if tq_is_stock_in_sector(stock_code, sector):
            return True, sector, f"属于热点板块[{sector}]"

    return False, "", "不属于当前热点板块"


def check_trend_condition(df: pd.DataFrame) -> Tuple[bool, str]:
    """条件3: 趋势判断"""
    if len(df) < StrategyConfig.MA_TREND_DAYS + StrategyConfig.MA_TREND_UP_DAYS:
        return False, f"数据不足{StrategyConfig.MA_TREND_DAYS + StrategyConfig.MA_TREND_UP_DAYS}天"

    latest = df.iloc[-1]

    # 股价在20日线上方
    if latest['close'] <= latest['ma20']:
        return False, f"股价{latest['close']:.2f}未站上20日线{latest['ma20']:.2f}"

    # 20日线趋势向上
    if len(df) >= StrategyConfig.MA_TREND_DAYS + StrategyConfig.MA_TREND_UP_DAYS:
        current_ma20 = df['ma20'].iloc[-1]
        past_ma20 = df['ma20'].iloc[-1 - StrategyConfig.MA_TREND_UP_DAYS]

        if current_ma20 <= past_ma20:
            return False, "20日线走平或向下"

    return True, "趋势向上，股价在20日线上方"


def check_first_pullback_entry(df: pd.DataFrame) -> Tuple[bool, Dict, str]:
    """条件4: 回调买点判断"""
    n = len(df)
    if n < 30:
        return False, {}, f"数据不足30天"

    cfg = StrategyConfig

    # 寻找最近高点
    lookback = 20
    start_idx = max(0, n - lookback)
    recent_high = df['close'].iloc[start_idx:].max()
    recent_high_idx = df['close'].iloc[start_idx:].idxmax()
    recent_high_pos = df.index.get_loc(recent_high_idx)

    current_pos = n - 1
    if current_pos <= recent_high_pos:
        return False, {}, "非回调状态"

    # 计算回调天数
    pullback_days = current_pos - recent_high_pos
    if not (cfg.PULLBACK_DAYS_MIN <= pullback_days <= cfg.PULLBACK_DAYS_MAX):
        return False, {}, f"回调{pullback_days}天不符合要求({cfg.PULLBACK_DAYS_MIN}-{cfg.PULLBACK_DAYS_MAX}天)"

    # 检查缩量
    up_start = max(0, recent_high_pos - 3)
    up_volume_avg = df['volume'].iloc[up_start:recent_high_pos + 1].mean()
    pullback_volume_avg = df['volume'].iloc[recent_high_pos + 1:current_pos + 1].mean()

    if up_volume_avg > 0:
        volume_shrink_pct = (1 - pullback_volume_avg / up_volume_avg) * 100
    else:
        volume_shrink_pct = 0

    if volume_shrink_pct < cfg.VOLUME_SHRINK_PCT:
        return False, {}, f"缩量不足{volume_shrink_pct:.1f}% < {cfg.VOLUME_SHRINK_PCT}%"

    # 检查企稳K线
    last_bar = df.iloc[current_pos]
    o, h, l, c = last_bar['open'], last_bar['high'], last_bar['low'], last_bar['close']

    body_size = abs(c - o)
    total_range = h - l if (h - l) > 0 else 0.001
    lower_shadow = min(o, c) - l

    is_doji = body_size / total_range <= cfg.DOJI_BODY_RATIO
    is_small_up = (c > o) and ((c - o) / o * 100 <= cfg.SMALL_UP_PCT)
    is_long_lower_shadow = (lower_shadow > 0) and (lower_shadow / max(body_size, 0.01) >= cfg.LONG_LOWER_SHADOW_RATIO)

    if not (is_doji or is_small_up or is_long_lower_shadow):
        return False, {}, "无企稳K线(十字星/小阳线/长下影)"

    # 检查支撑
    support_lines = []
    for ma_name, ma_value in [('MA5', last_bar['ma5']),
                              ('MA10', last_bar['ma10']),
                              ('MA20', last_bar['ma20'])]:
        if ma_value > 0:
            distance_pct = abs(c - ma_value) / ma_value * 100
            if distance_pct <= cfg.SUPPORT_TOLERANCE_PCT:
                support_lines.append(ma_name)

    if not support_lines:
        return False, {}, f"未在关键均线获得支撑(收盘价{c:.2f})"

    # 收集信息
    detail_info = {
        'pullback_days': pullback_days,
        'recent_high': recent_high,
        'recent_high_date': str(recent_high_idx),
        'current_price': c,
        'volume_shrink_pct': volume_shrink_pct,
        'support_lines': ','.join(support_lines),
        'kline_pattern': '十字星' if is_doji else ('小阳线' if is_small_up else '长下影'),
        'buy_signal': '尾盘企稳或次日早盘低开不跌'
    }

    reason = f"回调{pullback_days}天，缩量{volume_shrink_pct:.1f}%，{detail_info['kline_pattern']}，支撑{detail_info['support_lines']}"

    return True, detail_info, reason


# ==================== 仓位计算 ====================
def calculate_position_size(selected_count: int, market_condition: str = "normal") -> Dict:
    """计算仓位配置"""
    cfg = StrategyConfig

    if market_condition == "weak":
        # 大盘弱时
        total_position = cfg.WEAK_MARKET_POSITION_PCT
        max_stocks = 1
    else:
        # 正常或强势时
        total_position = min(selected_count * cfg.SINGLE_POSITION_PCT, cfg.TOTAL_POSITION_MAX_PCT)
        max_stocks = min(selected_count, cfg.TOTAL_POSITION_MAX_PCT // cfg.SINGLE_POSITION_PCT)

    position_per_stock = cfg.SINGLE_POSITION_PCT if selected_count > 0 else 0

    return {
        'total_position_pct': total_position,
        'position_per_stock_pct': position_per_stock,
        'max_stocks': max_stocks,
        'market_condition': market_condition
    }


# ==================== 主选股流程 ====================
def main_strategy():
    """主选股流程"""
    print("=" * 100)
    print("【顶级游资 - 强势股首次回调完整战法】")
    print(f"版本: 2.0 (配置文件版) | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

    # 显示当前配置
    print(f"📋 当前配置参数:")
    print(f"  强势股条件: {StrategyConfig.UP_LIMIT_CONSECUTIVE}连板 或 {StrategyConfig.BAND_RISE_THRESHOLD}%波段涨幅")
    print(f"  回调天数: {StrategyConfig.PULLBACK_DAYS_MIN}-{StrategyConfig.PULLBACK_DAYS_MAX}天")
    print(f"  缩量要求: ≥{StrategyConfig.VOLUME_SHRINK_PCT}%")
    print(f"  扫描数量: ≤{StrategyConfig.MAX_SCAN_STOCKS}只")
    print()

    if not TQ_AVAILABLE:
        logger.log('ERROR', "tqcenter模块不可用")
        return []

    # 1. 初始化TQ连接
    logger.log('INFO', "初始化TQ接口...")
    if not tq_initialize():
        return []

    # 2. 获取市场数据
    logger.log('INFO', "获取市场数据...")

    # 获取股票列表
    all_stocks = tq_get_all_astocks()
    if not all_stocks:
        logger.log('ERROR', "未获取到股票列表，程序终止")
        tq.close()
        return []

    # 获取热点板块
    hot_sectors = tq_get_hot_sectors()

    # 3. 开始选股扫描
    logger.log('INFO', f"开始扫描股票，共{len(all_stocks)}只...")

    selected_stocks = []
    scan_count = 0
    start_time = datetime.datetime.now()

    max_scan = min(StrategyConfig.MAX_SCAN_STOCKS, len(all_stocks))
    scan_stocks = all_stocks[:max_scan]

    for i, stock_code in enumerate(scan_stocks):
        try:
            scan_count += 1

            # 进度提示
            if scan_count % StrategyConfig.SCAN_BATCH_SIZE == 0:
                elapsed = (datetime.datetime.now() - start_time).seconds
                progress = (scan_count / max_scan) * 100
                logger.log('INFO', f"进度: {scan_count}/{max_scan} ({progress:.1f}%)，耗时: {elapsed}秒")

            # 获取K线数据
            kline_df = tq_get_kline_data(stock_code, count=StrategyConfig.HISTORY_DAYS)
            if kline_df.empty or len(kline_df) < 30:
                continue

            # 计算技术指标
            kline_df = calculate_technical_indicators(kline_df)

            # 条件1: 强势股判断
            is_strong, reason1 = check_strong_stock_condition(kline_df)
            if not is_strong:
                continue

            # 条件2: 主线人气股判断
            is_mainstream, hot_sector, reason2 = check_mainstream_stock(stock_code, hot_sectors)

            # 条件3: 趋势判断
            trend_ok, reason3 = check_trend_condition(kline_df)
            if not trend_ok:
                continue

            # 条件4: 回调买点判断
            pullback_ok, detail, reason4 = check_first_pullback_entry(kline_df)
            if not pullback_ok:
                continue

            # 所有条件满足
            stock_result = {
                '股票代码': stock_code,
                '热点板块': hot_sector,
                '强势原因': reason1,
                '主线原因': reason2,
                '趋势原因': reason3,
                '买点原因': reason4,
                '详情': detail,
                '扫描时间': datetime.datetime.now().strftime("%H:%M:%S")
            }

            selected_stocks.append(stock_result)
            logger.log('INFO', f"发现目标 [{len(selected_stocks)}]: {stock_code}")

        except Exception as e:
            if StrategyConfig.ENABLE_DEBUG:
                logger.log('DEBUG', f"处理{stock_code}失败: {e}")
            continue

    # 4. 输出选股结果
    elapsed_total = (datetime.datetime.now() - start_time).seconds

    print("\n" + "=" * 100)
    print("📊 选股结果报告")
    print("=" * 100)

    print(f"扫描统计: 共扫描 {scan_count} 只股票，耗时 {elapsed_total} 秒")
    print(f"选中数量: {len(selected_stocks)} 只股票符合全部条件")

    if selected_stocks:
        print(f"\n🎯 符合【强势股首次回调】战法的股票:")
        print("-" * 100)

        for i, stock in enumerate(selected_stocks, 1):
            detail = stock['详情']

            print(f"\n{i}. 【{stock['股票代码']}】")
            if stock['热点板块'] and stock['热点板块'] != "无板块":
                print(f"   板块: {stock['热点板块']}")
            print(f"   强势: {stock['强势原因']}")
            print(f"   买点: {stock['买点原因']}")
            print(f"   数据: 前高{detail.get('recent_high', 0):.2f}, "
                  f"现价{detail.get('current_price', 0):.2f}, "
                  f"回调{detail.get('pullback_days', 0)}天, "
                  f"缩量{detail.get('volume_shrink_pct', 0):.1f}%")
            print(f"   形态: {detail.get('kline_pattern', '')}, "
                  f"支撑: {detail.get('support_lines', '')}")
            print(f"   买点: {detail.get('buy_signal', '尾盘或次日早盘')}")
            print(f"   仓位: 建议{StrategyConfig.SINGLE_POSITION_PCT}%")
            print("   " + "─" * 60)

        # 计算仓位配置
        position_info = calculate_position_size(len(selected_stocks))

        print(f"\n💡 策略执行总结:")
        print(f"   1. 符合条件: {len(selected_stocks)} 只")
        print(f"   2. 建议总仓: {position_info['total_position_pct']}%")
        print(f"   3. 单只仓位: {position_info['position_per_stock_pct']}%")
        print(f"   4. 止损纪律: 亏损-{StrategyConfig.STOP_LOSS_PCT}%无条件止损")
        print(f"   5. 止盈策略: 反弹至前高/1-3天不新高/放量滞涨")

        print(f"\n📈 核心口诀:")
        print("   只做强势首次调，缩量企稳才下手。")
        print("   线上持股破线走，止损五个必须守。")
        print("   不追高、不抄底，只做反弹最安逸。")

        # 保存结果
        if StrategyConfig.SAVE_RESULTS:
            save_results(selected_stocks, position_info)

    else:
        print(f"\n⚠️  今日未筛选出符合条件的股票。")
        print(f"💡 投资建议: 空仓等待，耐心等待下次机会")

    # 5. 断开连接
    print(f"\n步骤4: 清理资源...")
    tq.close()
    print("✅ TQ连接已关闭")
    print("=" * 100)
    print("🎉 选股程序执行完成!")

    return selected_stocks


def save_results(selected_stocks: List[Dict], position_info: Dict):
    """保存选股结果到文件"""
    try:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"选股结果_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("顶级游资-强势股首次回调战法选股结果\n")
            f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"选中股票: {len(selected_stocks)} 只\n")
            f.write(f"建议总仓: {position_info['total_position_pct']}%\n")
            f.write(f"单只仓位: {position_info['position_per_stock_pct']}%\n")
            f.write("=" * 60 + "\n\n")

            f.write("【策略参数】\n")
            f.write(
                f"强势股: {StrategyConfig.UP_LIMIT_CONSECUTIVE}连板 或 {StrategyConfig.BAND_RISE_THRESHOLD}%波段涨幅\n")
            f.write(f"回调天数: {StrategyConfig.PULLBACK_DAYS_MIN}-{StrategyConfig.PULLBACK_DAYS_MAX}天\n")
            f.write(f"缩量要求: ≥{StrategyConfig.VOLUME_SHRINK_PCT}%\n")
            f.write(f"止损: -{StrategyConfig.STOP_LOSS_PCT}%\n\n")

            f.write("【选股列表】\n")
            for stock in selected_stocks:
                detail = stock['详情']
                f.write(f"\n股票代码: {stock['股票代码']}\n")
                f.write(f"热点板块: {stock['热点板块']}\n")
                f.write(f"强势原因: {stock['强势原因']}\n")
                f.write(f"买点原因: {stock['买点原因']}\n")
                f.write(f"前高位置: {detail.get('recent_high', 0):.2f}\n")
                f.write(f"当前价格: {detail.get('current_price', 0):.2f}\n")
                f.write(f"回调天数: {detail.get('pullback_days', 0)}\n")
                f.write(f"缩量比例: {detail.get('volume_shrink_pct', 0):.1f}%\n")
                f.write(f"支撑均线: {detail.get('support_lines', '')}\n")
                f.write(f"K线形态: {detail.get('kline_pattern', '')}\n")
                f.write(f"买点时机: {detail.get('buy_signal', '尾盘或次日早盘')}\n")
                f.write(f"建议仓位: {StrategyConfig.SINGLE_POSITION_PCT}%\n")
                f.write(f"止损位置: -{StrategyConfig.STOP_LOSS_PCT}% 或 跌破{StrategyConfig.STOP_LOSS_MA}日线\n")
                f.write("-" * 40 + "\n")

            f.write("\n【核心口诀】\n")
            f.write("只做强势首次调，缩量企稳才下手。\n")
            f.write("线上持股破线走，止损五个必须守。\n")
            f.write("不追高、不抄底，只做反弹最安逸。\n")

        print(f"📁 详细结果已保存到: {filename}")

    except Exception as e:
        print(f"⚠️  保存结果失败: {e}")


# ==================== 程序入口 ====================
if __name__ == "__main__":
    try:
        import pandas as pd
        import numpy as np
    except ImportError as e:
        print(f"❌ 缺少必要的Python库: {e}")
        print("💡 请运行: pip install pandas numpy")
        sys.exit(1)

    try:
        print("🚀 启动选股程序...")
        print(f"配置文件: config.py")
        print(f"开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        results = main_strategy()

        if results:
            print(f"\n✅ 选股完成，共找到 {len(results)} 只符合条件股票")
        else:
            print(f"\nℹ️  选股完成，未找到符合条件的股票")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
        try:
            tq.close()
        except:
            pass
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback

        traceback.print_exc()
        try:
            tq.close()
        except:
            pass