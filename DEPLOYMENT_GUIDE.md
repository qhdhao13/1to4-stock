# 🐰 万兔福智能股票分析系统部署指南

## 🎯 系统概述

**万兔福**（万物皆可分析，快速如兔，福运相伴）智能股票分析系统采用"一主四辅"万兔福架构，包含5个独立的Agent协同工作：

1. **🦸 万兔福总指挥 (18889)**: 主Agent - 任务调度、结果聚合、报告生成
2. **🐇 万兔之眼 (18990)**: 数据员 - 数据采集、热门板块、龙虎榜监控
3. **🐇 万兔之脑 (18891)**: 策略员 - 策略引擎、智能选股、信号生成
4. **🐇 万兔之镜 (18892)**: 回测员 - 历史验证、胜率计算、风险收益
5. **🐇 万兔之盾 (18893)**: 风控员 - 风险控制、仓位管理、止损监控

## 系统架构

```
┌─────────────────────────────────────────────┐
│                主Agent (18889)               │
│          任务调度 & 报告生成                 │
└───────────────┬───────────────┬─────────────┘
                │               │
                ▼               ▼
    ┌───────────────┐   ┌───────────────┐
    │  数据员       │   │  策略员       │
    │  (18990)      │   │  (18891)      │
    │  数据采集     │   │  策略执行     │
    └───────┬───────┘   └───────┬───────┘
            │                   │
            └───────┬───────────┘
                    │
            ┌───────▼───────┐   ┌───────────────┐
            │  回测员       │   │  风控员       │
            │  (18892)      │   │  (18893)      │
            │  历史验证     │   │  风险控制     │
            └───────────────┘   └───────────────┘
```

## 环境要求

### 硬件要求
- CPU: 2核以上
- 内存: 4GB以上
- 存储: 1GB可用空间

### 软件要求
- Python 3.8+
- pip 包管理工具
- Git (用于版本控制)

### Python依赖
```bash
# 核心依赖
pip install aiohttp aiosignal aiohappyeyeballs

# 数据源依赖
pip install akshare pandas numpy

# 可选：如果需要使用TuShare
pip install tushare
```

## 快速部署

### 1. 克隆代码
```bash
git clone <repository-url>
cd stock_system
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置系统
编辑 `config.py` 文件，根据需要调整：
- 端口配置
- 策略参数
- 数据源设置

### 4. 启动系统

#### 方式一：一键启动（推荐）
```bash
python3 start_all.py
```

#### 方式二：手动启动各个Agent
```bash
# 启动数据员
python3 data_collector.py &

# 启动策略员
python3 strategy_engine_simple.py &

# 启动回测员
python3 backtester_simple.py &

# 启动风控员
python3 risk_manager_simple.py &

# 启动主Agent
python3 master_agent_simple.py &
```

### 5. 验证部署
```bash
# 检查所有Agent健康状态
curl http://localhost:18889/health

# 运行每日分析
curl http://localhost:18889/analysis/daily
```

## 配置文件说明

### config.py 主要配置项

#### 系统架构配置
```python
SYSTEM_ARCHITECTURE = {
    "master": {"port": 18889, ...},
    "data_collector": {"port": 18990, ...},
    "strategy_engine": {"port": 18891, ...},
    "backtester": {"port": 18892, ...},
    "risk_manager": {"port": 18893, ...}
}
```

#### 策略参数配置
```python
STRATEGY_CONFIG = {
    "capital": 1000000,  # 初始资金
    "max_positions": 2,  # 同时持股数量
    "take_profit": 0.05,  # 止盈比例
    "stop_loss": 0.08,   # 止损比例
    # ... 更多配置
}
```

#### 数据源配置
```python
"data_sources": {
    "akshare": {"enabled": True, "priority": 1},
    "tushare": {"enabled": True, "token": "your_token"}
}
```

## API接口文档

### 主Agent接口

#### 健康检查
```
GET http://localhost:18889/health
```
返回所有Agent的健康状态。

#### 每日分析
```
GET http://localhost:18889/analysis/daily
```
执行完整的每日分析流程，返回分析报告。

#### 提交任务
```
POST http://localhost:18889/task/submit
Content-Type: application/json

{
    "task_type": "daily_analysis",
    "params": {}
}
```

### 数据员接口

#### 获取热门板块
```
POST http://localhost:18990/data/hot_sectors
Content-Type: application/json

{
    "days": 3,
    "count": 10
}
```

#### 获取龙虎榜数据
```
POST http://localhost:18990/data/dragon_tiger
Content-Type: application/json

{
    "days": 30
}
```

### 策略员接口

#### 运行策略
```
POST http://localhost:18891/strategy/run
Content-Type: application/json

{
    "stocks": [...],
    "params": {}
}
```

### 回测员接口

#### 运行回测
```
POST http://localhost:18892/backtest/run
Content-Type: application/json

{
    "strategy_data": {...},
    "historical_data": {...}
}
```

### 风控员接口

#### 风险检查
```
POST http://localhost:18893/risk/check
Content-Type: application/json

{
    "trade_data": [...],
    "portfolio": {...}
}
```

## 系统测试

### 运行完整测试
```bash
python3 test_full_system.py
```

### 运行集成测试
```bash
python3 test_system_integration.py
```

### 测试单个Agent
```bash
# 测试数据员
python3 data_collector.py &
curl http://localhost:18990/health

# 测试策略员
python3 strategy_engine_simple.py &
curl http://localhost:18891/health
```

## 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 查看端口占用
lsof -i :18889

# 停止占用进程
kill -9 <pid>
```

#### 2. AkShare连接失败
```bash
# 运行代理配置工具
python3 proxy_config.py

# 选择自动配置代理
```

#### 3. Python依赖问题
```bash
# 更新pip
pip install --upgrade pip

# 重新安装依赖
pip install -r requirements.txt
```

#### 4. Agent启动失败
检查日志文件：
```bash
tail -f logs/data_collector_*.log
tail -f logs/strategy_*.log
```

### 日志文件
- `logs/data_collector_YYYYMMDD.log` - 数据员日志
- `logs/strategy_YYYYMMDD.log` - 策略员日志
- `logs/startup_YYYYMMDD.log` - 启动日志

## 监控和维护

### 系统状态监控
```bash
# 检查所有Agent状态
curl http://localhost:18889/health | jq .

# 检查系统负载
top -n 1 | grep python
```

### 数据清理
```bash
# 清理日志文件（保留最近7天）
find logs/ -name "*.log" -mtime +7 -delete

# 清理缓存数据
rm -rf cache/*
```

### 备份配置
```bash
# 备份配置文件
cp config.py config.py.backup.$(date +%Y%m%d)

# 备份策略配置
cp strategy_config.json strategy_config.json.backup.$(date +%Y%m%d)
```

## 性能优化

### 1. 调整端口配置
如果默认端口冲突，修改 `config.py` 中的端口号。

### 2. 配置代理
对于网络不稳定的情况，使用代理：
```bash
export http_proxy=http://127.0.0.1:1080
export https_proxy=http://127.0.0.1:1080
```

### 3. 调整超时时间
在 `config.py` 中调整网络超时：
```python
NETWORK_CONFIG = {
    "timeout": 30,  # 增加超时时间
    "retry_times": 3
}
```

### 4. 启用缓存
系统默认启用数据缓存，可在配置中调整缓存策略。

## 扩展开发

### 添加新的数据源
1. 在 `data_collector.py` 中添加新的数据获取方法
2. 在配置中启用新的数据源
3. 添加相应的API接口

### 开发新策略
1. 在 `strategy_engine_simple.py` 中添加策略逻辑
2. 在配置中配置策略参数
3. 测试策略效果

### 集成第三方服务
系统支持通过HTTP API集成第三方服务，如：
- 消息通知（Telegram、钉钉）
- 数据存储（MySQL、MongoDB）
- 云服务（AWS、Azure）

## 安全建议

### 1. 修改默认端口
生产环境中建议修改默认端口号。

### 2. 配置防火墙
```bash
# 只允许特定IP访问
iptables -A INPUT -p tcp --dport 18889 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 18889 -j DROP
```

### 3. 使用HTTPS
对于生产环境，建议配置HTTPS：
```python
# 在aiohttp配置中添加SSL
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain('server.crt', 'server.key')
```

### 4. 定期更新
```bash
# 更新代码
git pull origin main

# 更新依赖
pip install --upgrade -r requirements.txt
```

## 联系方式

- 项目仓库: <repository-url>
- 问题反馈: 创建Issue或联系维护者
- 文档更新: 提交Pull Request

---

**最后更新**: 2026-03-03
**版本**: 1.0.0
**维护者**: OpenClaw Team