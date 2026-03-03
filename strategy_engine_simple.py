#!/usr/bin/env python3
"""
简化版策略员 (18891)
负责选股规则、信号生成、交易计划
"""

import asyncio
from aiohttp import web
import json
import logging
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import SYSTEM_ARCHITECTURE, STRATEGY_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StrategyEngineSimple")

class StrategyEngineSimple:
    """简化版策略引擎"""
    
    def __init__(self):
        self.port = SYSTEM_ARCHITECTURE["strategy_engine"]["port"]
        self.name = SYSTEM_ARCHITECTURE["strategy_engine"]["name"]
        
        # 策略配置
        self.filters = STRATEGY_CONFIG['stock_filters']
        
        logger.info(f"🚀 {self.name} 初始化完成 (端口: {self.port})")
    
    async def start_server(self):
        """启动HTTP服务器"""
        app = web.Application()
        
        # 注册路由
        app.router.add_post('/strategy/run', self.handle_run_strategy)
        app.router.add_get('/strategy/signals', self.handle_get_signals)
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
        return web.json_response({
            "status": "healthy",
            "name": self.name,
            "port": self.port,
            "timestamp": datetime.now().isoformat()
        })
    
    async def handle_status(self, request):
        """状态检查"""
        return web.json_response({
            "status": "running",
            "name": self.name,
            "filters": list(self.filters.keys()),
            "timestamp": datetime.now().isoformat()
        })
    
    async def handle_run_strategy(self, request):
        """运行策略"""
        try:
            data = await request.json()
            stocks = data.get('stocks', [])
            params = data.get('params', {})
            
            logger.info(f"📊 运行策略，股票数量: {len(stocks)}")
            
            # 简化策略：随机选择前3只股票
            selected_stocks = stocks[:3] if len(stocks) > 3 else stocks
            
            result = {
                "status": "success",
                "selected_stocks": selected_stocks,
                "count": len(selected_stocks),
                "strategy": "简化随机选择策略",
                "timestamp": datetime.now().isoformat()
            }
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"策略运行错误: {e}")
            return web.json_response({
                "status": "error",
                "error": str(e)
            }, status=500)
    
    async def handle_get_signals(self, request):
        """获取信号"""
        # 示例信号数据
        signals = [
            {"symbol": "000001", "name": "平安银行", "signal": "BUY", "confidence": 0.75},
            {"symbol": "000002", "name": "万科A", "signal": "HOLD", "confidence": 0.60},
            {"symbol": "000858", "name": "五粮液", "signal": "SELL", "confidence": 0.80}
        ]
        
        return web.json_response({
            "status": "success",
            "signals": signals,
            "count": len(signals),
            "timestamp": datetime.now().isoformat()
        })

async def main():
    """主函数"""
    engine = StrategyEngineSimple()
    await engine.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 收到中断信号，正在关闭策略员...")
    except Exception as e:
        logger.error(f"策略员运行异常: {str(e)}")
        sys.exit(1)