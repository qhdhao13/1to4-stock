#!/usr/bin/env python3
"""
股票系统配置文件
定义一主四辅架构和策略参数
"""

import os
from datetime import datetime

# ==================== 系统架构配置 ====================
SYSTEM_ARCHITECTURE = {
    "master": {
        "port": 18889,
        "name": "主Agent-总指挥",
        "description": "任务调度、结果聚合、报告生成",
        "start_time": "09:25:00",  # 每日启动时间
        "check_interval": 60,  # 检查间隔(秒)
    },
    "data_collector": {
        "port": 18990,  # 改为18990避免冲突
        "name": "辅1-数据员",
        "description": "热门板块、龙虎榜、基础数据采集",
        "dependencies": [],  # 无依赖
    },
    "strategy_engine": {
        "port": 18891,
        "name": "辅2-策略员",
        "description": "选股规则、信号生成、交易计划",
        "dependencies": ["data_collector"],  # 依赖数据员
    },
    "backtester": {
        "port": 18892,
        "name": "辅3-回测员",
        "description": "历史验证、胜率计算、风险收益",
        "dependencies": ["strategy_engine"],  # 依赖策略员
    },
    "risk_manager": {
        "port": 18893,
        "name": "辅4-风控员",
        "description": "仓位管理、止损监控、风险过滤",
        "dependencies": ["strategy_engine", "backtester"],  # 依赖策略和回测
    }
}

# ==================== 策略参数配置 ====================
STRATEGY_CONFIG = {
    "name": "热门板块・龙虎榜・均线粘合发散・短线低吸系统",
    "version": "1.0.0",
    "author": "OpenClaw Stock System",
    
    # 资金管理
    "capital": 1000000,  # 初始资金100万
    "max_positions": 2,  # 同时持股最多2只
    "max_portfolio_size": 0.6,  # 总仓位上限60%
    "min_cash_ratio": 0.4,  # 永远保留≥40%现金
    
    # 仓位管理
    "initial_position": 0.2,  # 首次开仓20%
    "add_position_threshold": -0.02,  # 下跌2%补仓
    "add_position_size": 0.1,  # 补仓10%
    "max_single_position": 0.3,  # 单票总仓位上限30%
    
    # 止盈止损
    "take_profit": 0.05,  # 收益≥5% → 全部卖出
    "stop_loss": 0.08,  # 最大亏损≤8% → 无条件清仓
    
    # 时间控制
    "max_holding_days": 7,  # 最长不超过7天
    "auto_sell_days": 5,  # 5天不涨 → 自动卖出
    
    # 选股条件
    "stock_filters": {
        # 板块条件
        "hot_sector_count": 20,  # 热门板块前20名
        "hot_sector_days": 3,  # 近3日涨幅
        
        # 龙虎榜条件
        "dragon_tiger_days": 30,  # 近1个月内上过龙虎榜
        
        # 股价条件
        "max_price": 50,  # 股价≤50元
        
        # 涨幅限制
        "max_total_gain": 0.3,  # 2025.1.1至今累计涨幅≤30%
        "start_date": "2025-01-01",  # 统计起始日
        
        # 均线参数
        "ma_periods": [5, 10, 20, 30],  # MA5/10/20/30
        "convergence_year": 2025,  # 2025年均线粘合
        "divergence_year": 2026,  # 2026年开始向上发散
        
        # 基础过滤
        "min_market_cap": 50,  # 市值≥50亿
        "min_daily_turnover": 200000000,  # 日均成交额≥2亿
        "exclude_st": True,  # 排除ST股
        "exclude_suspended": True,  # 排除停牌股
    },
    
    # 数据源配置
    "data_sources": {
        "akshare": {
            "enabled": True,
            "priority": 1,
            "timeout": 30,
        },
        "tushare": {
            "enabled": True,
            "token": "97f10d5f7b6ddedae78d3293caf73a020ab83b00c199883847a9ad5c",
            "priority": 2,
            "timeout": 30,
        }
    },
    
    # 回测参数
    "backtest": {
        "period": 90,  # 近3个月
        "min_win_rate": 0.52,  # 只保留胜率≥52%的标的
        "sample_size": 100,  # 样本数量
    },
    
    # 输出配置
    "output": {
        "report_template": "standard",  # 报告模板
        "save_path": "./reports",  # 报告保存路径
        "log_level": "INFO",  # 日志级别
    }
}

# ==================== 网络通信配置 ====================
NETWORK_CONFIG = {
    "host": "localhost",
    "timeout": 30,  # 超时时间(秒)
    "retry_times": 3,  # 重试次数
    "heartbeat_interval": 10,  # 心跳间隔(秒)
    
    # 消息格式
    "message_format": {
        "type": "json",
        "encoding": "utf-8",
        "compression": False,
    },
    
    # API端点
    "endpoints": {
        "master": {
            "submit_task": "/task/submit",
            "get_result": "/task/result",
            "status": "/status",
        },
        "data_collector": {
            "get_hot_sectors": "/data/hot_sectors",
            "get_dragon_tiger": "/data/dragon_tiger",
            "get_stock_data": "/data/stock",
        },
        "strategy_engine": {
            "run_strategy": "/strategy/run",
            "get_signals": "/strategy/signals",
        },
        "backtester": {
            "run_backtest": "/backtest/run",
            "get_stats": "/backtest/stats",
        },
        "risk_manager": {
            "check_risk": "/risk/check",
            "get_position": "/risk/position",
        }
    }
}

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATHS = {
    "data": os.path.join(BASE_DIR, "../data"),
    "logs": os.path.join(BASE_DIR, "../logs"),
    "reports": os.path.join(BASE_DIR, "../reports"),
    "cache": os.path.join(BASE_DIR, "../cache"),
}

# 创建必要目录
for path in PATHS.values():
    os.makedirs(path, exist_ok=True)

# ==================== 工具函数 ====================
def get_today_str():
    """获取今日日期字符串"""
    return datetime.now().strftime("%Y%m%d")

def get_report_filename():
    """生成报告文件名"""
    return f"stock_report_{get_today_str()}.md"

def get_agent_url(agent_name, endpoint=""):
    """获取Agent的URL"""
    if agent_name not in SYSTEM_ARCHITECTURE:
        raise ValueError(f"未知的Agent: {agent_name}")
    
    port = SYSTEM_ARCHITECTURE[agent_name]["port"]
    base_url = f"http://localhost:{port}"
    
    if endpoint:
        if agent_name in NETWORK_CONFIG["endpoints"]:
            if endpoint in NETWORK_CONFIG["endpoints"][agent_name]:
                endpoint_path = NETWORK_CONFIG["endpoints"][agent_name][endpoint]
                return base_url + endpoint_path
    
    return base_url

if __name__ == "__main__":
    print("✅ 股票系统配置文件加载成功")
    print(f"系统架构: {len(SYSTEM_ARCHITECTURE)}个Agent")
    print(f"策略名称: {STRATEGY_CONFIG['name']}")
    print(f"初始资金: {STRATEGY_CONFIG['capital']:,}元")