#!/usr/bin/env python3
"""
简化版主Agent (18889)
负责任务调度、结果聚合、报告生成
"""

import asyncio
import aiohttp
from aiohttp import web
import json
import logging
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import SYSTEM_ARCHITECTURE, STRATEGY_CONFIG, NETWORK_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MasterAgentSimple")

class MasterAgentSimple:
    """简化版主Agent"""
    
    def __init__(self):
        self.port = SYSTEM_ARCHITECTURE["master"]["port"]
        self.name = SYSTEM_ARCHITECTURE["master"]["name"]
        
        # 其他Agent的URL
        self.agent_urls = {
            "data_collector": "http://localhost:18990",
            "strategy_engine": "http://localhost:18891",
            "backtester": "http://localhost:18892",
            "risk_manager": "http://localhost:18893"
        }
        
        logger.info(f"🚀 {self.name} 初始化完成 (端口: {self.port})")
    
    async def start_server(self):
        """启动HTTP服务器"""
        app = web.Application()
        
        # 注册路由
        app.router.add_post('/task/submit', self.handle_submit_task)
        app.router.add_get('/task/result', self.handle_get_result)
        app.router.add_get('/analysis/daily', self.handle_daily_analysis)
        app.router.add_get('/status', self.handle_status)
        app.router.add_get('/health', self.handle_health)
        
        # 启动服务器
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"🌐 {self.name} HTTP服务器已启动: http://localhost:{self.port}")
        
        # 保持运行
        await asyncio.Future()
    
    async def handle_health(self, request):
        """健康检查"""
        # 检查所有Agent的健康状态
        agent_status = {}
        
        for agent_name, url in self.agent_urls.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/health", timeout=5) as response:
                        if response.status == 200:
                            agent_status[agent_name] = "healthy"
                        else:
                            agent_status[agent_name] = f"unhealthy (HTTP {response.status})"
            except Exception as e:
                agent_status[agent_name] = f"unreachable ({str(e)})"
        
        return web.json_response({
            "status": "healthy",
            "name": self.name,
            "port": self.port,
            "agent_status": agent_status,
            "timestamp": datetime.now().isoformat()
        })
    
    async def handle_status(self, request):
        """状态检查"""
        return web.json_response({
            "status": "running",
            "name": self.name,
            "agents_configured": len(self.agent_urls),
            "timestamp": datetime.now().isoformat()
        })
    
    async def handle_submit_task(self, request):
        """提交任务"""
        try:
            data = await request.json()
            task_type = data.get('task_type', 'daily_analysis')
            params = data.get('params', {})
            
            logger.info(f"📋 提交任务: {task_type}")
            
            # 根据任务类型执行不同的流程
            if task_type == "daily_analysis":
                result = await self._run_daily_analysis(params)
            elif task_type == "backtest":
                result = await self._run_backtest(params)
            else:
                result = {"status": "error", "error": f"未知任务类型: {task_type}"}
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"任务提交错误: {e}")
            return web.json_response({
                "status": "error",
                "error": str(e)
            }, status=500)
    
    async def _run_daily_analysis(self, params):
        """运行每日分析"""
        logger.info("🔍 开始每日分析流程...")
        
        results = {}
        
        try:
            # 1. 获取数据
            logger.info("  1. 从数据员获取数据...")
            async with aiohttp.ClientSession() as session:
                data_response = await session.post(
                    f"{self.agent_urls['data_collector']}/data/hot_sectors",
                    json={"days": 3, "count": 10},
                    timeout=10
                )
                if data_response.status == 200:
                    data_result = await data_response.json()
                    results['data'] = data_result
                    logger.info(f"     获取到 {data_result.get('count', 0)} 个板块数据")
                else:
                    results['data'] = {"error": f"HTTP {data_response.status}"}
            
            # 2. 运行策略
            logger.info("  2. 运行策略分析...")
            if 'data' in results and 'hot_sectors' in results['data']:
                stocks = []
                for sector in results['data']['hot_sectors']:
                    stocks.append({
                        "symbol": sector.get('code', ''),
                        "name": sector.get('name', ''),
                        "gain": sector.get('gain', 0)
                    })
                
                async with aiohttp.ClientSession() as session:
                    strategy_response = await session.post(
                        f"{self.agent_urls['strategy_engine']}/strategy/run",
                        json={"stocks": stocks, "params": {}},
                        timeout=10
                    )
                    if strategy_response.status == 200:
                        strategy_result = await strategy_response.json()
                        results['strategy'] = strategy_result
                        logger.info(f"     策略选中 {strategy_result.get('count', 0)} 只股票")
                    else:
                        results['strategy'] = {"error": f"HTTP {strategy_response.status}"}
            
            # 3. 风险检查
            logger.info("  3. 进行风险检查...")
            trade_data = results.get('strategy', {}).get('selected_stocks', [])
            async with aiohttp.ClientSession() as session:
                risk_response = await session.post(
                    f"{self.agent_urls['risk_manager']}/risk/check",
                    json={"trade_data": trade_data, "portfolio": {}, "market_condition": "normal"},
                    timeout=10
                )
                if risk_response.status == 200:
                    risk_result = await risk_response.json()
                    results['risk'] = risk_result
                    logger.info(f"     风险评分: {risk_result.get('risk_score', 'N/A')}")
                else:
                    results['risk'] = {"error": f"HTTP {risk_response.status}"}
            
            # 生成报告
            report = self._generate_daily_report(results)
            
            return {
                "status": "success",
                "task_type": "daily_analysis",
                "results": results,
                "report": report,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"每日分析错误: {e}")
            return {
                "status": "error",
                "error": str(e),
                "results": results
            }
    
    def _generate_daily_report(self, results):
        """生成每日报告"""
        report = {
            "title": "股票系统每日分析报告",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": "",
            "recommendations": [],
            "risk_assessment": "中等"
        }
        
        # 根据结果生成报告
        if 'strategy' in results and 'selected_stocks' in results['strategy']:
            stocks = results['strategy']['selected_stocks']
            report['summary'] = f"今日推荐 {len(stocks)} 只股票"
            report['recommendations'] = [f"关注 {s.get('name', '')} ({s.get('symbol', '')})" for s in stocks[:3]]
        
        if 'risk' in results:
            risk_score = results['risk'].get('risk_score', 50)
            if risk_score < 30:
                report['risk_assessment'] = "低"
            elif risk_score < 70:
                report['risk_assessment'] = "中等"
            else:
                report['risk_assessment'] = "高"
                report['recommendations'].append("市场风险较高，建议谨慎操作")
        
        return report
    
    async def _run_backtest(self, params):
        """运行回测"""
        logger.info("📈 运行回测流程...")
        
        # 这里可以添加完整的回测流程
        return {
            "status": "success",
            "task_type": "backtest",
            "message": "回测功能待实现",
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_get_result(self, request):
        """获取任务结果"""
        task_id = request.query.get('task_id', 'test')
        
        return web.json_response({
            "status": "success",
            "task_id": task_id,
            "result": {
                "progress": 100,
                "status": "completed",
                "message": "任务执行完成"
            },
            "timestamp": datetime.now().isoformat()
        })
    
    async def handle_daily_analysis(self, request):
        """每日分析"""
        result = await self._run_daily_analysis({})
        return web.json_response(result)

async def main():
    """主函数"""
    master_agent = MasterAgentSimple()
    await master_agent.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 收到中断信号，正在关闭主Agent...")
    except Exception as e:
        logger.error(f"主Agent运行异常: {str(e)}")
        sys.exit(1)