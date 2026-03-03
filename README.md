# 🐰 万兔福 - 智能股票分析系统

![GitHub](https://img.shields.io/github/license/qhdhao13/1to4-stock)
![GitHub last commit](https://img.shields.io/github/last-commit/qhdhao13/1to4-stock)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Status](https://img.shields.io/badge/status-production%20ready-green)
![System](https://img.shields.io/badge/系统-万兔福-orange)

## 🎯 系统命名含义

**万兔福** - 万物皆可分析，快速如兔，福运相伴

- **万 (万物)**: 代表系统的全面性，覆盖股票分析的各个方面
- **兔 (快速)**: 谐音"two"，代表"一主四辅"架构，寓意敏捷快速
- **福 (福运)**: 寓意给投资者带来好运和稳定收益

## 📊 系统概述

基于OpenClaw框架构建的智能股票分析系统，采用"一主四辅"分布式架构（万兔福架构），实现自动化股票分析、策略执行和风险控制。

## 🏗️ 万兔福系统架构

```
          🐰 万兔福智能分析系统 🐰
          ======================

          ┌─────────────────────┐
          │      🦸 主Agent     │
          │    (万兔福总指挥)    │
          │     端口: 18889     │
          └─────────┬───────────┘
                    │
          ┌─────────┴───────────┐
          │                     │
    ┌─────▼─────┐         ┌─────▼─────┐
    │ 🐇 数据员 │         │ 🐇 策略员 │
    │ (万兔之眼) │         │ (万兔之脑) │
    │  端口: 18990 │         │  端口: 18891 │
    └─────┬─────┘         └─────┬─────┘
          │                     │
          └─────────┬───────────┘
                    │
          ┌─────────┴───────────┐
          │                     │
    ┌─────▼─────┐         ┌─────▼─────┐
    │ 🐇 回测员 │         │ 🐇 风控员 │
    │ (万兔之镜) │         │ (万兔之盾) │
    │  端口: 18892 │         │  端口: 18893 │
    └─────────────┘         └─────────────┘

✨ 万兔福寓意: 万物分析 + 快速敏捷 + 福运相伴 ✨
```

## ✨ 万兔福核心功能

### 🐇 1. 万兔之眼 - 数据采集 (数据员)
- **万物洞察**: 热门板块数据全景扫描
- **快速捕捉**: 龙虎榜数据实时监控
- **全面覆盖**: 实时股票数据多维采集
- **福源广进**: 多数据源支持 (AkShare, TuShare等)

### 🐇 2. 万兔之脑 - 策略分析 (策略员)
- **智能决策**: 基于AI的智能选股策略
- **快速分析**: 技术指标实时计算
- **信号精准**: 买卖信号生成系统
- **福智双全**: 多策略组合优化

### 🐇 3. 万兔之镜 - 历史验证 (回测员)
- **历史映照**: 策略历史表现全面回测
- **胜率验证**: 投资胜率科学计算
- **风险评估**: 收益风险平衡分析
- **福报预测**: 绩效报告智能生成

### 🐇 4. 万兔之盾 - 风险控制 (风控员)
- **仓位守护**: 智能仓位管理系统
- **止损监控**: 动态止损止盈机制
- **风险评分**: 多维风险评分系统
- **福安保障**: 交易审批安全流程

### 🦸 5. 万兔福总指挥 - 任务调度 (主Agent)
- **万物协调**: 五员协同工作流管理
- **快速聚合**: 分析结果智能汇总
- **福报生成**: 专业报告自动生成
- **系统监控**: 全系统健康状态监控

## 🚀 万兔福快速开始

### 环境要求
- Python 3.8+ (万兔福的运行环境)
- pip 包管理工具 (福源管理)

### 安装步骤 - 三步开启万兔福
```bash
# 1. 获取万兔福
git clone https://github.com/qhdhao13/1to4-stock.git
cd 1to4-stock

# 2. 安装福源依赖
pip install aiohttp akshare pandas

# 3. 启动万兔福系统
python3 start_all.py
```

### 快速测试 - 验证万兔福功能
```bash
# 运行万兔福快速测试
python3 quick_test.py

# 运行万兔福完整测试
python3 test_full_system.py
```

## 📖 详细文档

- [部署指南](DEPLOYMENT_GUIDE.md) - 完整部署和配置说明
- [API文档](DEPLOYMENT_GUIDE.md#api接口文档) - 所有接口详细说明
- [故障排除](DEPLOYMENT_GUIDE.md#故障排除) - 常见问题解决方案

## 🔧 配置说明

### 主要配置文件
- `config.py` - 系统核心配置
- `STRATEGY_CONFIG` - 策略参数配置
- `SYSTEM_ARCHITECTURE` - Agent架构配置
- `NETWORK_CONFIG` - 网络通信配置

### 端口配置
```python
# 默认端口配置
主Agent: 18889
数据员: 18990
策略员: 18891
回测员: 18892
风控员: 18893
```

## 🧪 测试验证

### 单元测试
```bash
# 测试单个Agent
python3 data_collector.py &
curl http://localhost:18990/health
```

### 集成测试
```bash
# 测试两个Agent通信
python3 test_system_integration.py
```

### 完整系统测试
```bash
# 测试所有5个Agent
python3 test_full_system.py
```

## 📊 性能指标

- **启动时间**: < 5秒 (所有Agent)
- **响应时间**: < 100ms (健康检查)
- **并发能力**: 支持多任务并行
- **稳定性**: 7x24小时运行

## 🔒 安全特性

- 端口访问控制
- 数据加密传输
- 风险控制机制
- 异常处理系统

## 🛠️ 开发工具

### 代理配置工具
```bash
python3 proxy_config.py
```

### 系统监控
```bash
# 检查所有Agent状态
curl http://localhost:18889/health | jq .
```

### 日志管理
- 自动日志轮转
- 分级日志记录
- 错误追踪系统

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目维护者: qhdhao
- 问题反馈: [创建Issue](https://github.com/qhdhao13/1to4-stock/issues)
- 文档更新: 提交Pull Request

## 🙏 万兔福致谢

感谢以下开源项目为万兔福系统提供支持：
- [OpenClaw](https://github.com/openclaw/openclaw) - 万兔福的基础框架
- [AkShare](https://github.com/akfamily/akshare) - 万兔福的数据之源
- [aiohttp](https://github.com/aio-libs/aiohttp) - 万兔福的快速通道

---

**万兔福系统信息**  
🐰 **系统名称**: 万兔福智能股票分析系统  
📅 **最后更新**: 2026-03-03  
🎯 **版本**: 1.0.0 (万兔福初代)  
✅ **状态**: 生产就绪，福运相伴  

**万兔福愿景**: 让每一位投资者都能享受到智能、快速、福运相伴的投资分析体验！