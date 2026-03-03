#!/usr/bin/env python3
"""
简化版风控员 (18893)
负责仓位管理、止损监控、风险过滤
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
logger = logging.getLogger("RiskManagerSimple")

class RiskManagerSimple:
    """简化版风控员"""
    
    def __init__(self):
        self.port = SYSTEM_ARCHITECTURE["risk_manager"]["port"]
        self.name = SYSTEM_ARCHITECTURE["risk_manager"]["name"]
        
        # 风控配置
        self.risk_config = {
            "max_position_size": STRATEGY_CONFIG.get("max_single_position", 0.3),
            "stop_loss": STRATEGY_CONFIG.get("stop_loss", 0.08),
            "take_profit": STRATEGY_CONFIG.get("take_profit", 0.05),
            "max_portfolio_risk": 0.6,
            "min_cash_ratio": 0.4
        }
        
        logger.info(f"🚀 {self.name} 初始化完成 (端口: {self.port})")
    
    async def start_server(self):
        """启动HTTP服务器"""
        app = web.Application()
        
        # 注册路由
        app.router.add_post('/risk/check', self.handle_check_risk)
        app.router.add_get('/risk/position', self.handle_get_position)
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
            "risk_config": self.risk_config,
            "timestamp": datetime.now().isoformat()
        })
    
    async def handle_status(self, request):
        """状态检查"""
        return web.json_response({
            "status": "running",
            "name": self.name,
            "risk_level": "medium",
            "timestamp": datetime.now().isoformat()
        })
    
    async def handle_check_risk(self, request):
        """检查风险"""
        try:
            data = await request.json()
            trade_data = data.get('trade_data', {})
            portfolio = data.get('portfolio', {})
            market_condition = data.get('market_condition', "normal")
            
            logger.info(f"🔍 检查风险，交易数据: {len(trade_data)}条")
            
            # 简化风险检查逻辑
            risk_checks = {
                "position_size_ok": True,
                "stop_loss_set": True,
                "portfolio_diversified": True,
                "cash_reserve_sufficient": True,
                "market_risk_acceptable": market_condition != "high_volatility",
                "leverage_within_limit": True
            }
            
            # 计算风险评分 (0-100，越低越好)
            risk_score = 25 if market_condition == "normal" else 65
            
            recommendations = []
            if risk_score > 50:
                recommendations.append("建议降低仓位，增加现金储备")
            if market_condition == "high_volatility":
                recommendations.append("市场波动大，建议谨慎操作")
            
            result = {
                "status": "success",
                "risk_checks": risk_checks,
                "risk_score": risk_score,
                "risk_level": "low" if risk_score < 30 else "medium" if risk_score < 70 else "high",
                "recommendations": recommendations,
                "approved": risk_score < 70,
                "timestamp": datetime.now().isoformat()
            }
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"风险检查错误: {e}")
            return web.json_response({
                "status": "error",
                "error": str(e)
            }, status=500)
    
    async def handle_get_position(self, request):
        """获取仓位信息"""
        # 示例仓位信息
        positions = [
            {"symbol": "000001", "name": "平安银行", "quantity": 1000, "avg_price": 12.5, "current_price": 13.2, "profit": 700},
            {"symbol": "000858", "name": "五粮液", "quantity": 500, "avg_price": 150.3, "current_price": 148.7, "profit": -800},
            {"symbol": "300750", "name": "宁德时代", "quantity": 200, "avg_price": 180.5, "current_price": 195.2, "profit": 2940}
        ]
        
        total_value = sum(p["quantity"] * p["current_price"] for p in positions)
        total_profit = sum(p["profit"] for p in positions)
        
        position_info = {
            "positions": positions,
            "total_positions": len(positions),
            "total_value": total_value,
            "total_profit": total_profit,
            "portfolio_risk": 0.42,
            "cash_ratio": 0.55,
            "timestamp": datetime.now().isoformat()
        }
        
        return web.json_response({
            "status": "success",
            "position_info": position_info,
            "timestamp": datetime.now().isoformat()
        })

async def main():
    """主函数"""
    risk_manager = RiskManagerSimple()
    await risk_manager.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 收到中断信号，正在关闭风控员...")
    except Exception as e:
        logger.error(f"风控员运行异常: {str(e)}")
        sys.exit(1)