#!/usr/bin/env python3
"""
快速测试 - 验证所有Agent的基本功能
"""

import asyncio
import aiohttp
import subprocess
import time
import os
import sys

async def test_agent(agent_name, port, agent_file):
    """测试单个Agent"""
    print(f"🚀 测试 {agent_name} (端口: {port})...")
    
    # 启动Agent
    cmd = ["python3", agent_file]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # 等待启动
    time.sleep(3)
    
    if process.poll() is not None:
        print(f"   ❌ {agent_name} 启动失败")
        return None
    
    print(f"   ✅ {agent_name} 启动成功")
    
    # 测试健康检查
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:{port}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 健康检查通过: {data.get('status', 'unknown')}")
                    return process
                else:
                    print(f"   ❌ 健康检查失败: HTTP {response.status}")
                    process.terminate()
                    return None
    except Exception as e:
        print(f"   ❌ 健康检查异常: {e}")
        process.terminate()
        return None

async def main():
    """主函数"""
    print("=" * 60)
    print("⚡ OpenClaw股票系统快速测试")
    print("=" * 60)
    
    agents = [
        ("数据员", 18990, "data_collector.py"),
        ("策略员", 18891, "strategy_engine_simple.py"),
        ("回测员", 18892, "backtester_simple.py"),
        ("风控员", 18893, "risk_manager_simple.py"),
        ("主Agent", 18889, "master_agent_simple.py"),
    ]
    
    processes = []
    
    try:
        # 测试所有Agent
        for agent_name, port, agent_file in agents:
            process = await test_agent(agent_name, port, agent_file)
            if process:
                processes.append((agent_name, process))
            else:
                print(f"⚠️  {agent_name} 测试失败")
        
        print(f"\n📊 测试结果: {len(processes)}/{len(agents)} 个Agent通过")
        
        if len(processes) == len(agents):
            print("\n🎉 所有Agent测试通过！")
            
            # 测试主Agent协调能力
            print("\n🔗 测试主Agent协调能力...")
            try:
                async with aiohttp.ClientSession() as session:
                    response = await session.get("http://localhost:18889/health", timeout=10)
                    if response.status == 200:
                        data = await response.json()
                        agent_status = data.get("agent_status", {})
                        
                        print("子Agent状态:")
                        healthy = 0
                        for agent, status in agent_status.items():
                            if "healthy" in str(status):
                                print(f"   ✅ {agent}: {status}")
                                healthy += 1
                            else:
                                print(f"   ❌ {agent}: {status}")
                        
                        print(f"\n健康Agent: {healthy}/{len(agent_status)}")
                        
                        if healthy == len(agent_status):
                            print("✅ 主Agent协调测试通过！")
                        else:
                            print("⚠️  主Agent协调测试部分失败")
                    else:
                        print(f"❌ 主Agent健康检查失败: HTTP {response.status}")
            except Exception as e:
                print(f"❌ 协调测试异常: {e}")
        
        # 保持运行几秒钟
        print("\n⏳ 系统运行中...")
        time.sleep(5)
        
    finally:
        # 清理进程
        print("\n🧹 清理进程...")
        for agent_name, process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=3)
                print(f"   已停止 {agent_name}")

if __name__ == "__main__":
    asyncio.run(main())