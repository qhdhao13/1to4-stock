#!/usr/bin/env python3
"""
测试脚本：测试一主四辅股票系统
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_agent(port: int, endpoint: str, data: dict = None) -> dict:
    """测试单个Agent"""
    try:
        url = f"http://localhost:{port}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            if data:
                async with session.post(url, json=data, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"HTTP {response.status}", "text": await response.text()}
            else:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"HTTP {response.status}", "text": await response.text()}
    except Exception as e:
        return {"error": str(e)}

async def test_all_agents():
    """测试所有Agent"""
    print("=" * 60)
    print("🧪 开始测试一主四辅股票系统")
    print("=" * 60)
    
    agents = [
        {"name": "数据员", "port": 18890, "endpoint": "/health"},
        {"name": "策略员", "port": 18891, "endpoint": "/health"},
        {"name": "回测员", "port": 18892, "endpoint": "/health"},
        {"name": "风控员", "port": 18893, "endpoint": "/health"},
        {"name": "主Agent", "port": 18889, "endpoint": "/health"},
    ]
    
    results = {}
    
    for agent in agents:
        print(f"🔍 测试 {agent['name']} (端口: {agent['port']})...")
        
        result = await test_agent(agent['port'], agent['endpoint'])
        
        if "error" not in result:
            print(f"  ✅ {agent['name']} 健康检查通过")
            results[agent['name']] = "✅ 健康"
        else:
            print(f"  ❌ {agent['name']} 健康检查失败: {result.get('error', '未知错误')}")
            results[agent['name']] = f"❌ 失败: {result.get('error', '未知错误')}"
        
        time.sleep(1)
    
    # 测试数据员功能
    print("\n📊 测试数据员功能...")
    data_result = await test_agent(18790, "/data/hot_sectors", {"days": 3, "count": 5})
    if "error" not in data_result:
        print(f"  ✅ 数据员功能正常，获取到 {len(data_result.get('hot_sectors', []))} 个热门板块")
    else:
        print(f"  ❌ 数据员功能异常: {data_result.get('error', '未知错误')}")
    
    # 测试策略员功能
    print("\n🎯 测试策略员功能...")
    strategy_result = await test_agent(18791, "/strategy/run", {
        "hot_sectors": [{"code": "BK0481", "name": "半导体", "gain": 5.2}],
        "filters": {
            "max_price": 50,
            "max_total_gain": 0.3,
            "min_market_cap": 50,
        }
    })
    if "error" not in strategy_result:
        print(f"  ✅ 策略员功能正常，生成 {len(strategy_result.get('signals', []))} 个信号")
    else:
        print(f"  ❌ 策略员功能异常: {strategy_result.get('error', '未知错误')}")
    
    # 测试主Agent任务提交
    print("\n🚀 测试主Agent任务提交...")
    task_result = await test_agent(18789, "/task/submit", {"type": "manual_analysis", "params": {"test": True}})
    if "error" not in task_result:
        print(f"  ✅ 主Agent任务提交正常")
    else:
        print(f"  ❌ 主Agent任务提交异常: {task_result.get('error', '未知错误')}")
    
    print("\n" + "=" * 60)
    print("📋 测试结果汇总:")
    print("=" * 60)
    
    for agent_name, status in results.items():
        print(f"{agent_name:10} : {status}")
    
    # 判断整体状态
    all_healthy = all("✅" in status for status in results.values())
    
    if all_healthy:
        print("\n🎉 所有Agent测试通过！系统可以正常启动。")
        print("\n🚀 启动命令:")
        print("  cd /Users/mac_qhdhao/.openclaw/workspace/stock_system")
        print("  python3 start_all.py")
    else:
        print("\n⚠️  部分Agent测试失败，请检查:")
        print("  1. Agent进程是否已启动")
        print("  2. 端口是否被占用")
        print("  3. 依赖库是否安装")
        print("\n💡 启动单个Agent测试:")
        print("  python3 master_agent.py")
        print("  python3 data_collector.py")
        print("  python3 strategy_engine.py")
        print("  python3 backtester.py")
        print("  python3 risk_manager.py")

async def quick_start_test():
    """快速启动测试"""
    print("🚀 快速启动测试...")
    
    # 检查端口占用
    import socket
    ports = [18789, 18790, 18791, 18792, 18793]
    
    print("🔍 检查端口占用...")
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        if result == 0:
            print(f"  ⚠️  端口 {port} 已被占用")
        else:
            print(f"  ✅ 端口 {port} 可用")
    
    print("\n💡 建议启动顺序:")
    print("  1. 启动数据员: python3 data_collector.py")
    print("  2. 启动策略员: python3 strategy_engine.py")
    print("  3. 启动回测员: python3 backtester.py")
    print("  4. 启动风控员: python3 risk_manager.py")
    print("  5. 启动主Agent: python3 master_agent.py")
    print("\n  或使用一键启动: python3 start_all.py")

def main():
    """主函数"""
    print("OpenClaw 一主四辅股票系统测试工具")
    print("=" * 60)
    
    print("请选择测试模式:")
    print("1. 完整测试（需要所有Agent已启动）")
    print("2. 快速启动测试（检查端口和依赖）")
    print("3. 退出")
    
    choice = input("\n请输入选择 (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(test_all_agents())
    elif choice == "2":
        asyncio.run(quick_start_test())
    elif choice == "3":
        print("👋 退出测试")
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()