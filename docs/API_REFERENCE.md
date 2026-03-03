# API接口文档

## 📡 概述

本系统采用HTTP REST API进行组件间通信。所有API均返回JSON格式数据，使用标准HTTP状态码。

### 基础信息
- **协议**：HTTP/1.1
- **数据格式**：JSON
- **字符编码**：UTF-8
- **超时设置**：30秒
- **重试机制**：3次，指数退避

### 通用响应格式
```json
{
  "status": "success|error",
  "data": {...},  // 成功时返回数据
  "error": "错误信息",  // 失败时返回错误
  "timestamp": "2026-03-01T09:25:00",
  "request_id": "uuid-v4"
}
```

### 通用错误码
| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

## 🎯 主Agent API (端口: 18789)

### 健康检查
**GET** `/health`

检查主Agent健康状态。

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "agent": "主Agent-总指挥",
    "port": 18789,
    "status": "running",
    "timestamp": "2026-03-01T09:25:00"
  }
}
```

### 状态查询
**GET** `/status`

获取主Agent详细状态信息。

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "agent": "主Agent-总指挥",
    "port": 18789,
    "status": "running",
    "last_task_time": "2026-03-01T09:25:00",
    "task_count": 15,
    "success_count": 14,
    "error_count": 1,
    "subagents_status": {
      "data_collector": "healthy",
      "strategy_engine": "healthy",
      "backtester": "healthy",
      "risk_manager": "healthy"
    }
  }
}
```

### 提交分析任务
**POST** `/task/submit`

提交新的分析任务。

**请求参数**：
```json
{
  "type": "daily_analysis|manual_analysis|backtest_only",
  "params": {
    "test_mode": false,  // 测试模式
    "force_refresh": false,  // 强制刷新数据
    "custom_filters": {}  // 自定义过滤条件
  }
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "task_id": "task_20260301_092500",
    "status": "submitted",
    "estimated_time": 120,  // 预计耗时（秒）
    "message": "任务已提交，预计2分钟内完成"
  }
}
```

### 获取任务结果
**GET** `/task/result/{task_id}`

获取指定任务的结果。

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "task_id": "task_20260301_092500",
    "status": "completed",
    "start_time": "2026-03-01T09:25:00",
    "end_time": "2026-03-01T09:26:30",
    "duration": 90,
    "result": {
      "signals_count": 5,
      "trading_plans": [...],
      "report_path": "./reports/20260301_092500.md"
    }
  }
}
```

## 📊 数据员 API (端口: 18790)

### 健康检查
**GET** `/health`

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "agent": "辅1-数据员",
    "port": 18790,
    "status": "running",
    "cache_size": 125,
    "last_update": "2026-03-01T09:24:30"
  }
}
```

### 获取热门板块
**POST** `/data/hot_sectors`

获取热门板块数据。

**请求参数**：
```json
{
  "days": 3,  // 统计天数（1-7）
  "count": 20,  // 返回数量（1-50）
  "refresh": false  // 强制刷新缓存
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "hot_sectors": [
      {
        "code": "BK0481",
        "name": "半导体",
        "gain_3d": 8.52,
        "stock_count": 85,
        "update_time": "2026-03-01T09:25:00"
      },
      {
        "code": "BK0493",
        "name": "人工智能",
        "gain_3d": 6.78,
        "stock_count": 42,
        "update_time": "2026-03-01T09:25:00"
      }
    ],
    "total_count": 20,
    "generated_at": "2026-03-01T09:25:00"
  }
}
```

### 获取龙虎榜数据
**POST** `/data/dragon_tiger`

获取龙虎榜数据。

**请求参数**：
```json
{
  "days": 30,  // 查询天数（1-90）
  "symbol": "000001",  // 可选：指定股票代码
  "refresh": false
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "dragon_tiger_list": [
      {
        "code": "000001",
        "name": "平安银行",
        "date": "2026-02-28",
        "reason": "日涨幅偏离值达7%",
        "buy_amount": 125000000,
        "sell_amount": 85000000,
        "net_amount": 40000000
      }
    ],
    "total_count": 45,
    "time_range": "2026-02-01至2026-03-01"
  }
}
```

### 获取股票基础数据
**POST** `/data/stock_basic`

获取股票基础数据。

**请求参数**：
```json
{
  "symbols": ["000001", "000002", "000858"],
  "fields": ["最新价", "涨跌幅", "成交量", "成交额", "总市值"]
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "stocks": [
      {
        "code": "000001",
        "name": "平安银行",
        "current_price": 12.45,
        "change_pct": 1.52,
        "volume": 125000000,
        "turnover": 1556250000,
        "market_cap": 242.5,
        "update_time": "2026-03-01T09:25:00"
      }
    ],
    "total_count": 3
  }
}
```

### 获取历史K线数据
**POST** `/data/historical`

获取股票历史K线数据。

**请求参数**：
```json
{
  "symbol": "000001",
  "start_date": "20250101",
  "end_date": "20260301",
  "period": "daily",  // daily, weekly, monthly
  "adjust": "qfq"  // qfq: 前复权, hfq: 后复权, None: 不复权
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "symbol": "000001",
    "period": "daily",
    "adjust": "qfq",
    "kline_data": [
      {
        "date": "2026-03-01",
        "open": 12.30,
        "high": 12.50,
        "low": 12.20,
        "close": 12.45,
        "volume": 125000000,
        "turnover": 1556250000
      }
    ],
    "total_records": 280
  }
}
```

## 🎯 策略员 API (端口: 18791)

### 健康检查
**GET** `/health`

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "agent": "辅2-策略员",
    "port": 18791,
    "status": "running",
    "filters_count": 7,
    "last_run": "2026-03-01T09:25:30"
  }
}
```

### 运行选股策略
**POST** `/strategy/run`

运行完整的选股策略。

**请求参数**：
```json
{
  "hot_sectors": [
    {
      "code": "BK0481",
      "name": "半导体",
      "gain_3d": 8.52
    }
  ],
  "filters": {
    "max_price": 50,
    "max_total_gain": 0.3,
    "dragon_tiger_days": 30,
    "min_market_cap": 50,
    "min_daily_turnover": 200000000,
    "exclude_st": true,
    "exclude_suspended": true,
    "convergence_year": 2025,
    "divergence_year": 2026,
    "ma_periods": [5, 10, 20, 30]
  }
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "signals": [
      {
        "code": "002049",
        "name": "紫光国微",
        "sector": "半导体",
        "current_price": 98.50,
        "dragon_tiger": true,
        "dragon_tiger_date": "2026-02-28",
        "total_gain_since_2025": 0.182,
        "ma_pattern": "2025年粘合 → 2026年发散",
        "market_cap": 85.3,
        "daily_turnover": 320000000,
        "is_st": false,
        "filter_passed": [1, 2, 3, 4, 5, 6]  // 通过的条件编号
      }
    ],
    "filter_steps": {
      "step1_dragon_tiger": 125,
      "step2_after_dragon_tiger": 89,
      "step3_after_price": 67,
      "step4_after_gain": 42,
      "step5_after_ma": 18,
      "step6_after_basic": 5
    },
    "total_stocks": 125,
    "filtered_stocks": 5,
    "signal_count": 1,
    "generated_at": "2026-03-01T09:26:00"
  }
}
```

### 获取策略状态
**GET** `/strategy/status`

获取策略引擎状态。

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "agent": "辅2-策略员",
    "filters": [
      "热门板块过滤",
      "龙虎榜过滤",
      "股价过滤",
      "涨幅过滤",
      "均线形态过滤",
      "基础条件过滤"
    ],
    "cache_hit_rate": 0.85,
    "avg_process_time": 2.5,
    "total_runs": 156
  }
}
```

## 📈 回测员 API (端口: 18792)

### 健康检查
**GET** `/health`

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "agent": "辅3-回测员",
    "port": 18792,
    "status": "running",
    "cache_size": 89,
    "min_win_rate": 0.52
  }
}
```

### 运行回测验证
**POST** `/backtest/run`

对选股信号进行回测验证。

**请求参数**：
```json
{
  "signals": [
    {
      "code": "002049",
      "name": "紫光国微",
      "current_price": 98.50
    }
  ],
  "period": 90,  // 回测周期（天）
  "min_win_rate": 0.52,  // 最低胜率要求
  "sample_size": 50  // 最大样本数量
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "valid_signals": [
      {
        "code": "002049",
        "name": "紫光国微",
        "backtest_win_rate": 0.583,
        "backtest_total_trades": 12,
        "backtest_profit_trades": 7,
        "backtest_avg_profit": 0.042,
        "backtest_max_drawdown": 0.125,
        "backtest_sharpe_ratio": 0.85,
        "trades_sample": [
          {
            "entry_date": "2025-12-15",
            "exit_date": "2025-12-20",
            "profit_pct": 0.058,
            "days_held": 5,
            "exit_reason": "signal"
          }
        ]
      }
    ],
    "backtest_stats": {
      "avg_win_rate": 0.583,
      "std_win_rate": 0.085,
      "avg_profit": 0.042,
      "avg_max_drawdown": 0.125,
      "avg_sharpe_ratio": 0.85,
      "total_trades": 12,
      "sample_size": 1,
      "valid_samples": 1
    },
    "backtest_report": "# 回测分析报告...",
    "total_signals": 1,
    "valid_count": 1,
    "filter_rate": 1.0,
    "generated_at": "2026-03-01T09:26:30"
  }
}
```

### 获取回测统计
**POST** `/backtest/stats`

获取回测统计信息。

**请求参数**：
```json
{
  "backtest_id": "latest"  // 或具体的回测ID
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "backtest_id": "backtest_20260301_092630",
    "overall_stats": {
      "total_backtests": 156,
      "avg_win_rate": 0.548,
      "avg_profit": 0.038,
      "avg_max_drawdown": 0.142,
      "success_rate": 0.72
    },
    "recent_backtests": [
      {
        "id": "backtest_20260301_092630",
        "time": "2026-03-01T09:26:30",
        "signals_count": 5,
        "valid_count": 3,
        "avg_win_rate": 0.583
      }
    ]
  }
}
```

## 🛡️ 风控员 API (端口: 18793)

### 健康检查
**GET** `/health`

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "agent": "辅4-风控员",
    "port": 18793,
    "status": "running",
    "positions_count": 3,
    "total_value": 285000,
    "portfolio_ratio": 0.285
  }
}
```

### 风险检查和交易计划
**POST** `/risk/check`

检查风险并生成交易计划。

**请求参数**：
```json
{
  "signals": [
    {
      "code": "002049",
      "name": "紫光国微",
      "current_price": 98.50,
      "backtest_win_rate": 0.583,
      "backtest_max_drawdown": 0.125
    }
  ],
  "capital": 1000000,  // 可用资金
  "position_rules": {
    "max_positions": 5,
    "max_portfolio_size": 0.6,
    "max_single_position": 0.3,
    "initial_position": 0.2,
    "add_position_size": 0.1,
    "take_profit": 0.05,
    "stop_loss": 0.08,
    "max_holding_days": 7,
    "auto_sell_days": 5
  }
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "trading_plans": [
      {
        "code": "002049",
        "name": "紫光国微",
        "sector": "半导体",
        "current_price": 98.50,
        "buy_price": 98.50,
        "add_price": 96.53,
        "take_profit_price": 103.43,
        "stop_loss_price": 90.62,
        "initial_shares": 200,
        "max_shares": 300,
        "initial_investment": 19700,
        "max_investment": 29550,
        "initial_position_ratio": 0.2,
        "max_position_ratio": 0.3,
        "holding_days_limit": 7,
        "risk_score": 42,
        "backtest_win_rate": 0.583,
        "backtest_avg_profit": 0.042,
        "dragon_tiger": "是",
        "total_gain": "18.2%",
        "ma_pattern": "2025年粘合 → 2026年发散",
        "logic": "属于热门板块【半导体】，近期