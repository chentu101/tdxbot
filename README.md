# tdxbot
用Python编的利用通达信TQ接口选强势股的选股程序

# 强势股首次回调战法 - 参数配置说明

## 文件结构

strong_stock_main.py    # 主程序

config.py              # 配置文件

run_strategy.bat       # Windows启动脚本

run_strategy.sh        # Linux/Mac启动脚本

README.md             # 说明文档

## 快速开始

### Windows用户
1. 双击运行 `run_strategy.bat`
2. 或命令行运行: `python strong_stock_main.py`

### Linux/Mac用户
1. 给脚本执行权限: `chmod +x run_strategy.sh`
2. 运行: `./run_strategy.sh`
3. 或直接运行: `python3 strong_stock_main.py`

## 参数配置指南

### 1. 选股条件调整
在 `config.py` 的 `StrategyConfig` 类中修改：
## 快速开始

### Windows用户
1. 双击运行 `run_strategy.bat`
2. 或命令行运行: `python strong_stock_main.py`

### Linux/Mac用户
1. 给脚本执行权限: `chmod +x run_strategy.sh`
2. 运行: `./run_strategy.sh`
3. 或直接运行: `python3 strong_stock_main.py`

## 参数配置指南

### 1. 选股条件调整
在 `config.py` 的 `StrategyConfig` 类中修改：

调整强势股条件

UP_LIMIT_CONSECUTIVE = 2      # 连板要求(默认2)

BAND_RISE_THRESHOLD = 30.0    # 波段涨幅(默认30%)

调整回调天数

PULLBACK_DAYS_MIN = 2         # 最小回调天数(默认2)

PULLBACK_DAYS_MAX = 5         # 最大回调天数(默认5)

调整缩量要求

VOLUME_SHRINK_PCT = 30.0      # 缩量比例(默认30%)

### 2. 仓位管理调整

python

单只股票仓位

SINGLE_POSITION_PCT = 20      # 20% = 2成仓

总仓位限制

TOTAL_POSITION_MAX_PCT = 50   # 50% = 5成仓

弱势市场仓位

WEAK_MARKET_POSITION_PCT = 10 # 10% = 1成仓
### 3. 止损止盈调整

python

止损条件

STOP_LOSS_PCT = 5.0           # 亏损5%止损

STOP_LOSS_MA = 10             # 跌破10日线止损

止盈条件

PROFIT_TAKING_DAYS = 3        # 反弹3天不新高止盈

复制
### 4. 数据配置调整

python

K线周期

KLINE_PERIOD = '1d'           # 日线，可选: '5m', '15m', '30m', '60m'

复权类型

DIVIDEND_TYPE = 'front'       # 前复权，可选: 'back', 'none'

历史数据天数

HISTORY_DAYS = 60             # 获取60天数据

复制
### 5. 扫描配置调整

python

扫描数量控制

MAX_SCAN_STOCKS = 500         # 最大扫描股票数

SCAN_BATCH_SIZE = 50          # 进度显示批次大小

调试模式

ENABLE_DEBUG = False          # 是否启用调试

SAVE_RESULTS = True           # 是否保存结果

复制
## 调参建议

### 不同市场环境
| 市场环境 | 建议调整 |
|---------|---------|
| 强势市场 | 提高`BAND_RISE_THRESHOLD`，增加`TOTAL_POSITION_MAX_PCT` |
| 震荡市场 | 降低`VOLUME_SHRINK_PCT`，放宽`PULLBACK_DAYS_MAX` |
| 弱势市场 | 启用`WEAK_MARKET_POSITION_PCT`，提高`STOP_LOSS_PCT` |

### 风险偏好
| 风险等级 | 建议调整 |
|---------|---------|
| 保守型 | 降低`SINGLE_POSITION_PCT`，提高`STOP_LOSS_PCT` |
| 稳健型 | 保持默认参数 |
| 激进型 | 提高`TOTAL_POSITION_MAX_PCT`，降低`VOLUME_SHRINK_PCT` |

## 注意事项

1. **参数验证**: 修改参数后建议先用小规模股票池测试
2. **回测验证**: 重要参数调整后应进行历史回测
3. **分步调整**: 每次只调整1-2个参数，观察效果
4. **记录日志**: 记录每次参数调整的效果，便于优化

## 常见问题

### Q1: 如何提高选股数量？
A: 降低`BAND_RISE_THRESHOLD`(如30→20)，降低`VOLUME_SHRINK_PCT`(如30→20)

### Q2: 如何降低风险？
A: 降低`SINGLE_POSITION_PCT`(如20→10)，提高`STOP_LOSS_PCT`(如5→3)

### Q3: 如何适应震荡市？
A: 放宽`PULLBACK_DAYS_MAX`(如5→7)，降低`VOLUME_SHRINK_PCT`(如30→20)

### Q4: 如何加快扫描速度？
A: 降低`MAX_SCAN_STOCKS`(如500→200)，降低`HISTORY_DAYS`(如60→30)
使用说明
1. 文件结构
复制
项目目录/
├── strong_stock_main.py    # 主程序
├── config.py              # 配置文件
├── run_strategy.bat       # Windows启动脚本
├── run_strategy.sh        # Linux/Mac启动脚本
└── README.md             # 说明文档
2. 运行步骤

首次运行：确保通达信客户端已登录

调整参数：根据需要修改config.py中的参数

运行程序：双击run_strategy.bat或运行python strong_stock_main.py

查看结果：程序会输出选股结果并保存到文件

3. 参数调整示例

示例1：降低选股要求（选更多股票）

python
下载
复制
# 修改config.py
BAND_RISE_THRESHOLD = 20.0    # 30 → 20
VOLUME_SHRINK_PCT = 20.0      # 30 → 20
PULLBACK_DAYS_MAX = 7         # 5 → 7

示例2：提高风险控制（更保守）

python
下载
复制
# 修改config.py
SINGLE_POSITION_PCT = 10      # 20 → 10
STOP_LOSS_PCT = 3.0           # 5 → 3
TOTAL_POSITION_MAX_PCT = 30   # 50 → 30

示例3：适应震荡市

python
下载
复制
# 修改config.py
VOLUME_SHRINK_PCT = 20.0      # 30 → 20
SUPPORT_TOLERANCE_PCT = 3.0   # 2 → 3
PROFIT_TAKING_DAYS = 2        # 3 → 2
优势特点

参数集中管理：所有策略参数都在config.py中，便于调整

详细注释：每个参数都有详细说明和使用建议

分类清晰：参数按功能分类，查找方便

灵活调整：支持不同市场环境和风险偏好

完整文档：提供详细的调参指南和示例

这样配置后，您只需修改config.py文件即可调整所有策略参数，无需修改主程序代码，大大提高了策略调整的便利性和安全性。
