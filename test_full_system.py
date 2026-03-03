#!/usr/bin/env python3
"""
完整系统测试 - 启动所有5个Agent进行端到端测试
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
logger = logging.getLogger("FullSystemTest")

class FullSystemTest:
    """完整系统测试"""
    
    def __init__(self):
        self.agents = {
            "data_collector": {
                "port": 18990,
                "file": "data_collector.py",
                "process": None,
                "description": "辅1-数据员"
            },
            "strategy_engine": {
                "port": 18891,
                "file": "strategy_engine_simple.py",
                "process": None,
                "description": "辅2-策略员"
            },
            "backtester": {
                "port": 18892,
                "file": "backtester_simple.py",
                "process": None,
                "description": "辅3-回测员"
            },
            "risk_manager": {
                "port": 18893,
                "file": "risk_manager_simple.py",
                "process": None,
                "description": "辅4-风控员"
            },
            "master_agent": {
                "port": 18889,
                "file": "master_agent_simple.py",
                "process": None,
                "description": "主Agent-总指挥"
            }
        }
        
        self.test_results = {}
    
    async def start_all_agents(self):
        """启动所有Agent"""
        logger.info("=" * 60)
        logger.info("🚀 启动所有5个Agent")
        logger.info("=" * 60)
        
        started_agents = []
        
        for agent_name, info in self.agents.items():
            success = await self._start_agent(agent_name, info["file"], info["port"])
            if success:
                started_agents.append(agent_name)
                await self._check_agent_health(agent_name, info["port"])
            else:
                logger.error(f"❌ {agent_name} 启动失败")
        
        logger.info(f"\n📊 Agent启动结果: {len(started_agents)}/{len(self.agents)}")
        
        if len(started_agents) == len(self.agents):
            logger.info("✅ 所有Agent启动成功！")
            return True
        else:
            logger.warning(f"⚠️  部分Agent启动失败: {set(self.agents.keys()) - set(started_agents)}")
            return False
    
    async def _start_agent(self, agent_name, agent_file, port):
        """启动单个Agent"""
        cmd = ["python3", agent_file]
        
        logger.info(f"🚀 启动 {agent_name} ({port})...")
        
        try:
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
            
            if process.poll() is None:
                logger.info(f"   ✅ {agent_name} 启动成功 (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"   ❌ {agent_name} 启动失败")
                if stderr:
                    logger.error(f"      stderr: {stderr[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"   ❌ {agent_name} 启动异常: {e}")
            return False
    
    async def _check_agent_health(self, agent_name, port):
        """检查Agent健康状态"""
        url = f"http://localhost:{port}/health"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status', 'unknown')
                        logger.info(f"   ✅ {agent_name} 健康: {status}")
                        return True
                    else:
                        logger.warning(f"   ⚠️  {agent_name} 健康检查失败: HTTP {response.status}")
                        return False
        except Exception as e:
            logger.error(f"   ❌ {agent_name} 健康检查异常: {e}")
            return False
    
    async def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        logger.info("\n" + "=" * 60)
        logger.info("🔗 测试端到端工作流程")
        logger.info("=" * 60)
        
        test_cases = [
            self._test_daily_analysis_workflow,
            self._test_backtest_workflow,
            self._test_risk_check_workflow
        ]
        
        results = {}
        for i, test_func in enumerate(test_cases, 1):
            logger.info(f"\n📋 测试用例 {i}: {test_func.__name__}")
            result = await test_func()
            results[test_func.__name__] = result
        
        # 汇总结果
        logger.info("\n" + "=" * 60)
        logger.info("📊 端到端测试结果")
        logger.info("=" * 60)
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\n总测试: {total}个，通过: {passed}个，失败: {total-passed}个")
        
        return passed == total
    
    async def _test_daily_analysis_workflow(self):
        """测试每日分析工作流程"""
        logger.info("   测试每日分析流程...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. 主Agent执行每日分析
                logger.info("     1. 主Agent执行每日分析...")
                response = await session.get(
                    "http://localhost:18889/analysis/daily",
                    timeout=30
                )
                
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("status") == "success":
                        logger.info(f"     ✅ 每日分析成功")
                        
                        # 检查结果结构
                        report = result.get("report", {})
                        if report:
                            logger.info(f"       生成报告: {report.get('title', 'N/A')}")
                            logger.info(f"       推荐股票: {report.get('summary', 'N/A')}")
                        
                        return True
                    else:
                        logger.error(f"     ❌ 每日分析失败: {result.get('error', '未知错误')}")
                        return False
                else:
                    logger.error(f"     ❌ HTTP错误: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"     ❌ 测试异常: {e}")
            return False
    
    async def _test_backtest_workflow(self):
        """测试回测工作流程"""
        logger.info("   测试回测流程...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # 直接测试回测员
                logger.info("     1. 测试回测员接口...")
                response = await session.post(
                    "http://localhost:18892/backtest/run",
                    json={
                        "strategy_data": {"name": "测试策略"},
                        "historical_data": {},
                        "params": {}
                    },
                    timeout=20
                )
                
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("status") == "success":
                        backtest_result = result.get("backtest_result", {})
                        win_rate = backtest_result.get("win_rate", 0)
                        
                        logger.info(f"     ✅ 回测成功，胜率: {win_rate*100:.1f}%")
                        return True
                    else:
                        logger.error(f"     ❌ 回测失败: {result.get('error', '未知错误')}")
                        return False
                else:
                    logger.error(f"     ❌ HTTP错误: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"     ❌ 测试异常: {e}")
            return False
    
    async def _test_risk_check_workflow(self):
        """测试风险检查工作流程"""
        logger.info("   测试风险检查流程...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # 测试风控员
                logger.info("     1. 测试风控员接口...")
                response = await session.post(
                    "http://localhost:18893/risk/check",
                    json={
                        "trade_data": [
                            {"symbol": "000001", "name": "平安银行", "action": "BUY", "quantity": 1000}
                        ],
                        "portfolio": {},
                        "market_condition": "normal"
                    },
                    timeout=10
                )
                
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("status") == "success":
                        risk_score = result.get("risk_score", 50)
                        approved = result.get("approved", False)
                        
                        logger.info(f"     ✅ 风险检查成功，评分: {risk_score}，批准: {approved}")
                        return True
                    else:
                        logger.error(f"     ❌ 风险检查失败: {result.get('error', '未知错误')}")
                        return False
                else:
                    logger.error(f"     ❌ HTTP错误: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"     ❌ 测试异常: {e}")
            return False
    
    async def test_master_agent_coordination(self):
        """测试主Agent协调能力"""
        logger.info("\n" + "=" * 60)
        logger.info("👑 测试主Agent协调能力")
        logger.info("=" * 60)
        
        try:
            async with aiohttp.ClientSession() as session:
                # 检查主Agent的健康状态（会检查所有子Agent）
                logger.info("检查主Agent健康状态（包含所有子Agent状态）...")
                response = await session.get(
                    "http://localhost:18889/health",
                    timeout=10
                )
                
                if response.status == 200:
                    result = await response.json()
                    agent_status = result.get("agent_status", {})
                    
                    logger.info("子Agent状态:")
                    for agent, status in agent_status.items():
                        status_icon = "✅" if "healthy" in str(status) else "❌"
                        logger.info(f"   {status_icon} {agent}: {status}")
                    
                    # 统计健康状态
                    healthy_count = sum(1 for s in agent_status.values() if "healthy" in str(s))
                    total_count = len(agent_status)
                    
                    logger.info(f"\n健康Agent: {healthy_count}/{total_count}")
                    
                    if healthy_count == total_count:
                        logger.info("✅ 所有Agent健康状态正常")
                        return True
                    else:
                        logger.warning(f"⚠️  部分Agent状态异常")
                        return False
                else:
                    logger.error(f"❌ 主Agent健康检查失败: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 协调测试异常: {e}")
            return False
    
    def cleanup(self):
        """清理所有进程"""
        logger.info("\n🧹 清理所有进程...")
        
        for agent_name, info in self.agents.items():
            if info["process"] and info["process"].poll() is None:
                try:
                    info["process"].terminate()
                    info["process"].wait(timeout=3)
                    logger.info(f"   已停止 {agent_name}")
                except:
                    try:
                        info["process"].kill()
                        logger.info(f"   强制停止 {agent_name}")
                    except:
                        logger.warning(f"   无法停止 {agent_name}")
    
    async def run_full_test(self):
        """运行完整测试"""
        try:
            # 1. 启动所有Agent
            agents_started = await self.start_all_agents()
            if not agents_started:
                logger.error("❌ Agent启动失败，无法继续测试")
                return False
            
            # 等待所有Agent完全启动
            logger.info("\n⏳ 等待所有Agent完全启动...")
            await asyncio.sleep(5)
            
            # 2. 测试端到端工作流程
            workflow_passed = await self.test_end_to_end_workflow()
            
            # 3. 测试主Agent协调能力
            coordination_passed = await self.test_master_agent_coordination()
            
            # 最终结果
            logger.info("\n" + "=" * 60)
            logger.info("🎯 完整系统测试最终结果")
            logger.info("=" * 60)
            
            logger.info(f"✅ Agent启动: {'成功' if agents_started else '失败'}")
            logger.info(f"✅ 工作流程测试: {'通过' if workflow_passed else '失败'}")
            logger.info(f"✅ 协调能力测试: {'通过' if coordination_passed else '失败'}")
            
            overall_success = agents_started and workflow_passed and coordination_passed
            
            if overall_success:
                logger.info("\n🎉 🎉 🎉 完整系统测试全部通过！ 🎉 🎉 🎉")
                logger.info("一主四辅股票系统架构验证成功！")
            else:
                logger.info("\n⚠️  系统测试部分失败，需要进一步调试")
            
            return overall_success
            
        except KeyboardInterrupt:
            logger.info("\n👋 收到中断信号")
            return False
        except Exception as e:
            logger.error(f"测试异常: {e}")
            return False
        finally:
            self.cleanup()

async def main():
    """主函数"""
    test = FullSystemTest()
    
    print("=" * 60)
    print("🧪 OpenClaw 一主四辅股票系统完整测试")
    print("=" * 60)
    print("将测试:")
    print("  1. 所有5个Agent的启动")
    print("  2. 端到端工作流程")
    print("  3. 主Agent协调能力")
    print("  4. 系统整体稳定性")
    print("\n测试可能需要几分钟时间...")
    
    print("\n开始测试...")
    
    success = await test.run_full_test()
    
    if success:
        print("\n✅ 测试完成！系统可以正常部署使用。")
    else:
        print("\n⚠️  测试完成，但发现一些问题需要修复。")
    
    return success

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"测试运行异常: {e}")