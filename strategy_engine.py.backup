#!/usr/bin/env python3
"""
辅2：策略员 (18791)
负责选股规则、信号生成、交易计划
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/strategy_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StrategyEngine")

class StrategyEngine:
    """策略员 - 负责选股规则和信号生成"""
    
    def __init__(self):
        self.port = SYSTEM_ARCHITECTURE["strategy_engine"]["port"]
        self.name = SYSTEM_ARCHITECTURE["strategy_engine"]["name"]
        
        # 策略配置
        self.filters = STRATEGY_CONFIG['stock_filters']
        
        logger.info(f"🚀 {self.name} 初始化完成 (端口: {self.port})")
    
    async def start_server(self):
        """启动HTTP服务器"""
        from aiohttp import web
        
        app = web.Application()
        
        # 注册路由
        app.router.add_post('/strategy/run', self.handle_run_strategy)
        app.router.add_post('/strategy/signals', self.handle_get_signals)
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
    
    async def handle_run_strategy(self, request):
        """处理策略运行请求"""
        try:
            data = await request.json()
            hot_sectors = data.get('hot_sectors', [])
            filters = data.get('filters', self.filters)
            
            logger.info(f"🎯 运行选股策略: {len(hot_sectors)}个热门板块")
            
            # 运行策略
            result = await self.run_strategy(hot_sectors, filters)
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"策略运行失败: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_get_signals(self, request):
        """获取信号请求"""
        try:
            data = await request.json()
            symbols = data.get('symbols', [])
            
            logger.info(f"📡 获取选股信号: {len(symbols)}只股票")
            
            # 获取信号
            signals = await self.get_signals_for_stocks(symbols)
            
            return web.json_response(signals)
            
        except Exception as e:
            logger.error(f"信号获取失败: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_status(self, request):
        """获取状态"""
        status = {
            "agent": self.name,
            "port": self.port,
            "status": "running",
            "filters": list(self.filters.keys()),
            "last_update": datetime.now().isoformat(),
        }
        return web.json_response(status)
    
    async def handle_health(self, request):
        """健康检查"""
        return web.json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})
    
    async def run_strategy(self, hot_sectors: List[Dict], filters: Dict) -> Dict:
        """运行选股策略"""
        logger.info("🔍 开始执行选股策略...")
        
        try:
            # 1. 获取热门板块的股票
            sector_stocks = await self.get_stocks_in_sectors(hot_sectors)
            logger.info(f"📊 热门板块包含 {len(sector_stocks)} 只股票")
            
            if not sector_stocks:
                return {
                    "status": "success",
                    "signals": [],
                    "filter_steps": {},
                    "message": "热门板块无股票数据",
                    "generated_at": datetime.now().isoformat()
                }
            
            # 2. 逐步应用过滤条件
            filter_results = {}
            filtered_stocks = sector_stocks.copy()
            
            # 步骤1: 龙虎榜过滤
            filter_results['step1_dragon_tiger'] = len(filtered_stocks)
            filtered_stocks = await self.filter_dragon_tiger(filtered_stocks, filters)
            filter_results['step2_after_dragon_tiger'] = len(filtered_stocks)
            
            # 步骤2: 股价过滤
            filtered_stocks = await self.filter_price(filtered_stocks, filters)
            filter_results['step3_after_price'] = len(filtered_stocks)
            
            # 步骤3: 涨幅过滤
            filtered_stocks = await self.filter_gain(filtered_stocks, filters)
            filter_results['step4_after_gain'] = len(filtered_stocks)
            
            # 步骤4: 均线形态过滤
            filtered_stocks = await self.filter_ma_pattern(filtered_stocks, filters)
            filter_results['step5_after_ma'] = len(filtered_stocks)
            
            # 步骤5: 基础过滤
            filtered_stocks = await self.filter_basic(filtered_stocks, filters)
            filter_results['step6_after_basic'] = len(filtered_stocks)
            
            # 3. 生成选股信号
            signals = await self.generate_signals(filtered_stocks, filters)
            
            logger.info(f"✅ 策略执行完成: 原始{len(sector_stocks)}只 → 过滤后{len(filtered_stocks)}只 → 信号{len(signals)}个")
            
            return {
                "status": "success",
                "signals": signals,
                "filter_steps": filter_results,
                "total_stocks": len(sector_stocks),
                "filtered_stocks": len(filtered_stocks),
                "signal_count": len(signals),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"策略执行异常: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "signals": [],
                "generated_at": datetime.now().isoformat()
            }
    
    async def get_stocks_in_sectors(self, hot_sectors: List[Dict]) -> List[str]:
        """获取热门板块的股票"""
        logger.info(f"🔍 获取热门板块股票...")
        
        try:
            import akshare as ak
            
            all_stocks = []
            
            for sector in hot_sectors[:10]:  # 只处理前10个热门板块
                try:
                    sector_code = sector.get('code', '')
                    sector_name = sector.get('name', '')
                    
                    # 获取板块成分股
                    cons_df = ak.stock_board_cons_em(symbol=sector_code)
                    
                    if not cons_df.empty and '代码' in cons_df.columns:
                        stocks = cons_df['代码'].tolist()
                        logger.debug(f"板块 {sector_name} 包含 {len(stocks)} 只股票")
                        all_stocks.extend(stocks)
                        
                except Exception as e:
                    logger.debug(f"板块 {sector.get('name', '')} 股票获取失败: {str(e)[:50]}")
                    continue
            
            # 去重
            unique_stocks = list(set(all_stocks))
            logger.info(f"✅ 获取到 {len(unique_stocks)} 只唯一股票")
            
            return unique_stocks
            
        except ImportError:
            logger.error("❌ AkShare 未安装，返回示例股票")
            return self._get_sample_stocks()
        except Exception as e:
            logger.error(f"❌ 板块股票获取异常: {str(e)}")
            return self._get_sample_stocks()
    
    async def filter_dragon_tiger(self, stocks: List[str], filters: Dict) -> List[str]:
        """龙虎榜过滤"""
        days = filters.get('dragon_tiger_days', 30)
        logger.info(f"🐉 龙虎榜过滤: 近{days}天上榜")
        
        try:
            # 这里需要调用数据员的龙虎榜接口
            # 暂时返回所有股票（示例）
            return stocks
            
        except Exception as e:
            logger.error(f"龙虎榜过滤失败: {str(e)}")
            return stocks
    
    async def filter_price(self, stocks: List[str], filters: Dict) -> List[str]:
        """股价过滤"""
        max_price = filters.get('max_price', 50)
        logger.info(f"💰 股价过滤: ≤{max_price}元")
        
        try:
            import akshare as ak
            
            filtered_stocks = []
            
            # 分批处理，避免请求过多
            batch_size = 50
            for i in range(0, len(stocks), batch_size):
                batch = stocks[i:i+batch_size]
                
                try:
                    # 获取实时行情
                    spot_df = ak.stock_zh_a_spot()
                    
                    for symbol in batch:
                        stock_data = spot_df[spot_df['代码'] == symbol]
                        if not stock_data.empty:
                            price = stock_data.iloc[0]['最新价']
                            if price <= max_price:
                                filtered_stocks.append(symbol)
                                
                except Exception as e:
                    logger.debug(f"股价过滤批次失败: {str(e)[:50]}")
                    continue
            
            logger.info(f"✅ 股价过滤: {len(stocks)} → {len(filtered_stocks)}")
            return filtered_stocks
            
        except ImportError:
            logger.error("❌ AkShare 未安装，跳过股价过滤")
            return stocks
        except Exception as e:
            logger.error(f"❌ 股价过滤异常: {str(e)}")
            return stocks
    
    async def filter_gain(self, stocks: List[str], filters: Dict) -> List[str]:
        """涨幅过滤"""
        max_gain = filters.get('max_total_gain', 0.3)
        start_date = filters.get('start_date', '2025-01-01')
        logger.info(f"📈 涨幅过滤: {start_date}至今涨幅≤{max_gain*100}%")
        
        try:
            import akshare as ak
            from datetime import datetime
            
            filtered_stocks = []
            
            # 将开始日期转换为datetime
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            today_str = datetime.now().strftime("%Y%m%d")
            start_str = start_dt.strftime("%Y%m%d")
            
            for symbol in stocks[:100]:  # 只处理前100只，避免过多请求
                try:
                    # 获取历史数据
                    hist_df = ak.stock_zh_a_hist(
                        symbol=symbol,
                        period="daily",
                        start_date=start_str,
                        end_date=today_str,
                        adjust="qfq"
                    )
                    
                    if not hist_df.empty and len(hist_df) > 1:
                        start_price = hist_df.iloc[-1]['收盘']  # 最早的价格
                        end_price = hist_df.iloc[0]['收盘']     # 最新的价格
                        
                        total_gain = (end_price - start_price) / start_price
                        
                        if total_gain <= max_gain:
                            filtered_stocks.append(symbol)
                            
                except Exception as e:
                    logger.debug(f"股票 {symbol} 涨幅计算失败: {str(e)[:50]}")
                    continue
            
            logger.info(f"✅ 涨幅过滤: {len(stocks)} → {len(filtered_stocks)}")
            return filtered_stocks
            
        except ImportError:
            logger.error("❌ AkShare 未安装，跳过涨幅过滤")
            return stocks
        except Exception as e:
            logger.error(f"❌ 涨幅过滤异常: {str(e)}")
            return stocks
    
    async def filter_ma_pattern(self, stocks: List[str], filters: Dict) -> List[str]:
        """均线形态过滤"""
        convergence_year = filters.get('convergence_year', 2025)
        divergence_year = filters.get('divergence_year', 2026)
        ma_periods = filters.get('ma_periods', [5, 10, 20, 30])
        
        logger.info(f"📊 均线形态过滤: {convergence_year}年粘合 → {divergence_year}年发散")
        
        try:
            import akshare as ak
            import numpy as np
            
            filtered_stocks = []
            
            for symbol in stocks[:50]:  # 只处理前50只
                try:
                    # 获取两年历史数据
                    end_date = datetime.now().strftime("%Y%m%d")
                    start_date = f"{convergence_year}0101"
                    
                    hist_df = ak.stock_zh_a_hist(
                        symbol=symbol,
                        period="daily",
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
                    
                    if hist_df.empty or len(hist_df) < 100:
                        continue
                    
                    # 分离两个年份的数据
                    hist_df['date'] = pd.to_datetime(hist_df['日期'])
                    hist_2025 = hist_df[hist_df['date'].dt.year == convergence_year]
                    hist_2026 = hist_df[hist_df['date'].dt.year == divergence_year]
                    
                    if len(hist_2025) < 50 or len(hist_2026) < 20:
                        continue
                    
                    # 计算2025年均线粘合度
                    closes_2025 = hist_2025['收盘'].astype(float).values
                    ma_values_2025 = []
                    
                    for period in ma_periods:
                        if len(closes_2025) >= period:
                            ma = np.convolve(closes_2025, np.ones(period)/period, mode='valid')
                            ma_values_2025.append(ma)
                    
                    # 检查粘合度（均线之间距离小）
                    if len(ma_values_2025) >= 2:
                        # 计算最后20个交易日的均线标准差
                        last_20_ma = []
                        for ma in ma_values_2025:
                            if len(ma) >= 20:
                                last_20_ma.append(ma[-20:])
                        
                        if last_20_ma:
                            # 计算均线之间的平均距离
                            ma_matrix = np.array(last_20_ma)
                            ma_std = np.std(ma_matrix, axis=0).mean()
                            
                            # 粘合条件：均线波动小
                            if ma_std < closes_2025[-1] * 0.02:  # 波动小于2%
                                # 检查2026年发散（均线向上排列）
                                closes_2026 = hist_2026['收盘'].astype(float).values
                                if len(closes_2026) >= 20:
                                    # 计算短期趋势
                                    trend_2026 = (closes_2026[-1] - closes_2026[0]) / closes_2026[0]
                                    
                                    if trend_2026 > 0:  # 向上趋势
                                        filtered_stocks.append(symbol)
                    
                except Exception as e:
                    logger.debug(f"股票 {symbol} 均线分析失败: {str(e)[:50]}")
                    continue
            
            logger.info(f"✅ 均线形态过滤: {len(stocks)} → {len(filtered_stocks)}")
            return filtered_stocks
            
        except ImportError:
            logger.error("❌ 必要库未安装，跳过均线过滤")
            return stocks
        except Exception as e:
            logger.error(f"❌ 均线过滤异常: {str(e)}")
            return stocks
    
    async def filter_basic(self, stocks: List[str], filters: Dict) -> List[str]:
        """基础过滤"""
        min_cap = filters.get('min_market_cap', 50)  # 亿
        min_turnover = filters.get('min_daily_turnover', 200000000)  # 2亿
        exclude_st = filters.get('exclude_st', True)
        exclude_suspended = filters.get('exclude_suspended', True)
        
        logger.info(f"🛡️ 基础过滤: 市值≥{min_cap}亿, 成交额≥{min_turnover/100000000:.1f}亿")
        
        try:
            import akshare as ak
            
            filtered_stocks = []
            
            # 分批处理
            batch_size = 50
            for i in range(0, len(stocks), batch_size):
                batch = stocks[i:i+batch_size]
                
                try:
                    # 获取实时行情
                    spot_df = ak.stock_zh_a_spot()
                    
                    for symbol in batch:
                        stock_data = spot_df[spot_df['代码'] == symbol]
                        if not stock_data.empty:
                            data = stock_data.iloc[0]
                            
                            # 检查ST
                            if exclude_st and ('ST' in data.get('名称', '') or '*ST' in data.get('名称', '')):
                                continue
                            
                            # 检查市值
                            market_cap = data.get('总市值', 0)
                            if isinstance(market_cap, str):
                                market_cap = float(market_cap.replace('亿', '')) if '亿' in market_cap else 0
                            
                            if market_cap < min_cap:
                                continue
                            
                            # 检查成交额
                            turnover = data.get('成交额', 0)
                            if turnover < min_turnover:
                                continue
                            
