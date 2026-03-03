# 部署指南

## 🚀 快速部署

### 环境要求
- **操作系统**：Linux/macOS/Windows (推荐Linux)
- **Python版本**：3.8 或更高版本
- **内存**：至少 2GB RAM
- **磁盘空间**：至少 1GB 可用空间
- **网络**：可访问互联网（获取数据）

### 步骤1：克隆代码
```bash
git clone https://github.com/qhdhao13/1to4-stock.git
cd 1to4-stock
```

### 步骤2：安装依赖
```bash
pip install -r requirements.txt
```

如果没有requirements.txt，手动安装：
```bash
pip install akshare==1.18.30 pandas numpy aiohttp
```

### 步骤3：创建必要目录
```bash
mkdir -p logs data reports cache
```

### 步骤4：测试安装
```bash
python3 run_test.py
```

## 🔧 详细部署配置

### 配置文件说明
系统配置文件位于 `config.py`，主要包含以下配置：

#### 系统架构配置
```python
SYSTEM_ARCHITECTURE = {
    "master_agent": {"port": 18789, "name": "主Agent-总指挥"},
    "data_collector": {"port": 18790, "name": "辅1-数据员"},
    "strategy_engine": {"port": 18791, "name": "辅2-策略员"},
    "backtester": {"port": 18792, "name": "辅3-回测员"},
    "risk_manager": {"port": 18793, "name": "辅4-风控员"},
}
```

#### 策略参数配置
```python
STRATEGY_CONFIG = {
    "capital": 1000000,  # 初始资金100万
    "max_portfolio_size": 0.6,  # 总仓位≤60%
    "max_single_position": 0.3,  # 单票≤30%
    "initial_position": 0.2,  # 首次建仓20%
    "add_position_size": 0.1,  # 补仓10%
    "take_profit": 0.05,  # 止盈5%
    "stop_loss": 0.08,  # 止损8%
    "max_holding_days": 7,  # 最长持有7天
    "auto_sell_days": 5,  # 5天不涨自动卖出
}
```

### 数据源配置

#### AkShare配置（默认）
AkShare无需额外配置，但需要注意：
- 确保网络可访问 `akshare` 数据源
- 如遇网络问题，可设置代理：
  ```bash
  export http_proxy=http://your-proxy:port
  export https_proxy=http://your-proxy:port
  ```

#### Tushare Pro配置（备用）
如需使用Tushare Pro作为备用数据源：
1. 安装Tushare Pro：
   ```bash
   pip install tushare
   ```
2. 在代码中配置Token：
   ```python
   import tushare as ts
   ts.set_token('97f10d5f7b6ddedae78d3293caf73a020ab83b00c199883847a9ad5c')
   ```

## 🏃‍♂️ 运行方式

### 方式一：一键启动（推荐）
```bash
python3 start_all.py
```

启动过程：
1. 检查端口占用
2. 按依赖顺序启动各Agent
3. 检查健康状态
4. 进入监控模式

### 方式二：手动启动
```bash
# 终端1：启动数据员
python3 data_collector.py

# 终端2：启动策略员
python3 strategy_engine.py

# 终端3：启动回测员
python3 backtester.py

# 终端4：启动风控员
python3 risk_manager.py

# 终端5：启动主Agent
python3 master_agent.py
```

### 方式三：后台运行
```bash
# 使用nohup后台运行
nohup python3 data_collector.py > logs/data_collector.log 2>&1 &
nohup python3 strategy_engine.py > logs/strategy_engine.log 2>&1 &
nohup python3 backtester.py > logs/backtester.log 2>&1 &
nohup python3 risk_manager.py > logs/risk_manager.log 2>&1 &
nohup python3 master_agent.py > logs/master_agent.log 2>&1 &

# 查看进程
ps aux | grep python

# 查看日志
tail -f logs/master_agent.log
```

## ⏰ 定时任务配置

### 每日自动运行
系统设计为每日9:25自动执行分析任务。

#### Linux (cron)
```bash
# 编辑crontab
crontab -e

# 添加以下行（每日9:25运行）
25 9 * * * cd /path/to/1to4-stock && python3 -c "import requests; requests.post('http://localhost:18789/task/submit', json={'type': 'daily_analysis'})"

# 保存并退出
```

#### macOS (launchd)
创建 `~/Library/LaunchAgents/com.1to4stock.daily.plist`：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.1to4stock.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-c</string>
        <string>import requests; requests.post('http://localhost:18789/task/submit', json={'type': 'daily_analysis'})</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/1to4-stock</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>25</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/path/to/1to4-stock/logs/cron.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/1to4-stock/logs/cron_error.log</string>
</dict>
</plist>
```

加载任务：
```bash
launchctl load ~/Library/LaunchAgents/com.1to4stock.daily.plist
```

#### Windows (任务计划程序)
1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器：每日9:25
4. 操作：启动程序
   - 程序：`python.exe`
   - 参数：`-c "import requests; requests.post('http://localhost:18789/task/submit', json={'type': 'daily_analysis'})"`
   - 起始于：`C:\path\to\1to4-stock`

## 📊 监控与维护

### 健康检查
```bash
# 检查所有Agent
curl http://localhost:18789/health
curl http://localhost:18790/health
curl http://localhost:18791/health
curl http://localhost:18792/health
curl http://localhost:18793/health

# 批量检查脚本
#!/bin/bash
for port in 18789 18790 18791 18792 18793; do
    if curl -s http://localhost:$port/health | grep -q '"status":"healthy"'; then
        echo "✅ 端口 $port: 健康"
    else
        echo "❌ 端口 $port: 异常"
    fi
done
```

### 日志管理
系统日志按日期分割：
```
logs/
├── master_agent_20260301.log
├── data_collector_20260301.log
├── strategy_engine_20260301.log
├── backtester_20260301.log
├── risk_manager_20260301.log
└── startup_20260301.log
```

#### 日志轮转配置（Linux）
```bash
# 安装logrotate
sudo apt-get install logrotate

# 创建配置文件 /etc/logrotate.d/1to4stock
/path/to/1to4-stock/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) $(whoami)
}
```

### 性能监控

#### 内存监控
```bash
# 查看各Agent内存使用
ps aux | grep python | grep -v grep | awk '{print $2, $4, $11}'

# 监控脚本
#!/bin/bash
while true; do
    clear
    echo "=== 1to4股票系统监控 ==="
    echo "时间: $(date)"
    echo ""
    
    # 进程状态
    echo "进程状态:"
    ps aux | grep -E "(data_collector|strategy_engine|backtester|risk_manager|master_agent)" | grep -v grep
    
    # 端口状态
    echo ""
    echo "端口状态:"
    for port in 18789 18790 18791 18792 18793; do
        if nc -z localhost $port 2>/dev/null; then
            echo "✅ 端口 $port: 监听中"
        else
            echo "❌ 端口 $port: 未监听"
        fi
    done
    
    sleep 10
done
```

#### 磁盘空间监控
```bash
# 检查日志和缓存大小
du -sh logs/ data/ cache/ reports/

# 自动清理旧日志（保留最近30天）
find logs/ -name "*.log" -mtime +30 -delete
find cache/ -name "*.cache" -mtime +7 -delete
```

## 🐳 Docker部署（可选）

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制代码
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建目录
RUN mkdir -p logs data reports cache

# 暴露端口
EXPOSE 18789 18790 18791 18792 18793

# 启动命令
CMD ["python3", "start_all.py"]
```

### Docker Compose配置
```yaml
version: '3.8'

services:
  stock-system:
    build: .
    ports:
      - "18789:18789"
      - "18790:18790"
      - "18791:18791"
      - "18792:18792"
      - "18793:18793"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./reports:/app/reports
      - ./cache:/app/cache
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
```

### 构建和运行
```bash
# 构建镜像
docker build -t 1to4-stock .

# 运行容器
docker run -d \
  --name 1to4-stock \
  -p 18789:18789 \
  -p 18790:18790 \
  -p 18791:18791 \
  -p 18792:18792 \
  -p 18793:18793 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/cache:/app/cache \
  1to4-stock

# 使用Docker Compose
docker-compose up -d
```

## 🔒 安全配置

### 防火墙配置
```bash
# 只允许本地访问
sudo ufw allow from 127.0.0.1 to any port 18789:18793
sudo ufw deny from any to any port 18789:18793
```

### 进程权限
```bash
# 创建专用用户
sudo useradd -r -s /bin/false stockbot

# 修改文件权限
sudo chown -R stockbot:stockbot /path/to/1to4-stock
sudo chmod 750 /path/to/1to4-stock

# 以专用用户运行
sudo -u stockbot python3 start_all.py
```

## 🚨 故障排除

### 常见问题

#### 问题1：端口被占用
```bash
# 检查端口占用
sudo lsof -i :18789

# 杀死占用进程
sudo kill -9 <PID>

# 或修改config.py中的端口号
```

#### 问题2：AkShare连接失败
```bash
# 测试AkShare连接
python3 -c "import akshare as ak; print(ak.__version__)"

# 设置代理
export http_proxy=http://your-proxy:port
export https_proxy=http://your-proxy:port
```

#### 问题3：内存不足
```bash
# 查看内存使用
free -h

# 限制缓存大小
# 修改config.py中的缓存配置
CACHE_CONFIG = {
    "max_memory_cache": 100,  # MB
    "max_disk_cache": 1000,   # MB
}
```

#### 问题4：日志文件过大
```bash
# 清理旧日志
find logs/ -name "*.log" -size +100M -delete

# 配置日志轮转
# 参考上面的logrotate配置
```

### 调试模式
```bash
# 启用调试日志
export LOG_LEVEL=DEBUG

# 重新启动系统
python3 start_all.py

# 查看详细日志
tail -f logs/master_agent.log | grep -E "(DEBUG|ERROR)"
```

## 🔄 更新与升级

### 代码更新
```bash
# 拉取最新代码
git pull origin main

# 重新安装依赖
pip install -r requirements.txt --upgrade

# 重启系统
pkill -f "python3.*(data_collector|strategy_engine|backtester|risk_manager|master_agent)"
python3 start_all.py
```

### 数据迁移
```bash
# 备份旧数据
tar -czf backup_$(date +%Y%m%d).tar.gz data/ cache/ reports/

# 清理旧数据（可选）
rm -rf data/* cache/* reports/*
```

## 📞 支持与帮助

### 获取帮助
1. 查看日志文件：`logs/` 目录
2. 运行测试脚本：`python3 run_test.py`
3. 检查系统状态：`curl http://localhost:18789/status`

### 报告问题
如遇问题，请提供：
1. 操作系统和Python版本
2. 错误日志内容
3. 复现步骤
4. 相关配置文件

### 社区支持
- GitHub Issues: https://github.com/qhdhao13/1to4-stock/issues
- 文档: https://github.com/qhdhao13/1to4-stock/tree/main/docs

---

**部署完成提示**：系统部署完成后，可通过 `python3 run_test.py` 验证所有组件是否正常工作。建议首次运行后观察日志24小时，确保定时任务正常执行。