# 策略详细说明文档

## 🎯 策略概述

**热门板块・龙虎榜・均线粘合发散・短线低吸系统**是一个基于技术分析和市场情绪的多因子选股策略。策略核心是通过7个严格的选股条件，筛选出具有高概率上涨潜力的股票，并配合严格的交易规则进行风险控制。

## 📊 7大选股条件详解

### 条件1：热门板块筛选

#### 筛选标准
- **数据源**：AkShare `stock_board_industry_summary_em()`
- **时间窗口**：最近3个交易日
- **筛选数量**：涨幅前20名的板块
- **更新频率**：每日开盘前更新

#### 实现逻辑
```python
def get_hot_sectors(days=3, count=20):
    """
    获取热门板块
    1. 获取各板块近3日涨跌幅
    2. 按涨幅降序排序
    3. 取前20名作为热门板块
    """
    sector_data = ak.stock_board_industry_summary_em()
    
    # 计算近N日涨幅
    sector_data['gain_3d'] = sector_data['涨跌幅'].rolling(window=days).sum()
    
    # 筛选和排序
    hot_sectors = sector_data.nlargest(count, 'gain_3d')
    
    return hot_sectors[['板块名称', '板块代码', 'gain_3d']].to_dict('records')
```

#### 逻辑依据
- 资金流向：热门板块有资金持续流入
- 市场关注度：高关注度带来流动性溢价
- 趋势延续：短期强势板块有延续性

### 条件2：龙虎榜条件

#### 筛选标准
- **数据源**：AkShare `stock_sina_lhb_detail_daily()`
- **时间窗口**：最近30个自然日
- **上榜类型**：机构席位、游资席位
- **上榜次数**：至少上榜1次

#### 实现逻辑
```python
def check_dragon_tiger(symbol, days=30):
    """
    检查股票是否近期上过龙虎榜
    1. 获取近30天龙虎榜数据
    2. 检查目标股票是否在榜
    3. 记录上榜日期和原因
    """
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    
    lhb_data = ak.stock_sina_lhb_detail_daily(start_date=start_date, end_date=end_date)
    
    # 检查股票是否在龙虎榜中
    in_lhb = symbol in lhb_data['代码'].values if not lhb_data.empty else False
    
    return {
        "in_lhb": in_lhb,
        "last_date": lhb_data[lhb_data['代码'] == symbol]['上榜日期'].iloc[0] if in_lhb else None,
        "reason": lhb_data[lhb_data['代码'] == symbol]['上榜原因'].iloc[0] if in_lhb else None
    }
```

#### 逻辑依据
- 机构关注：龙虎榜代表大资金关注
- 流动性提升：上榜股票交易活跃度提高
- 信息优势：机构调研和信息优势

### 条件3：股价条件

#### 筛选标准
- **价格上限**：≤ 50元
- **价格下限**：≥ 5元（隐含条件）
- **价格单位**：人民币

#### 实现逻辑
```python
def filter_by_price(stocks, max_price=50, min_price=5):
    """
    按股价过滤股票
    1. 获取股票实时价格
    2. 筛选价格区间内的股票
    """
    spot_data = ak.stock_zh_a_spot()
    
    filtered_stocks = []
    for symbol in stocks:
        stock_info = spot_data[spot_data['代码'] == symbol]
        if not stock_info.empty:
            price = stock_info.iloc[0]['最新价']
            if min_price <= price <= max_price:
                filtered_stocks.append(symbol)
    
    return filtered_stocks
```

#### 逻辑依据
- 资金效率：低价股资金利用率高
- 波动性适中：50元以下股票波动相对合理
- 散户参与度：低价股散户参与度高，流动性好

### 条件4：涨幅限制条件

#### 筛选标准
- **起始日期**：2025年1月1日
- **涨幅上限**：累计涨幅 ≤ 30%
- **计算基准**：前复权价格
- **数据频率**：日线数据

#### 实现逻辑
```python
def filter_by_gain(symbol, start_date="20250101", max_gain=0.3):
    """
    检查2025.1.1至今涨幅
    1. 获取历史数据
    2. 计算累计涨幅
    3. 判断是否超过上限
    """
    end_date = datetime.now().strftime("%Y%m%d")
    
    hist_data = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"  # 前复权
    )
    
    if hist_data.empty or len(hist_data) < 10:
        return False
    
    # 计算累计涨幅
    start_price = hist_data.iloc[-1]['收盘']  # 最早的价格
    end_price = hist_data.iloc[0]['收盘']     # 最新的价格
    total_gain = (end_price - start_price) / start_price
    
    return total_gain <= max_gain
```

#### 逻辑依据
- 风险控制：避免追高已大幅上涨股票
- 上涨空间：留有足够上涨空间
- 均值回归：大幅上涨后可能回调

### 条件5：均线形态条件

#### 筛选标准
- **粘合时期**：2025年全年
- **发散时期**：2026年开始
- **均线周期**：MA5、MA10、MA20、MA30
- **粘合标准**：均线间距 < 股价的2%
- **发散标准**：均线向上排列且趋势向上

#### 实现逻辑

##### 均线粘合检测
```python
def check_ma_convergence_2025(symbol):
    """
    检查2025年均线粘合
    1. 获取2025年历史数据
    2. 计算各周期均线
    3. 检查均线间距
    """
    # 获取2025年数据
    hist_2025 = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date="20250101",
        end_date="20251231",
        adjust="qfq"
    )
    
    if hist_2025.empty or len(hist_2025) < 100:
        return False
    
    df = hist_2025.copy()
    df['close'] = df['收盘'].astype(float)
    
    # 计算均线
    ma_periods = [5, 10, 20, 30]
    ma_values = []
    
    for period in ma_periods:
        ma = df['close'].rolling(window=period).mean()
        ma_values.append(ma[-20:])  # 取最后20个交易日
    
    # 计算均线标准差（粘合度）
    ma_matrix = np.array(ma_values)
    ma_std = np.std(ma_matrix, axis=0).mean()
    
    # 粘合判断：均线波动小于股价的2%
    current_price = df['close'].iloc[-1]
    return ma_std < current_price * 0.02
```

##### 均线发散检测
```python
def check_ma_divergence_2026(symbol):
    """
    检查2026年均线发散
    1. 获取2026年历史数据
    2. 计算均线排列
    3. 检查发散趋势
    """
    # 获取2026年数据
    end_date = datetime.now().strftime("%Y%m%d")
    hist_2026 = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date="20260101",
        end_date=end_date,
        adjust="qfq"
    )
    
    if hist_2026.empty or len(hist_2026) < 20:
        return False
    
    df = hist_2026.copy()
    df['close'] = df['收盘'].astype(float)
    
    # 计算均线值
    ma_periods = [5, 10, 20, 30]
    ma_current = []
    ma_trends = []
    
    for period in ma_periods:
        ma = df['close'].rolling(window=period).mean()
        ma_current.append(ma.iloc[-1])  # 当前均线值
        
        # 计算均线趋势（斜率）
        if len(ma) >= 10:
            x = np.arange(10)
            y = ma[-10:].values
            slope = np.polyfit(x, y, 1)[0]
            ma_trends.append(slope)
    
    # 发散判断条件
    # 1. 均线向上排列：MA5 > MA10 > MA20 > MA30
    is_ascending = all(ma_current[i] > ma_current[i+1] for i in range(len(ma_current)-1))
    
    # 2. 均线趋势向上：各均线斜率 > 0
    is_upward = all(trend > 0 for trend in ma_trends) if ma_trends else False
    
    return is_ascending and is_upward
```

#### 逻辑依据
- **粘合阶段**：多空力量平衡，酝酿变盘
- **发散阶段**：趋势确立，上涨动力充足
- **时间周期**：长期酝酿，短期爆发

### 条件6：基础过滤条件

#### 筛选标准
- **ST股票**：排除ST和*ST股票
- **市值要求**：总市值 ≥ 50亿元
- **流动性要求**：日均成交额 ≥ 2亿元
- **上市时间**：上市满1年（隐含条件）

#### 实现逻辑
```python
def filter_basic_conditions(symbol):
    """
    基础条件过滤
    1. 排除ST股票
    2. 检查市值
    3. 检查成交额
    """
    spot_data = ak.stock_zh_a_spot()
    stock_info = spot_data[spot_data['代码'] == symbol]
    
    if stock_info.empty:
        return False
    
    info = stock_info.iloc[0]
    
    # 1. 排除ST股票
    name = info['名称']
    if 'ST' in name or '*ST' in name:
        return False
    
    # 2. 检查市值
    market_cap = info['总市值']
    if isinstance(market_cap, str):
        market_cap = float(market_cap.replace('亿', '')) if '亿' in market_cap else 0
    
    if market_cap < 50:  # 50亿元
        return False
    
    # 3. 检查成交额
    turnover = info['成交额']
    if turnover < 200000000:  # 2亿元
        return False
    
    return True
```

#### 逻辑依据
- **ST排除**：避免退市风险和流动性风险
- **市值要求**：确保公司规模和稳定性
- **流动性要求**：确保进出方便，避免冲击成本

## 💰 交易规则详解

### 规则1：资金管理规则

#### 参数设置
- **初始资金**：1,000,000元（模拟盘）
- **总仓位上限**：60%（600,000元）
- **单票仓位上限**：30%（300,000元）
- **现金保留**：至少保留40%现金

#### 实现逻辑
```python
class CapitalManager:
    def __init__(self, total_capital=1000000):
        self.total_capital = total_capital
        self.positions = {}  # 当前持仓
        self.available_capital = total_capital
    
    def can_buy(self, symbol, amount):
        """检查是否可以买入"""
        # 检查总仓位
        total_position_value = sum(p['current_value'] for p in self.positions.values())
        if total_position_value + amount > self.total_capital * 0.6:
            return False
        
        # 检查单票仓位
        current_position = self.positions.get(symbol, {}).get('current_value', 0)
        if current_position + amount > self.total_capital * 0.3:
            return False
        
        # 检查可用资金
        if amount > self.available_capital:
            return False
        
        return True
```

### 规则2：建仓与补仓规则

#### 建仓规则
- **首次建仓**：20%仓位（单票上限的20%）
- **建仓价格**：当前价格 ± 1%
- **建仓时机**：满足所有选股条件时

#### 补仓规则
- **补仓条件**：股价下跌2%
- **补仓比例**：10%仓位（单票上限的10%）
- **补仓次数**：最多补仓1次
- **补仓后仓位**：不超过30%

#### 实现逻辑
```python
def generate_trading_plan(signal, available_capital):
    """生成交易计划"""
    current_price = signal['current_price']
    
    # 计算价格区间
    buy_price_range = (current_price * 0.99, current_price * 1.01)  # ±1%
    add_price = current_price * 0.98  # 下跌2%补仓
    take_profit = current_price * 1.05  # 上涨5%止盈
    stop_loss = current_price * 0.92  # 下跌8%止损
    
    # 计算仓位
    initial_ratio = 0.2  # 首次20%
    add_ratio = 0.1      # 补仓10%
    max_ratio = 0.3      # 最大30%
    
    initial_investment = available_capital * initial_ratio
    add_investment = available_capital * add_ratio
    
    return {
        "buy_price_range": buy_price_range,
        "add_price": add_price,
        "take_profit": take_profit,
        "stop_loss": stop_loss,
        "initial_investment": initial_investment,
        "add_investment": add_investment,
        "max_investment": available_capital * max_ratio
    }
```

### 规则3：止盈止损规则

#### 止盈规则
- **止盈比例**：+5%
- **止盈方式**：全部卖出
- **止盈时机**：盘中触及止盈价

#### 止损规则
- **止损比例**：-8%
- **止损方式**：无条件全部卖出
- **止损时机**：盘中触及止损价立即执行

#### 实现逻辑
```python
class PositionMonitor:
    def __init__(self):
        self.positions = {}
    
    def check_stop_loss_take_profit(self, symbol, current_price):
        """检查是否需要止损止盈"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        cost_price = position['cost_price']
        
        # 计算盈亏比例
        profit_pct = (current_price - cost_price) / cost_price
        
        # 止盈检查
        if profit_pct >= 0.05:
            return {
                "action": "sell",
                "reason": "take_profit",
                "profit_pct": profit_pct
            }
        
        # 止损检查
        if profit_pct <= -0.08:
            return {
                "action": "sell",
                "reason": "stop_loss",
                "profit_pct": profit_pct
            }
        
        return None
```

### 规则4：时间控制规则

#### 持有时间规则
- **最长持有**：7个交易日
- **自动卖出**：5个交易日不涨自动卖出
- **时间计算**：按交易日计算，排除节假日

#### 实现逻辑
```python
def check_holding_time(position, current_date):
    """检查持仓时间"""
    buy_date = position['buy_date']
    holding_days = (current_date - buy_date).days
    
    # 检查是否超过最长持有时间
    if holding_days >= 7:
        return {
            "action": "sell",
            "reason": "max_holding_days",
            "holding_days": holding_days
        }
    
    # 检查是否5天不涨
    if holding_days >= 5:
        current_price = position['current_price']
        cost_price = position['cost_price']
        profit_pct = (current_price - cost_price) / cost_price
        
        if profit_pct <= 0:  # 不涨或亏损
            return {
                "action": "sell",
                "reason": "no_gain_5days",
                "holding_days": holding_days,
                "profit_pct": profit_pct
            }
    
    return None
```

## 📈 策略逻辑总结

### 核心逻辑链
```
市场情绪（热门板块）→ 资金关注（龙虎榜）→ 价格合理（≤50元）
→ 上涨空间（涨幅≤30%）→ 技术形态（均线粘合发散）
→ 基本面过滤（非ST、市值≥50亿、成交额≥2亿）
→ 风险控制（仓位管理、止盈止损、时间控制）
```

### 策略优势
1. **多维度验证**：7个条件从不同角度验证股票质量
2. **风险控制严格**：多层次风控体系
3. **逻辑清晰**：每个条件都有明确的市场逻辑
4. **可执行性强**：明确的买卖点和仓位管理

### 适用市场环境
- **震荡市**：均线粘合发散策略效果较好
- **结构性行情**：热门板块策略能捕捉热点
- **温和上涨市**：风险控制能保护收益