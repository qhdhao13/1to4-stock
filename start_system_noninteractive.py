#!/usr/bin/env python3
"""
非交互式启动股票系统
"""

import subprocess
import time
import os
import sys

def start_agent(agent_file, port):
    """启动单个Agent"""
    cmd = ["python3", agent_file]
    env = os.environ.copy()
    
    print(f"🚀 启动 {agent_file} (端口: {port})...")
    
    # 在后台启动进程
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # 等待几秒让进程启动
    time.sleep(3)
    
    # 检查进程是否还在运行
    if process.poll() is None:
        print(f"   ✅ {agent_file} 启动成功 (PID: {process.pid})")
        return process
    else:
        stdout, stderr = process.communicate()
        print(f"   ❌ {agent_file} 启动失败")
        print(f"      stderr: {stderr[:200]}")
        return None

def main():
    print("============================================================")
    print("🚀 非交互式启动股票系统")
    print("============================================================")
    
    # 定义启动顺序
    agents = [
        ("data_collector.py", 18890, "辅1-数据员"),
        ("strategy_engine.py", 18891, "辅2-策略员"),
        ("backtester.py", 18892, "辅3-回测员"),
        ("risk_manager.py", 18893, "辅4-风控员"),
        ("master_agent.py", 18889, "主Agent-总指挥"),
    ]
    
    processes = []
    
    try:
        for agent_file, port, desc in agents:
            process = start_agent(agent_file, port)
            if process:
                processes.append((agent_file, process))
            else:
                print(f"⚠️  {desc} 启动失败，继续启动其他Agent...")
        
        print("\n" + "=" * 60)
        print("📊 启动完成!")
        print("=" * 60)
        
        if processes:
            print(f"✅ 成功启动 {len(processes)}/{len(agents)} 个Agent")
            print("\n运行的Agent:")
            for agent_file, process in processes:
                print(f"  • {agent_file} (PID: {process.pid})")
        else:
            print("❌ 所有Agent启动失败")
        
        print("\n💡 系统将在后台运行")
        print("   按 Ctrl+C 停止所有进程")
        
        # 保持运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号，正在关闭所有进程...")
        for agent_file, process in processes:
            if process.poll() is None:
                process.terminate()
                print(f"   停止 {agent_file}...")
                process.wait(timeout=5)
        print("✅ 所有进程已停止")
        
    except Exception as e:
        print(f"\n❌ 启动过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()