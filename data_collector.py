#!/usr/bin/env python3
"""
辅1：数据员 (18790)
负责数据采集：热门板块、龙虎榜、基础数据
"""

import asyncio
import aiohttp
from aiohttp import web
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
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
        logging.FileHandler(f"logs/data_collector_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataCollector")

class DataCollector:
    """数据员 - 负责数据采集"""
    
    def __init__(self):
        self.port = SYSTEM_ARCHITECTURE["data_collector"]["port"]
        self.name = SYSTEM_ARCHITECTURE["data_collector"]["name"]
        
        # 数据缓存
        self.hot_sectors_cache = None
        self.dragon_tiger_cache = None
        self.stock_data_cache = {}
        self.cache_time = {}
        
        # 数据源
        self.data_sources = STRATEGY_CONFIG['data_sources']
        
        logger.info(f"🚀 {self.name} 初始化完成 (端口: {self.port})")
    
    async def start_server(self):
        """启动HTTP服务器"""
        from aiohttp import web
        
        app = web.Application()
        
        # 注册路由
        app.router.add_post('/data/hot_sectors', self.handle_hot_sectors)
        app.router.add_post('/data/dragon_tiger', self.handle_dragon_tiger)
        app.router.add_post('/data/stock', self.handle_stock_data)
        app.router.add_get('/status', self.handle_status)
        app.router.add_get('/health', self.handle_health)
        
        # 启动服务器
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"🌐 {self.name} HTTP服务器已启动: http://localhost:{self.port}")
        
        # 保持服务器运行
        await asyncio.Event().wait()
    
    async def handle_hot_sectors(self, request):
        """处理热门板块请求"""
        try:
            data = await request.json()
            days = data.get('days', STRATEGY_CONFIG['stock_filters']['hot_sector_days'])
            count = data.get('count', STRATEGY_CONFIG['stock_filters']['hot_sector_count'])
            
            logger.info(f"📊 获取热门板块: 近{days}日, 前{count}名")
            
            # 检查缓存
            cache_key = f"hot_sectors_{days}_{count}"
            if (cache_key in self.cache_time and 
                (datetime.now() - self.cache_time[cache_key]).seconds < 300):  # 5分钟缓存
                logger.info("📦 使用缓存的板块数据")
                return web.json_response(self.hot_sectors_cache)
            
            # 获取热门板块数据
            hot_sectors = await self.get_hot_sectors(days, count)
            
            # 更新缓存
            self.hot_sectors_cache = hot_sectors
            self.cache_time[cache_key] = datetime.now()
            
            return web.json_response(hot_sectors)
            
        except Exception as e:
            logger.error(f"热门板块获取失败: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_dragon_tiger(self, request):
        """处理龙虎榜请求"""
        try:
            data = await request.json()
            days = data.get('days', STRATEGY_CONFIG['stock_filters']['dragon_tiger_days'])
            
            logger.info(f"🐉 获取龙虎榜数据: 近{days}天")
            
            # 检查缓存
            cache_key = f"dragon_tiger_{days}"
            if (cache_key in self.cache_time and 
                (datetime.now() - self.cache_time[cache_key]).seconds < 300):  # 5分钟缓存
                logger.info("📦 使用缓存的龙虎榜数据")
                return web.json_response(self.dragon_tiger_cache)
            
            # 获取龙虎榜数据
            dragon_tiger = await self.get_dragon_tiger_data(days)
            
            # 更新缓存
            self.dragon_tiger_cache = dragon_tiger
            self.cache_time[cache_key] = datetime.now()
            
            return web.json_response(dragon_tiger)
            
        except Exception as e:
            logger.error(f"龙虎榜获取失败: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_stock_data(self, request):
        """处理股票数据请求"""
        try:
            data = await request.json()
            symbols = data.get('symbols', [])
            fields = data.get('fields', ['basic', 'price', 'volume', 'ma'])
            
            logger.info(f"📈 获取股票数据: {len(symbols)}只股票, 字段: {fields}")
            
            # 获取股票数据
            stock_data = await self.get_stock_data(symbols, fields)
            
            return web.json_response(stock_data)
            
        except Exception as e:
            logger.error(f"股票数据获取失败: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_status(self, request):
        """获取状态"""
        status = {
            "agent": self.name,
            "port": self.port,
            "status": "running",
            "cache_size": len(self.stock_data_cache),
            "last_update": datetime.now().isoformat(),
            "data_sources": list(self.data_sources.keys()),
        }
        return web.json_response(status)
    
    async def handle_health(self, request):
        """健康检查"""
        return web.json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})
    
    async def get_hot_sectors(self, days: int = 3, count: int = 20) -> Dict:
        """获取热门板块数据"""
        logger.info(f"🔥 开始获取热门板块数据 (近{days}日, 前{count}名)")
        
        try:
            # 尝试使用AkShare获取板块数据
            import akshare as ak
            
            # 获取板块涨跌幅数据
            sector_df = ak.stock_board_industry_name_em()
            
            if sector_df.empty:
                logger.warning("⚠️ 未获取到板块数据，返回示例数据")
                return self._get_sample_hot_sectors()
            
            # 获取板块历史数据计算涨幅
            hot_sectors = []
            for _, row in sector_df.head(30).iterrows():  # 先取前30个分析
                try:
                    sector_code = row['板块代码']
                    sector_name = row['板块名称']
                    
                    # 获取板块历史数据
                    hist_df = ak.stock_board_industry_hist_em(
                        symbol=sector_name,
                        start_date=(datetime.now() - timedelta(days=days+5)).strftime("%Y%m%d"),
                        end_date=datetime.now().strftime("%Y%m%d"),
                        adjust="qfq"
                    )
                    
                    if not hist_df.empty and len(hist_df) >= days:
                        # 计算涨幅
                        start_price = hist_df.iloc[-days]['收盘']
                        end_price = hist_df.iloc[-1]['收盘']
                        gain = (end_price - start_price) / start_price * 100
                        
                        # 计算成交量变化
                        if '成交量' in hist_df.columns:
                            volume_change = hist_df['成交量'].iloc[-days:].mean() / hist_df['成交量'].iloc[:-days].mean() if len(hist_df) > days else 1
                        else:
                            volume_change = 1
                        
                        hot_sectors.append({
                            "code": sector_code,
                            "name": sector_name,
                            "gain": round(gain, 2),
                            "volume_change": round(volume_change, 2),
                            "current_price": end_price,
                            "data_points": len(hist_df)
                        })
                        
                except Exception as e:
                    logger.debug(f"板块 {sector_name} 数据处理失败: {str(e)[:50]}")
                    continue
            
            # 按涨幅排序并取前count名
            hot_sectors.sort(key=lambda x: x['gain'], reverse=True)
            hot_sectors = hot_sectors[:count]
            
            logger.info(f"✅ 获取到 {len(hot_sectors)} 个热门板块")
            
            return {
                "status": "success",
                "count": len(hot_sectors),
                "days": days,
                "hot_sectors": hot_sectors,
                "generated_at": datetime.now().isoformat()
            }
            
        except ImportError:
            logger.error("❌ AkShare 未安装，无法获取板块数据")
            return self._get_sample_hot_sectors()
        except Exception as e:
            logger.error(f"❌ 热门板块获取异常: {str(e)}")
            return self._get_sample_hot_sectors()
    
    async def get_dragon_tiger_data(self, days: int = 30) -> Dict:
        """获取龙虎榜数据"""
        logger.info(f"🐉 开始获取龙虎榜数据 (近{days}天)")
        
        try:
            import akshare as ak
            
            # 获取龙虎榜数据
            today = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            
            dragon_df = ak.stock_sina_lhb_detail_daily(start_date=start_date, end_date=today)
            
            if dragon_df.empty:
                logger.warning("⚠️ 未获取到龙虎榜数据，返回示例数据")
                return self._get_sample_dragon_tiger()
            
            # 处理龙虎榜数据
            dragon_stocks = {}
            for _, row in dragon_df.iterrows():
                try:
                    symbol = row.get('代码', '')
                    name = row.get('名称', '')
                    date = row.get('交易日期', '')
                    reason = row.get('上榜原因', '')
                    
                    if symbol and symbol not in dragon_stocks:
                        dragon_stocks[symbol] = {
                            "code": symbol,
                            "name": name,
                            "latest_date": date,
                            "reason": reason,
                            "count": 1
                        }
                    elif symbol in dragon_stocks:
                        dragon_stocks[symbol]["count"] += 1
                        # 更新为最新日期
                        if date > dragon_stocks[symbol]["latest_date"]:
                            dragon_stocks[symbol]["latest_date"] = date
                            dragon_stocks[symbol]["reason"] = reason
                            
                except Exception as e:
                    logger.debug(f"龙虎榜记录处理失败: {str(e)[:50]}")
                    continue
            
            result = list(dragon_stocks.values())
            logger.info(f"✅ 获取到 {len(result)} 只龙虎榜股票")
            
            return {
                "status": "success",
                "count": len(result),
                "days": days,
                "dragon_tiger_stocks": result,
                "generated_at": datetime.now().isoformat()
            }
            
        except ImportError:
            logger.error("❌ AkShare 未安装，无法获取龙虎榜数据")
            return self._get_sample_dragon_tiger()
        except Exception as e:
            logger.error(f"❌ 龙虎榜获取异常: {str(e)}")
            return self._get_sample_dragon_tiger()
    
    async def get_stock_data(self, symbols: List[str], fields: List[str]) -> Dict:
        """获取股票数据"""
        logger.info(f"📈 开始获取股票数据: {len(symbols)}只股票")
        
        try:
            import akshare as ak
            
            results = {}
            
            for symbol in symbols:
                try:
                    stock_info = {}
                    
                    # 基础信息
                    if 'basic' in fields:
                        # 获取股票基本信息
                        spot_df = ak.stock_zh_a_spot()
                        stock_spot = spot_df[spot_df['代码'] == symbol]
                        
                        if not stock_spot.empty:
                            data = stock_spot.iloc[0]
                            stock_info['basic'] = {
                                "code": symbol,
                                "name": data.get('名称', ''),
                                "price": float(data.get('最新价', 0)),
                                "change": float(data.get('涨跌幅', 0)),
                                "volume": int(data.get('成交量', 0)),
                                "turnover": float(data.get('成交额', 0)),
                                "pe": data.get('市盈率', 'N/A'),
                                "pb": data.get('市净率', 'N/A'),
                                "market_cap": data.get('总市值', 'N/A'),
                            }
                    
                    # 历史数据（用于计算均线）
                    if 'ma' in fields or 'price' in fields or 'volume' in fields:
                        try:
                            # 获取历史数据
                            end_date = datetime.now().strftime("%Y%m%d")
                            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
                            
                            hist_df = ak.stock_zh_a_hist(
                                symbol=symbol, 
                                period="daily",
                                start_date=start_date,
                                end_date=end_date,
                                adjust="qfq"
                            )
                            
                            if not hist_df.empty:
                                # 价格数据
                                if 'price' in fields:
                                    latest = hist_df.iloc[0]
                                    stock_info['price'] = {
                                        "current": float(latest['收盘']),
                                        "high": float(latest['最高']),
                                        "low": float(latest['最低']),
                                        "open": float(latest['开盘']),
                                        "amplitude": float(latest['振幅']) if '振幅' in latest else 0,
                                    }
                                
                                # 成交量数据
                                if 'volume' in fields:
                                    latest = hist_df.iloc[0]
                                    stock_info['volume'] = {
                                        "volume": int(latest['成交量']),
                                        "turnover": float(latest['成交额']) if '成交额' in latest else 0,
                                        "volume_ratio": float(latest['量比']) if '量比' in latest else 1,
                                    }
                                
                                # 均线数据
                                if 'ma' in fields:
                                    # 计算均线
                                    closes = hist_df['收盘'].astype(float)
                                    ma_periods = STRATEGY_CONFIG['stock_filters']['ma_periods']
                                    
                                    ma_values = {}
                                    for period in ma_periods:
                                        if len(closes) >= period:
                                            ma_values[f'ma{period}'] = float(closes.head(period).mean())
                                    
                                    stock_info['ma'] = ma_values
                                    stock_info['history_days'] = len(hist_df)
                                    
                        except Exception as e:
                            logger.debug(f"股票 {symbol} 历史数据获取失败: {str(e)[:50]}")
                    
                    results[symbol] = stock_info
                    
                except Exception as e:
                    logger.debug(f"股票 {symbol} 数据处理失败: {str(e)[:50]}")
                    results[symbol] = {"error": str(e)[:100]}
            
            logger.info(f"✅ 成功获取 {len([v for v in results.values() if 'error' not in v])}/{len(symbols)} 只股票数据")
            
            return {
                "status": "success",
                "count": len(results),
                "stock_data": results,
                "generated_at": datetime.now().isoformat()
            }
            
        except ImportError:
            logger.error("❌ AkShare 未安装，无法获取股票数据")
            return self._get_sample_stock_data(symbols)
        except Exception as e:
            logger.error(f"❌ 股票数据获取异常: {str(e)}")
            return self._get_sample_stock_data(symbols)
    
    def _get_sample_hot_sectors(self) -> Dict:
        """获取示例热门板块数据（备用）"""
        sample_sectors = [
            {"code": "BK0481", "name": "半导体", "gain": 5.2, "volume_change": 1.8, "current_price": 1250.5, "data_points": 60},
            {"code": "BK0493", "name": "新能源汽车", "gain": 4.8, "volume_change": 1.5, "current_price": 980.3, "data_points": 60},
            {"code": "BK0516", "name": "人工智能", "gain": 3.9, "volume_change": 1.3, "current_price": 850.7, "data_points": 60},
            {"code": "BK0428", "name": "医药生物", "gain": 2.5, "volume_change": 1.1, "current_price": 720.4, "data_points": 60},
            {"code": "BK0473", "name": "白酒", "gain": 1.8, "volume_change": 0.9, "current_price": 650.2, "data_points": 60},
        ]
        
        return {
            "status": "sample",
            "count": len(sample_sectors),
            "days": 3,
            "hot_sectors": sample_sectors,
            "generated_at": datetime.now().isoformat(),
            "note": "示例数据，实际数据获取失败"
        }
    
    def _get_sample_dragon_tiger(self) -> Dict:
        """获取示例龙虎榜数据（备用）"""
        sample_stocks = [
            {"code": "000001", "name": "平安银行", "latest_date": "2026-02-28", "reason": "日涨幅偏离值达到7%"},
            {"code": "000002", "name": "万科A", "latest_date": "2026-02-27", "reason": "连续三个交易日内涨幅偏离值累计达到20%"},
            {"code": "000858", "name": "五粮液", "latest_date": "2026-02-26", "reason": "日换手率达到20%"},
            {"code": "002415", "name": "海康威视", "latest_date": "2026-02-25", "reason": "日振幅值达到15%"},
            {"code": "300750", "name": "宁德时代", "latest_date": "2026-02-24", "reason": "日涨幅偏离值达到7%"},
        ]
        
        return {
            "status": "sample",
            "count": len(sample_stocks),
            "days": 30,
            "dragon_tiger_stocks": sample_stocks,
            "generated_at": datetime.now().isoformat(),
            "note": "示例数据，实际数据获取失败"
        }
async def main():
    """主函数"""
    collector = DataCollector()
    await collector.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 收到中断信号，正在关闭数据员...")
    except Exception as e:
        logger.error(f"数据员运行异常: {str(e)}")
        sys.exit(1)
