#!/usr/bin/python
# -*- coding: utf8 -*-
# cp936

#
# 警告：Hikyuu 为量化研究工具，本身不包含程序化交易接口。此部分仅为策略调度运行时示例，
#      供自行实现程序化交易时参考，请自行负责程序化交易可能造成的损失。
#

from hikyuu import *
from hikyuu import sm, Strategy
import numpy as np

# 策略参数
FLAT_THRESHOLD = 0.002  # 判断均线走平的阈值，均线变化小于0.2%视为走平
BUY_DISTANCE = 0.01     # 实时价低于均线1%时买入
SELL_DISTANCE = 0.01    # 实时价高于均线1%时卖出
MA_PERIOD = 200          # 计算移动平均的周期

# 存储历史均价和股票持仓状态
price_history = {}
positions = {}





def is_ma_flat(stk_code, current_avg):
    """判断均线是否走平"""
    if stk_code not in price_history:
        price_history[stk_code] = []
    
    history = price_history[stk_code]
    history.append(current_avg)
    
    # 保留最近的N个均价用于计算均线
    if len(history) > MA_PERIOD:
        history.pop(0)
    
    # 至少需要MA_PERIOD个数据点才能判断均线趋势
    if len(history) < MA_PERIOD:
        return False
    
    # 计算最近几个均价的变化率的标准差，判断是否走平
    ma_changes = np.array([abs(history[i]/history[i-1] - 1) for i in range(1, len(history))])
    avg_change = np.mean(ma_changes)
    
    return avg_change < FLAT_THRESHOLD

def on_change(stg: Strategy, stk: Stock, spot: SpotRecord):
    print("[on_change]:", stk.market_code, stk.name, spot.close, spot.bid1, spot.ask1)
    stk_code = f"{stk.market_code}{stk.code}"
    cur_price = spot.close
    avg_price = spot.amount * 100 / spot.volume if spot.volume > 0 else cur_price
    # 计算实时价与均线的相对距离
    price_distance = (cur_price / avg_price) - 1


    print(f"{Datetime.now()}[on_change]: {stk.market_code}, cur: {cur_price:.3f}, "
          f"avg: {avg_price:.3f}, change: {price_distance:.2%}, "
          f"b1:{spot.bid1:.3f}({spot.bid1_amount}), s1:{spot.ask1:.3f}({spot.ask1_amount}),"
          f"b2:{spot.bid2:.3f}({spot.bid2_amount}), s2:{spot.ask2:.3f}({spot.ask2_amount})")
    
    # 初始化持仓状态
    if stk_code not in positions:
        positions[stk_code] = False  # False表示未持仓
    
    # 检查均线是否走平
    
    ma_flat = is_ma_flat(stk_code, avg_price)

    
    
    
    # 交易逻辑
    if not positions[stk_code]:  # 未持仓，寻找买入信号
        if ma_flat and price_distance < -BUY_DISTANCE:
            print(f"买入信号: {stk.name} 当前价: {cur_price:.3f}, 均价: {avg_price:.3f}, 距离: {price_distance:.2%}")
            # 实际买入操作在这里实现
            # buy_stock(stk, amount)
            positions[stk_code] = True
    else:  # 已持仓，寻找卖出信号
        if price_distance > SELL_DISTANCE:
            print(f"卖出信号: {stk.name} 当前价: {cur_price:.3f}, 均价: {avg_price:.3f}, 距离: {price_distance:.2%}")
            # 实际卖出操作在这里实现
            # sell_stock(stk, amount)
            positions[stk_code] = False

def on_spot(stg: Strategy, rev_time: Datetime):
    # print("[on_received_spot] rev_time:", rev_time)
    pass


def my_func1(stg: Strategy):
    print("[my_func1]", str(stg.now()))


def my_func2(stg: Strategy):
    print("[my_func2] calculate:", stg.now())
    for s in sm:
        print(s)


# 注意：
#   1.每一个Strategy 只能作为独立进程执行，即 python xxx.py 的方式执行！
#   2.请开启 HikyuuTdx 行情采集，否则接收不到数据
# Strategy 方式运行示例
if __name__ == '__main__':
    sm
    # 创建策略运行时，必须指定 stock 和 ktype 列表
    # strategy 只会加载指定的 stock, ktype 的数据，行情接收也只会更新这些数据
    # 如需使用交易日历，请记得同时指定 sh000001
    s = Strategy(['sz002481'],  [Query.MIN, Query.DAY])

    # 当前自动延迟10秒/20秒后执行，忽略节假日限制
    s.run_daily_at(my_func1, Datetime.now() - Datetime.today() + Seconds(10), False)
    s.run_daily_at(my_func1, Datetime.now() - Datetime.today() + Seconds(20), False)

    # 收到指定 stock 的行情更新
    s.on_change(on_change)

    # 收到行情更新
    s.on_received_spot(on_spot)

    # 每隔 1 分钟循环一次 (ignore_market 忽略开闭市时间限制, 否则仅在开盘期间执行)
    s.run_daily(my_func2, Minutes(1))  # , ignore_market=True)
    s.start()
