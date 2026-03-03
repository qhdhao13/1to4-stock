#!/usr/bin/env python3
"""
辅4：风控员 (18793)
负责仓位管理、止损监控、风险过滤
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import SYSTEM_ARCHITECTURE, STRATEGY_CONFIG, NETWORK_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/risk_manager_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RiskManager")

class RiskManager:
    """风控员 - 负责仓位管理和风险控制"""
    
    def __init__(self):
        self.port = SYSTEM_ARCHITECTURE["risk_manager"]["port"]
        self.name = SYSTEM_ARCHITECTURE["risk_manager"]["name"]
        
        # 风控配置
        self.capital = STRATEGY_CONFIG['capital']
        self.max_positions = STRATEGY_CONFIG['max_positions']
        self.max_portfolio_size = STRATEGY_CONFIG['max_portfolio_size']
        self.max_single_position = STRATEGY_CONFIG['max_single_position']
        self.initial_position = STRATEGY_CONFIG['initial_position']
        self.add_position_size = STRATEGY_CONFIG['add_position_size']
        self.take_profit = STRATEGY_CONFIG['take_profit']
        self.stop_loss = STRATEGY_CONFIG['stop_loss']
        self.max_holding_days = STRATEGY_CONFIG['max_holding_days']
        
        # 持仓记录
        self.positions = {}  # {symbol: position_info}
        self.trading_plans = []
        
        logger.info(f"🚀 {self.name} 初始化完成 (端口: {self.port})")
        logger.info(f"💰 初始资金: {self.capital:,}元")
        logger.info(f"📊 仓位限制: 总仓≤{self.max_portfolio_size*100}%, 单票≤{self.max_single_position*100}%")
        logger.info(f"🛡️ 风控规则: 止盈{self.take_profit*100}%, 止损{self.stop_loss*100}%")
    
    async def start_server(self):
        """启动HTTP服务器"""
        from aiohttp import web
        
        app = web.Application()
        
        # 注册路由
        app.router.add_post('/risk/check', self.handle_check_risk)
        app.router.add_post('/risk/position', self.handle_get_position)
        app.router.add_post('/risk/update', self.handle_update_position)
        app.router.add_get('/risk/status', self.handle_status)
        app.router.add_get('/risk/health', self.handle_health)
        
        # 启动服务器
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        logger.info(f"🌐 {self.name} HTTP服务器已启动: http://localhost:{self.port}")
        
        # 保持服务器运行
        await asyncio.Event().wait()
    
    async def handle_check_risk(self, request):
        """处理风险检查请求"""
        try:
            data = await request.json()
            signals = data.get('signals', [])
            capital = data.get('capital', self.capital)
            position_rules = data.get('position_rules', {})
            
            logger.info(f"🛡️ 风险检查: {len(signals)}个信号, 资金{capital:,}元")
            
            # 检查风险并生成交易计划
            result = await self.check_risk_and_generate_plans(signals, capital, position_rules)
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"风险检查失败: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_get_position(self, request):
        """获取持仓信息"""
        try:
            data = await request.json()
            symbol = data.get('symbol', 'all')
            
            if symbol == 'all':
                positions = self.positions
            else:
                positions = {symbol: self.positions.get(symbol, {})}
            
            # 计算总体统计
            total_value = sum(pos.get('current_value', 0) for pos in self.positions.values())
            total_cost = sum(pos.get('total_cost', 0) for pos in self.positions.values())
            total_profit = total_value - total_cost
            profit_rate = total_profit / total_cost if total_cost > 0 else 0
            
            return web.json_response({
                "status": "success",
                "positions": positions,
                "summary": {
                    "total_positions": len(self.positions),
                    "total_value": total_value,
                    "total_cost": total_cost,
                    "total_profit": total_profit,
                    "profit_rate": profit_rate,
                    "portfolio_ratio": total_value / self.capital if self.capital > 0 else 0,
                },
                "generated_at": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"持仓获取失败: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_update_position(self, request):
        """更新持仓信息"""
        try:
            data = await request.json()
            action = data.get('action', '')  # buy, sell, add
            symbol = data.get('symbol', '')
            price = data.get('price', 0)
            quantity = data.get('quantity', 0)
            
            logger.info(f"📝 更新持仓: {action} {symbol} {quantity}股 @ {price}")
            
            # 更新持仓
            result = await self.update_position(action, symbol, price, quantity)
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"持仓更新失败: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_status(self, request):
        """获取状态"""
        total_value = sum(pos.get('current_value', 0) for pos in self.positions.values())
        
        status = {
            "agent": self.name,
            "port": self.port,
            "status": "running",
            "positions": len(self.positions),
            "total_value": total_value,
            "portfolio_ratio": total_value / self.capital if self.capital > 0 else 0,
            "available_cash": self.capital - total_value,
            "last_update": datetime.now().isoformat(),
        }
        return web.json_response(status)
    
    async def handle_health(self, request):
        """健康检查"""
        return web.json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})
    
    async def check_risk_and_generate_plans(self, signals: List[Dict], capital: float, position_rules: Dict) -> Dict:
        """检查风险并生成交易计划"""
        logger.info("🔍 开始风险检查和交易计划生成...")
        
        try:
            if not signals:
                return {
                    "status": "success",
                    "trading_plans": [],
                    "risk_assessment": {"level": "low", "message": "无交易信号"},
                    "generated_at": datetime.now().isoformat()
                }
            
            # 应用风控规则
            max_positions = position_rules.get('max_positions', self.max_positions)
            max_portfolio_size = position_rules.get('max_portfolio_size', self.max_portfolio_size)
            initial_position = position_rules.get('initial_position', self.initial_position)
            
            # 1. 检查当前持仓
            current_positions = len(self.positions)
            current_portfolio_value = sum(pos.get('current_value', 0) for pos in self.positions.values())
            current_portfolio_ratio = current_portfolio_value / capital if capital > 0 else 0
            
            # 2. 计算可用仓位
            available_positions = max(0, max_positions - current_positions)
            available_capital = capital * max_portfolio_size - current_portfolio_value
            available_capital = max(0, available_capital)
            
            logger.info(f"📊 当前持仓: {current_positions}/{max_positions}只, 仓位{current_portfolio_ratio*100:.1f}%")
            logger.info(f"💰 可用资金: {available_capital:,.0f}元, 可开仓{available_positions}只")
            
            # 3. 对信号进行风险排序和过滤
            filtered_signals = await self.filter_signals_by_risk(signals)
            
            # 4. 生成交易计划
            trading_plans = []
            used_capital = 0
            
            for i, signal in enumerate(filtered_signals[:available_positions]):
                if used_capital >= available_capital * 0.9:  # 留10%缓冲
                    break
                
                # 生成单个交易计划
                plan = await self.generate_trading_plan(signal, capital, initial_position)
                if plan:
                    trading_plans.append(plan)
                    used_capital += plan.get('initial_investment', 0)
            
            # 5. 风险评估
            risk_assessment = await self.assess_overall_risk(trading_plans, capital)
            
            # 6. 保存交易计划
            self.trading_plans = trading_plans
            
            logger.info(f"✅ 生成 {len(trading_plans)} 个交易计划, 预计使用资金 {used_capital:,.0f}元")
            
            return {
                "status": "success",
                "trading_plans": trading_plans,
                "risk_assessment": risk_assessment,
                "position_summary": {
                    "current_positions": current_positions,
                    "current_portfolio_value": current_portfolio_value,
                    "current_portfolio_ratio": current_portfolio_ratio,
                    "available_positions": available_positions,
                    "available_capital": available_capital,
                    "used_capital": used_capital,
                    "remaining_capital": capital - current_portfolio_value - used_capital,
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"风险检查异常: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "trading_plans": [],
                "risk_assessment": {"level": "high", "message": f"风险检查异常: {str(e)[:100]}"},
                "generated_at": datetime.now().isoformat()
            }
    
    async def filter_signals_by_risk(self, signals: List[Dict]) -> List[Dict]:
        """按风险过滤信号"""
        filtered_signals = []
        
        for signal in signals:
            try:
                symbol = signal.get('code', '')
                name = signal.get('name', '')
                current_price = signal.get('current_price', 0)
                
                # 风险检查1: 价格合理性
                if current_price <= 0 or current_price > 1000:  # 价格异常
                    logger.debug(f"⚠️  {symbol} 价格异常: {current_price}")
                    continue
                
                # 风险检查2: 流动性检查（通过成交量）
                # 这里可以添加更复杂的流动性检查
                
                # 风险检查3: 技术指标风险
                backtest_win_rate = signal.get('backtest_win_rate', 0)
                if backtest_win_rate < 0.5:  # 胜率低于50%
                    logger.debug(f"⚠️  {symbol} 胜率过低: {backtest_win_rate*100:.1f}%")
                    continue
                
                # 风险检查4: 波动性风险
                max_drawdown = signal.get('backtest_max_drawdown', 0)
                if max_drawdown > 0.15:  # 最大回撤超过15%
                    logger.debug(f"⚠️  {symbol} 回撤过大: {max_drawdown*100:.1f}%")
                    continue
                
                # 计算风险评分
                risk_score = self.calculate_risk_score(signal)
                signal['risk_score'] = risk_score
                
                filtered_signals.append(signal)
                
            except Exception as e:
                logger.debug(f"信号 {signal.get('code', '')} 风险检查失败: {str(e)[:50]}")
                continue
        
        # 按风险评分排序（风险低的优先）
        filtered_signals.sort(key=lambda x: x.get('risk_score', 100))
        
        logger.info(f"🛡️ 风险过滤: {len(signals)} → {len(filtered_signals)}")
        
        return filtered_signals
    
    def calculate_risk_score(self, signal: Dict) -> float:
        """计算风险评分（越低越好）"""
        score = 50  # 基础分
        
        # 1. 胜率因素（胜率越高，风险越低）
        win_rate = signal.get('backtest_win_rate', 0.5)
        score -= (win_rate - 0.5) * 40  # 胜率每提高10%，风险分降低4分
        
        # 2. 回撤因素（回撤越小，风险越低）
        max_drawdown = signal.get('backtest_max_drawdown', 0.1)
        score += max_drawdown * 100  # 回撤每增加1%，风险分增加1分
        
        # 3. 夏普比率（越高越好）
        sharpe_ratio = signal.get('backtest_sharpe_ratio', 0)
        if sharpe_ratio > 0:
            score -= sharpe_ratio * 10
        
        # 4. 价格因素（价格适中风险低）
        price = signal.get('current_price', 0)
        if 10 <= price <= 50:
            score -= 10  # 10-50元价格区间风险较低
        elif price > 100:
            score += 20  # 高价股风险较高
        
        # 确保分数在合理范围内
        score = max(0, min(100, score))
        
        return round(score, 1)
    
    async def generate_trading_plan(self, signal: Dict, capital: float, initial_position_ratio: float) -> Optional[Dict]:
        """生成交易计划"""
        try:
            symbol = signal.get('code', '')
            name = signal.get('name', '')
            current_price = signal.get('current_price', 0)
            sector = signal.get('sector', '未知板块')
            
            if not symbol or current_price <= 0:
                return None
            
            # 计算投资金额
            initial_investment = capital * initial_position_ratio
            max_investment = capital * self.max_single_position
            
            # 计算股数（取整）
            initial_shares = int(initial_investment / current_price / 100) * 100  # 按手取整
            max_shares = int(max_investment / current_price / 100) * 100
            
            # 计算价格区间
            buy_price = current_price
            add_price = current_price * (1 + self.add_position_threshold)  # 注意：补仓是下跌时
            take_profit_price = current_price * (1 + self.take_profit)
            stop_loss_price = current_price * (1 - self.stop_loss)
            
            # 生成交易计划
            plan = {
                "code": symbol,
                "name": name,
                "sector": sector,
                "current_price": round(current_price, 2),
                "buy_price": round(buy_price, 2),
                "add_price": round(add_price, 2),
                "take_profit_price": round(take_profit_price, 2),
                "stop_loss_price": round(stop_loss_price, 2),
                "initial_shares": initial_shares,
                "max_shares": max_shares,
                "initial_investment": round(initial_shares * current_price, 2),
                "max_investment": round(max_shares * current_price, 2),
                "initial_position_ratio": initial_position_ratio,
                "max_position_ratio": self.max_single_position,
                "holding_days_limit": self.max_holding_days,
                "risk_score": signal.get('risk_score', 50),
                "backtest_win_rate": signal.get('backtest_win_rate', 0),
                "backtest_avg_profit": signal.get('backtest_avg_profit', 0),
                "dragon_tiger": signal.get('dragon_tiger', '否'),
                "total_gain": signal.get('total_gain', 'N/A'),
                "ma_pattern": signal.get('ma_pattern', 'N/A'),
                "logic": self.generate_trading_logic(signal),
                "risk": self.generate_risk_warning(signal),
                "generated_at": datetime.now().isoformat()
            }
            
            return plan
            
        except Exception as e:
            logger.debug(f"交易计划生成失败: {str(e)[:50]}")
            return None
    
    def generate_trading_logic(self, signal: Dict) -> str:
        """生成交易逻辑说明"""
        logic_parts = []
        
        # 板块逻辑
        sector = signal.get('sector', '')
        if sector:
            logic_parts.append(f"属于热门板块【{sector}】")
        
        # 龙虎榜逻辑
        dragon_tiger = signal.get('dragon_tiger', '')
        if dragon_tiger == '是':
            logic_parts.append("近期有机构/游资关注")
        
        # 技术逻辑
        ma_pattern = signal.get('ma_pattern', '')
        if '粘合' in ma_pattern and '发散' in ma_pattern:
            logic_parts.append("均线完成粘合