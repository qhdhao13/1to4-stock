#!/usr/bin/env python3
"""
主Agent (18789) - 总指挥
负责任务调度、结果聚合、报告生成
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import SYSTEM_ARCHITECTURE, STRATEGY_CONFIG, NETWORK_CONFIG, get_agent_url, get_report_filename

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/master_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MasterAgent")

class MasterAgent:
    """主Agent - 总指挥"""
    
    def __init__(self):
        self.port = SYSTEM_ARCHITECTURE["master"]["port"]
        self.name = SYSTEM_ARCHITECTURE["master"]["name"]
        self.start_time = SYSTEM_ARCHITECTURE["master"]["start_time"]
        self.check_interval = SYSTEM_ARCHITECTURE["master"]["check_interval"]
        
        # 任务状态
        self.tasks = {}
        self.results = {}
        self.stock_pool = []
        
        # HTTP客户端
        self.session = None
        
        logger.info(f"🚀 {self.name} 初始化完成 (端口: {self.port})")
    
    async def start_server(self):
        """启动HTTP服务器"""
        from aiohttp import web
        
        app = web.Application()
        
        # 注册路由
        app.router.add_post('/task/submit', self.handle_submit_task)
        app.router.add_get('/task/result', self.handle_get_result)
        app.router.add_get('/status', self.handle_status)
        app.router.add_get('/health', self.handle_health)
        
        # 启动服务器
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        logger.info(f"🌐 {self.name} HTTP服务器已启动: http://localhost:{self.port}")
        
        # 保持服务器运行
        await asyncio.Event().wait()
    
    async def handle_submit_task(self, request):
        """处理任务提交"""
        try:
            data = await request.json()
            task_type = data.get('type', 'daily_analysis')
            
            logger.info(f"📨 收到任务: {task_type}")
            
            # 执行任务
            if task_type == 'daily_analysis':
                result = await self.run_daily_analysis()
            elif task_type == 'manual_analysis':
                result = await self.run_manual_analysis(data.get('params', {}))
            else:
                result = {"error": f"未知任务类型: {task_type}"}
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"任务处理失败: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_get_result(self, request):
        """获取任务结果"""
        task_id = request.query.get('task_id', 'latest')
        
        if task_id == 'latest':
            result = self.results.get('latest', {})
        else:
            result = self.results.get(task_id, {})
        
        return web.json_response(result)
    
    async def handle_status(self, request):
        """获取系统状态"""
        status = {
            "agent": self.name,
            "port": self.port,
            "status": "running",
            "tasks": len(self.tasks),
            "stock_pool_size": len(self.stock_pool),
            "last_update": datetime.now().isoformat(),
        }
        return web.json_response(status)
    
    async def handle_health(self, request):
        """健康检查"""
        return web.json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})
    
    async def run_daily_analysis(self):
        """执行每日分析任务"""
        logger.info("🔄 开始执行每日分析任务...")
        
        try:
            # 1. 调用数据员获取数据
            data_result = await self.call_agent('data_collector', 'get_hot_sectors', {})
            logger.info(f"📊 数据员返回: {len(data_result.get('hot_sectors', []))}个热门板块")
            
            # 2. 调用策略员生成选股信号
            strategy_params = {
                "hot_sectors": data_result.get('hot_sectors', []),
                "filters": STRATEGY_CONFIG['stock_filters']
            }
            strategy_result = await self.call_agent('strategy_engine', 'run_strategy', strategy_params)
            logger.info(f"🎯 策略员返回: {len(strategy_result.get('signals', []))}个选股信号")
            
            # 3. 调用回测员验证信号
            backtest_params = {
                "signals": strategy_result.get('signals', []),
                "period": STRATEGY_CONFIG['backtest']['period']
            }
            backtest_result = await self.call_agent('backtester', 'run_backtest', backtest_params)
            logger.info(f"📈 回测员返回: {len(backtest_result.get('valid_signals', []))}个有效信号")
            
            # 4. 调用风控员生成交易计划
            risk_params = {
                "signals": backtest_result.get('valid_signals', []),
                "capital": STRATEGY_CONFIG['capital'],
                "position_rules": {
                    "max_positions": STRATEGY_CONFIG['max_positions'],
                    "max_portfolio_size": STRATEGY_CONFIG['max_portfolio_size'],
                    "initial_position": STRATEGY_CONFIG['initial_position'],
                }
            }
            risk_result = await self.call_agent('risk_manager', 'check_risk', risk_params)
            logger.info(f"🛡️ 风控员返回: {len(risk_result.get('trading_plans', []))}个交易计划")
            
            # 5. 聚合结果生成报告
            final_result = await self.generate_final_report(
                data_result, strategy_result, backtest_result, risk_result
            )
            
            # 6. 保存结果
            self.stock_pool = final_result.get('stock_pool', [])
            self.results['latest'] = final_result
            
            logger.info(f"✅ 每日分析任务完成! 生成{len(self.stock_pool)}只股票的交易计划")
            
            return final_result
            
        except Exception as e:
            logger.error(f"每日分析任务失败: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    async def run_manual_analysis(self, params):
        """执行手动分析任务"""
        logger.info(f"🔄 开始执行手动分析任务: {params}")
        
        # 这里可以根据params执行特定的分析
        # 暂时返回一个示例结果
        return {
            "status": "success",
            "type": "manual_analysis",
            "params": params,
            "message": "手动分析任务已接收",
            "timestamp": datetime.now().isoformat()
        }
    
    async def call_agent(self, agent_name: str, endpoint: str, params: Dict) -> Dict:
        """调用其他Agent"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        
        url = get_agent_url(agent_name, endpoint)
        
        try:
            logger.debug(f"📞 调用 {agent_name}.{endpoint}: {url}")
            
            async with self.session.post(url, json=params, timeout=NETWORK_CONFIG['timeout']) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"✅ {agent_name} 响应成功")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ {agent_name} 响应失败: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}"}
                    
        except asyncio.TimeoutError:
            logger.error(f"⏰ {agent_name} 调用超时")
            return {"error": "请求超时"}
        except Exception as e:
            logger.error(f"❌ {agent_name} 调用异常: {str(e)}")
            return {"error": str(e)}
    
    async def generate_final_report(self, data_result, strategy_result, backtest_result, risk_result):
        """生成最终报告"""
        logger.info("📝 生成最终报告...")
        
        # 获取交易计划
        trading_plans = risk_result.get('trading_plans', [])
        
        # 生成报告内容
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_time = datetime.now().strftime("%H:%M:%S")
        
        report_content = f"""# 【OpenClaw 龙虎榜均线粘合选股・今日交易计划】
生成时间: {report_date} {report_time}
策略名称: {STRATEGY_CONFIG['name']}
初始资金: {STRATEGY_CONFIG['capital']:,}元
总仓位上限: {STRATEGY_CONFIG['max_portfolio_size']*100}%
单票仓位上限: {STRATEGY_CONFIG['max_single_position']*100}%

## 📊 市场概况
- 热门板块数量: {len(data_result.get('hot_sectors', []))}
- 原始选股信号: {len(strategy_result.get('signals', []))}
- 回测有效信号: {len(backtest_result.get('valid_signals', []))}
- 最终交易计划: {len(trading_plans)}

## 🎯 今日交易计划
"""
        
        if trading_plans:
            for i, plan in enumerate(trading_plans, 1):
                report_content += f"""
### 计划{i}: {plan.get('name', 'N/A')} ({plan.get('code', 'N/A')})
**热门板块**: {plan.get('sector', 'N/A')}
**龙虎榜**: {plan.get('dragon_tiger', '否')}
**当前股价**: {plan.get('current_price', 'N/A')}
**2025.1.1至今涨幅**: {plan.get('total_gain', 'N/A')}
**均线形态**: {plan.get('ma_pattern', 'N/A')}

**买入区间**: {plan.get('buy_range', 'N/A')}
**补仓价(跌2%)**: {plan.get('add_price', 'N/A')}
**止盈价(+5%)**: {plan.get('take_profit_price', 'N/A')}
**止损价(-8%)**: {plan.get('stop_loss_price', 'N/A')}

**首次仓位**: {STRATEGY_CONFIG['initial_position']*100}%
**补仓后上限**: {STRATEGY_CONFIG['max_single_position']*100}%
**持股周期**: ≤{STRATEGY_CONFIG['max_holding_days']}天

**入选逻辑**: {plan.get('logic', 'N/A')}
**风险提示**: {plan.get('risk', 'N/A')}
"""
        else:
            report_content += "\n⚠️ 今日无符合条件的交易计划，建议观望。\n"
        
        # 添加策略说明
        report_content += f"""
## 📋 策略规则摘要
1. **板块条件**: 属于当前市场热门板块（近3日涨幅前20名）
2. **龙虎榜条件**: 近1个月内上过龙虎榜
3. **股价条件**: 股价 ≤ 50元
4. **涨幅限制**: 2025.1.1至今累计涨幅 ≤ 30%
5. **均线形态**: 2025年均线粘合 → 2026年向上发散
6. **基础过滤**: 非ST、市值≥50亿、日均成交额≥2亿

## ⚠️ 风险提示
- 股市有风险，投资需谨慎
- 本报告仅供参考，不构成投资建议
- 历史表现不代表未来收益
- 请根据自身风险承受能力进行投资
- 严格执行止损纪律（最大亏损≤8%）
"""
        
        # 保存报告文件
        report_filename = get_report_filename()
        report_path = os.path.join("reports", report_filename)
        
        os.makedirs("reports", exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"📄 报告已保存至: {report_path}")
        
        return {
            "status": "success",
            "report_path": report_path,
            "report_content": report_content[:1000] + "...",  # 只返回前1000字符
            "stock_pool": trading_plans,
            "summary": {
                "hot_sectors": len(data_result.get('hot_sectors', [])),
                "raw_signals": len(strategy_result.get('signals', [])),
                "valid_signals": len(backtest_result.get('valid_signals', [])),
                "trading_plans": len(trading_plans),
                "generated_at": datetime.now().isoformat()
            }
        }
    
    async def schedule_daily_task(self):
        """定时执行每日任务"""
        logger.info(f"⏰ 定时任务调度器启动，每日{self.start_time}执行")
        
        while True:
            now = datetime.now()
            target_time = datetime.strptime(self.start_time, "%H:%M:%S").time()
            
            # 计算下一次执行时间
            next_run = datetime.combine(now.date(), target_time)
            if now.time() > target_time:
                next_run += timedelta(days=1)
            
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"⏳ 下次执行时间: {next_run} (等待{wait_seconds:.0f}秒)")
            
            await asyncio.sleep(wait_seconds)
            
            # 执行任务
            logger.info("🔔 定时任务触发，开始执行每日分析...")
            try:
                await self.run_daily_analysis()
            except Exception as e:
                logger.error(f"定时任务执行失败: {str(e)}")
            
            # 等待一天
            await asyncio.sleep(86400 - 300)  # 减去5分钟容差
    
    async def run(self):
        """运行主Agent"""
        logger.info(f"🚀 {self.name} 开始运行...")
        
        # 创建任务
        server_task = asyncio.create_task(self.start_server())
        scheduler_task = asyncio.create_task(self.schedule_daily_task())
        
        # 等待任务完成（实际上会一直运行）
        await asyncio.gather(server_task, scheduler_task)

async def main():
    """主函数"""
    agent = MasterAgent()
    await agent.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 收到中断信号，正在关闭主Agent...")
    except Exception as e:
        logger.error(f"主Agent运行异常: {str(e)}")
        sys.exit(1)