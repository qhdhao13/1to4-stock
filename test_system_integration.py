#!/usr/bin/env python3
"""
系统集成测试 - 启动数据员和策略员进行通信测试
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
import subprocess
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SystemTest")

class SystemIntegrationTest:
    """系统集成测试"""
    
    def __init__(self):
        self.agents = {
            "data_collector": {"port": 18990, "process": None},
            "strategy_engine": {"port": 18891, "process": None}
        }
        
        self.base_urls = {
            "data": "http://localhost:18990",
            "strategy": "http://localhost:18891"
        }
    
    async def start_agent(self, agent_name, agent_file):
        """启动单个Agent"""
        cmd = ["python3", agent_file]
        
        logger.info(f"🚀 启动 {agent_name}...")
        
        # 在后台启动进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        self.agents[agent_name]["process"] = process
        
        # 等待启动
        await asyncio.sleep(3)
        
        # 检查是否启动成功
        if process.poll() is None:
            logger.info(f"   ✅ {agent_name} 启动成功 (PID: {process.pid})")
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"   ❌ {agent_name} 启动失败")
            logger.error(f"      stderr: {stderr[:200]}")
            return False
    
    async def check_agent_health(self, agent_name, port):
        """检查Agent健康状态"""
        url = f"http://localhost:{port}/health"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"   ✅ {agent_name} 健康检查通过: {data.get('status', 'unknown')}")
                        return True
                    else:
                        logger.warning(f"   ⚠️  {agent_name} 健康检查失败: HTTP {response.status}")
                        return False
        except Exception as e:
            logger.error(f"   ❌ {agent_name} 健康检查异常: {e}")
            return False
    
    async def test_agent_communication(self):
        """测试Agent间通信"""
        logger.info("🔗 测试Agent间通信...")
        
        # 测试数据员获取数据
        data_url = f"{self.base_urls['data']}/data/hot_sectors"
        data_payload = {"days": 3, "count": 5}
        
        try:
            async with aiohttp.ClientSession() as session:
                # 获取数据
                logger.info("   1. 从数据员获取热门板块数据...")
                async with session.post(data_url, json=data_payload, timeout=10) as response:
                    if response.status == 200:
                        data_result = await response.json()
                        logger.info(f"      ✅ 数据获取成功，板块数量: {data_result.get('count', 0)}")
                        
                        # 准备策略输入
                        stocks = []
                        if 'hot_sectors' in data_result:
                            for sector in data_result['hot_sectors']:
                                stocks.append({
                                    "symbol": sector.get('code', ''),
                                    "name": sector.get('name', ''),
                                    "gain": sector.get('gain', 0)
                                })
                        
                        # 测试策略员
                        strategy_url = f"{self.base_urls['strategy']}/strategy/run"
                        strategy_payload = {"stocks": stocks, "params": {}}
                        
                        logger.info("   2. 向策略员提交选股任务...")
                        async with session.post(strategy_url, json=strategy_payload, timeout=10) as strategy_response:
                            if strategy_response.status == 200:
                                strategy_result = await strategy_response.json()
                                logger.info(f"      ✅ 策略运行成功，选中股票: {strategy_result.get('count', 0)}只")
                                
                                # 显示结果
                                if 'selected_stocks' in strategy_result:
                                    logger.info("      📊 选股结果:")
                                    for i, stock in enumerate(strategy_result['selected_stocks'][:3], 1):
                                        logger.info(f"         {i}. {stock.get('symbol')} - {stock.get('name')}")
                                
                                return True
                            else:
                                logger.error(f"      ❌ 策略运行失败: HTTP {strategy_response.status}")
                                return False
                    else:
                        logger.error(f"      ❌ 数据获取失败: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"   ❌ 通信测试异常: {e}")
            return False
    
    async def run_test(self):
        """运行完整测试"""
        logger.info("=" * 60)
        logger.info("🧪 开始系统集成测试")
        logger.info("=" * 60)
        
        # 启动Agent
        agents_started = []
        
        # 启动数据员
        if await self.start_agent("data_collector", "data_collector.py"):
            agents_started.append("data_collector")
            await self.check_agent_health("data_collector", 18990)
        
        # 启动策略员（简化版）
        if await self.start_agent("strategy_engine", "strategy_engine_simple.py"):
            agents_started.append("strategy_engine")
            await self.check_agent_health("strategy_engine", 18891)
        
        if len(agents_started) < 2:
            logger.error("❌ Agent启动失败，无法进行集成测试")
            return False
        
        # 等待Agent完全启动
        logger.info("⏳ 等待Agent完全启动...")
        await asyncio.sleep(2)
        
        # 测试通信
        communication_ok = await self.test_agent_communication()
        
        # 测试结果
        logger.info("\n" + "=" * 60)
        logger.info("📊 测试结果")
        logger.info("=" * 60)
        
        logger.info(f"✅ Agent启动: {len(agents_started)}/2")
        logger.info(f"✅ Agent通信: {'通过' if communication_ok else '失败'}")
        
        if len(agents_started) == 2 and communication_ok:
            logger.info("\n🎉 系统集成测试通过！")
            logger.info("   数据员和策略员可以正常通信协作")
            return True
        else:
            logger.info("\n⚠️  系统集成测试部分通过")
            logger.info("   需要进一步调试")
            return False
    
    def cleanup(self):
        """清理进程"""
        logger.info("🧹 清理进程...")
        for agent_name, info in self.agents.items():
            if info["process"] and info["process"].poll() is None:
                info["process"].terminate()
                info["process"].wait(timeout=5)
                logger.info(f"   已停止 {agent_name}")

async def main():
    """主函数"""
    test = SystemIntegrationTest()
    
    try:
        success = await test.run_test()
        
        # 保持运行一段时间以便观察
        if success:
            logger.info("\n💡 系统运行中，按 Ctrl+C 停止测试...")
            await asyncio.sleep(10)
        
    except KeyboardInterrupt:
        logger.info("\n👋 收到中断信号")
    except Exception as e:
        logger.error(f"测试异常: {e}")
    finally:
        test.cleanup()

if __name__ == "__main__":
    asyncio.run(main())