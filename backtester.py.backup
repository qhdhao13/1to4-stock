#!/usr/bin/env python3
"""
辅3：回测员 (18792)
负责历史验证、胜率计算、风险收益分析
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
import pandas as pd
import numpy as np

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import SYSTEM_ARCHITECTURE, STRATEGY_CONFIG, NETWORK_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/backtester_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Backtester")

class Backtester:
    """回测员 - 负责历史验证和胜率计算"""
    
    def __init__(self):
        self.port = SYSTEM_ARCHITECTURE["backtester"]["port"]
        self.name = SYSTEM_ARCHITECTURE["backtester"]["name"]
        
        # 回测配置
        self.backtest_config = STRATEGY_CONFIG['backtest']
        
        # 回测结果缓存
        self.backtest_cache = {}
        
        logger.info(f"🚀 {self.name} 初始化完成 (端口: {self.port})")
    
    async def start_server(self):
        """启动HTTP服务器"""
        from aiohttp import web
        
        app = web.Application()
        
        # 注册路由
        app.router.add_post('/backtest/run', self.handle_run_backtest)
        app.router.add_post('/backtest/stats', self.handle_get_stats)
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
    
    async def handle_run_backtest(self, request):
        """处理回测请求"""
        try:
            data = await request.json()
            signals = data.get('signals', [])
            period = data.get('period', self.backtest_config['period'])
            min_win_rate = data.get('min_win_rate', self.backtest_config['min_win_rate'])
            
            logger.info(f"📈 运行回测: {len(signals)}个信号, 周期{period}天, 最低胜率{min_win_rate*100}%")
            
            # 运行回测
            result = await self.run_backtest(signals, period, min_win_rate)
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"回测运行失败: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_get_stats(self, request):
        """获取回测统计"""
        try:
            data = await request.json()
            backtest_id = data.get('backtest_id', 'latest')
            
            logger.info(f"📊 获取回测统计: {backtest_id}")
            
            # 获取统计信息
            stats = await self.get_backtest_stats(backtest_id)
            
            return web.json_response(stats)
            
        except Exception as e:
            logger.error(f"统计获取失败: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_status(self, request):
        """获取状态"""
        status = {
            "agent": self.name,
            "port": self.port,
            "status": "running",
            "cache_size": len(self.backtest_cache),
            "min_win_rate": self.backtest_config['min_win_rate'],
            "last_update": datetime.now().isoformat(),
        }
        return web.json_response(status)
    
    async def handle_health(self, request):
        """健康检查"""
        return web.json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})
    
    async def run_backtest(self, signals: List[Dict], period: int = 90, min_win_rate: float = 0.52) -> Dict:
        """运行回测"""
        logger.info(f"🔍 开始回测分析...")
        
        try:
            if not signals:
                return {
                    "status": "success",
                    "valid_signals": [],
                    "backtest_stats": {},
                    "message": "无信号需要回测",
                    "generated_at": datetime.now().isoformat()
                }
            
            # 1. 对每个信号进行回测
            backtest_results = []
            valid_signals = []
            
            for signal in signals[:self.backtest_config['sample_size']]:  # 限制样本数量
                try:
                    symbol = signal.get('code', '')
                    if not symbol:
                        continue
                    
                    # 运行单个信号回测
                    result = await self.backtest_single_signal(symbol, period)
                    
                    if result and result.get('win_rate', 0) >= min_win_rate:
                        # 信号有效，添加到结果
                        valid_signal = signal.copy()
                        valid_signal.update({
                            "backtest_win_rate": result['win_rate'],
                            "backtest_total_trades": result['total_trades'],
                            "backtest_profit_trades": result['profit_trades'],
                            "backtest_avg_profit": result['avg_profit'],
                            "backtest_max_drawdown": result['max_drawdown'],
                            "backtest_sharpe_ratio": result['sharpe_ratio'],
                        })
                        valid_signals.append(valid_signal)
                    
                    backtest_results.append(result)
                    
                except Exception as e:
                    logger.debug(f"信号 {signal.get('code', '')} 回测失败: {str(e)[:50]}")
                    continue
            
            # 2. 计算总体统计
            overall_stats = await self.calculate_overall_stats(backtest_results)
            
            # 3. 生成回测报告
            report = await self.generate_backtest_report(valid_signals, overall_stats)
            
            logger.info(f"✅ 回测完成: 原始{len(signals)}个 → 有效{len(valid_signals)}个, 平均胜率{overall_stats.get('avg_win_rate', 0)*100:.1f}%")
            
            return {
                "status": "success",
                "valid_signals": valid_signals,
                "backtest_stats": overall_stats,
                "backtest_report": report,
                "total_signals": len(signals),
                "valid_count": len(valid_signals),
                "filter_rate": len(valid_signals) / len(signals) if len(signals) > 0 else 0,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"回测执行异常: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "valid_signals": [],
                "backtest_stats": {},
                "generated_at": datetime.now().isoformat()
            }
    
    async def backtest_single_signal(self, symbol: str, period: int = 90) -> Optional[Dict]:
        """回测单个信号"""
        try:
            import akshare as ak
            
            # 获取历史数据
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=period+30)).strftime("%Y%m%d")  # 多取30天用于计算
            
            hist_df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if hist_df.empty or len(hist_df) < period:
                logger.debug(f"股票 {symbol} 历史数据不足")
                return None
            
            # 转换为DataFrame并处理
            df = hist_df.copy()
            df['date'] = pd.to_datetime(df['日期'])
            df['close'] = df['收盘'].astype(float)
            df['high'] = df['最高'].astype(float)
            df['low'] = df['最低'].astype(float)
            df['volume'] = df['成交量'].astype(float)
            
            # 按日期排序
            df = df.sort_values('date')
            
            # 模拟交易信号（基于均线金叉死叉）
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma10'] = df['close'].rolling(window=10).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()
            
            # 生成交易信号
            df['signal'] = 0
            df.loc[df['ma5'] > df['ma10'], 'signal'] = 1  # 金叉买入信号
            df.loc[df['ma5'] < df['ma10'], 'signal'] = -1  # 死叉卖出信号
            
            # 计算收益率
            df['returns'] = df['close'].pct_change()
            
            # 模拟交易
            trades = []
            position = 0
            entry_price = 0
            entry_date = None
            
            for i in range(1, len(df)):
                current_signal = df.iloc[i]['signal']
                prev_signal = df.iloc[i-1]['signal']
                
                # 买入信号（金叉）
                if position == 0 and current_signal == 1 and prev_signal <= 0:
                    position = 1
                    entry_price = df.iloc[i]['close']
                    entry_date = df.iloc[i]['date']
                
                # 卖出信号（死叉或持有5天后）
                elif position == 1:
                    days_held = (df.iloc[i]['date'] - entry_date).days if entry_date else 0
                    
                    # 卖出条件：死叉或持有5天
                    if current_signal == -1 and prev_signal >= 0:
                        exit_price = df.iloc[i]['close']
                        profit_pct = (exit_price - entry_price) / entry_price
                        
                        trades.append({
                            "entry_date": entry_date,
                            "exit_date": df.iloc[i]['date'],
                            "entry_price": entry_price,
                            "exit_price": exit_price,
                            "profit_pct": profit_pct,
                            "days_held": days_held,
                            "exit_reason": "signal"
                        })
                        
                        position = 0
                        entry_price = 0
                        entry_date = None
                    
                    # 强制平仓：持有超过5天
                    elif days_held >= 5:
                        exit_price = df.iloc[i]['close']
                        profit_pct = (exit_price - entry_price) / entry_price
                        
                        trades.append({
                            "entry_date": entry_date,
                            "exit_date": df.iloc[i]['date'],
                            "entry_price": entry_price,
                            "exit_price": exit_price,
                            "profit_pct": profit_pct,
                            "days_held": days_held,
                            "exit_reason": "timeout"
                        })
                        
                        position = 0
                        entry_price = 0
                        entry_date = None
            
            # 如果最后还有持仓，平仓
            if position == 1 and entry_date:
                exit_price = df.iloc[-1]['close']
                days_held = (df.iloc[-1]['date'] - entry_date).days
                profit_pct = (exit_price - entry_price) / entry_price
                
                trades.append({
                    "entry_date": entry_date,
                    "exit_date": df.iloc[-1]['date'],
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "profit_pct": profit_pct,
                    "days_held": days_held,
                    "exit_reason": "end_of_period"
                })
            
            # 计算回测指标
            if trades:
                profits = [t['profit_pct'] for t in trades]
                win_trades = [p for p in profits if p > 0]
                
                total_trades = len(trades)
                profit_trades = len(win_trades)
                win_rate = profit_trades / total_trades if total_trades > 0 else 0
                avg_profit = np.mean(profits) if profits else 0
                
                # 计算最大回撤
                equity_curve = [1.0]
                for trade in trades:
                    equity_curve.append(equity_curve[-1] * (1 + trade['profit_pct']))
                
                drawdowns = []
                peak = equity_curve[0]
                for equity in equity_curve:
                    if equity > peak:
                        peak = equity
                    drawdown = (peak - equity) / peak
                    drawdowns.append(drawdown)
                
                max_drawdown = max(drawdowns) if drawdowns else 0
                
                # 计算夏普比率（简化版）
                returns_std = np.std(profits) if len(profits) > 1 else 0
                sharpe_ratio = avg_profit / returns_std if returns_std > 0 else 0
                
                result = {
                    "symbol": symbol,
                    "total_trades": total_trades,
                    "profit_trades": profit_trades,
                    "loss_trades": total_trades - profit_trades,
                    "win_rate": win_rate,
                    "avg_profit": avg_profit,
                    "max_profit": max(profits) if profits else 0,
                    "min_profit": min(profits) if profits else 0,
                    "max_drawdown": max_drawdown,
                    "sharpe_ratio": sharpe_ratio,
                    "trades": trades[:10],  # 只返回前10笔交易
                }
                
                return result
            else:
                # 无交易信号
                return {
                    "symbol": symbol,
                    "total_trades": 0,
                    "profit_trades": 0,
                    "loss_trades": 0,
                    "win_rate": 0,
                    "avg_profit": 0,
                    "max_profit": 0,
                    "min_profit": 0,
                    "max_drawdown": 0,
                    "sharpe_ratio": 0,
                    "trades": [],
                }
                
        except ImportError:
            logger.error("❌ AkShare 未安装，无法回测")
            return None
        except Exception as e:
            logger.debug(f"股票 {symbol} 回测异常: {str(e)[:50]}")
            return None
    
    async def calculate_overall_stats(self, backtest_results: List[Optional[Dict]]) -> Dict:
        """计算总体统计"""
        valid_results = [r for r in backtest_results if r and r.get('total_trades', 0) > 0]
        
        if not valid_results:
            return {
                "avg_win_rate": 0,
                "total_trades": 0,
                "avg_profit": 0,
                "avg_max_drawdown": 0,
                "avg_sharpe_ratio": 0,
                "sample_size": len(backtest_results),
                "valid_samples": 0,
            }
        
        # 计算平均值
        win_rates = [r['win_rate'] for r in valid_results]
        profits = [r['avg_profit'] for r in valid_results]
        drawdowns = [r['max_drawdown'] for r in valid_results]
        sharpes = [r['sharpe_ratio'] for r in valid_results]
        total_trades = sum(r['total_trades'] for r in valid_results)
        
        stats = {
            "avg_win_rate": np.mean(win_rates),
            "std_win_rate": np.std(win_rates) if len(win_rates) > 1 else 0,
            "min_win_rate": min(win_rates) if win_rates else 0,
            "max_win_rate": max(win_rates) if win_rates else 0,
            "avg_profit": np.mean(profits),
            "std_profit": np.std(profits) if len(profits) > 1 else 0,
            "avg_max_drawdown": np.mean(drawdowns),
            "avg_sharpe_ratio": np.mean(sharpes),
            "total_trades": total_trades,
            "sample_size": len(backtest_results),
            "valid_samples": len(valid_results),
            "valid_rate": len(valid_results) / len(backtest_results) if len(backtest_results) > 0 else 0,
        }
        
        return stats
    
    async def generate_backtest_report(self, valid_signals: List[Dict], overall_stats: Dict) -> str:
        """生成回测报告"""
        report_date = datetime.now().strftime("%Y-%m-%d")
        
        report = f"""# 📈 回测分析报告
生成时间: {report_date}

## 📊 总体统计
- 样本数量: {overall_stats.get('sample_size', 0)}
- 有效样本: {overall_stats.get('valid_samples', 0)} ({overall_stats.get('valid_rate', 0)*100:.1f}%)
- 平均胜率: {overall_stats.get('avg_win_rate', 0)*100:.1f}%
- 平均收益率: {overall_stats.get('avg_profit', 0)*100:.2f}%
- 平均最大回撤: {overall_stats.get('avg_max_drawdown', 0)*100:.2f}%
- 平均夏普比率: {overall_stats.get('avg_sharpe_ratio', 0):.2f}
- 总交易次数: {overall_stats.get('total_trades', 0)}

##