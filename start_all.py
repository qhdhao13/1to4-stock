#!/usr/bin/env python3
"""
启动脚本：一键启动一主四辅股票系统
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
from typing import List, Dict
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/startup_{time.strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Startup")

class StockSystemStarter:
    """股票系统启动器"""
    
    def __init__(self):
        self.processes = {}  # 进程字典
        self.agents = [
            {"name": "master_agent", "port": 18889, "file": "master_agent.py", "desc": "主Agent-总指挥"},
            {"name": "data_collector", "port": 18990, "file": "data_collector.py", "desc": "辅1-数据员"},
            {"name": "strategy_engine", "port": 18891, "file": "strategy_engine.py", "desc": "辅2-策略员"},
            {"name": "backtester", "port": 18892, "file": "backtester.py", "desc": "辅3-回测员"},
            {"name": "risk_manager", "port": 18893, "file": "risk_manager.py", "desc": "辅4-风控员"},
        ]
        
        # 设置工作目录
        self.workspace = os.path.dirname(os.path.abspath(__file__))
        
        # 创建必要目录
        self._create_directories()
    
    def _create_directories(self):
        """创建必要目录"""
        directories = ["logs", "data", "reports", "cache"]
        for dir_name in directories:
            dir_path = os.path.join(self.workspace, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"📁 创建目录: {dir_path}")
    
    def start_agent(self, agent_info: Dict) -> bool:
        """启动单个Agent"""
        try:
            agent_file = os.path.join(self.workspace, agent_info["file"])
            
            if not os.path.exists(agent_file):
                logger.error(f"❌ Agent文件不存在: {agent_file}")
                return False
            
            # 启动进程
            cmd = [sys.executable, agent_file]
            env = os.environ.copy()
            env["PYTHONPATH"] = self.workspace
            
            process = subprocess.Popen(
                cmd,
                cwd=self.workspace,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 保存进程信息
            self.processes[agent_info["name"]] = {
                "process": process,
                "port": agent_info["port"],
                "desc": agent_info["desc"],
                "start_time": time.time()
            }
            
            logger.info(f"🚀 启动 {agent_info['desc']} (端口: {agent_info['port']}, PID: {process.pid})")
            
            # 等待一小段时间检查进程状态
            time.sleep(2)
            if process.poll() is not None:
                # 进程已退出
                stdout, stderr = process.communicate()
                logger.error(f"❌ {agent_info['desc']} 启动失败:")
                if stdout:
                    logger.error(f"   stdout: {stdout[:500]}")
                if stderr:
                    logger.error(f"   stderr: {stderr[:500]}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 启动 {agent_info['desc']} 失败: {str(e)}")
            return False
    
    def check_agent_health(self, agent_info: Dict) -> bool:
        """检查Agent健康状态"""
        import requests
        
        try:
            url = f"http://localhost:{agent_info['port']}/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    logger.info(f"✅ {agent_info['desc']} 健康检查通过")
                    return True
                else:
                    logger.warning(f"⚠️ {agent_info['desc']} 状态异常: {data}")
                    return False
            else:
                logger.warning(f"⚠️ {agent_info['desc']} 健康检查失败: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.warning(f"⚠️ {agent_info['desc']} 连接失败，可能尚未完全启动")
            return False
        except Exception as e:
            logger.warning(f"⚠️ {agent_info['desc']} 健康检查异常: {str(e)}")
            return False
    
    def start_all_agents(self) -> bool:
        """启动所有Agent"""
        logger.info("=" * 60)
        logger.info("🚀 开始启动一主四辅股票系统")
        logger.info("=" * 60)
        
        # 按依赖顺序启动
        startup_order = [
            "data_collector",  # 辅1：数据员（无依赖）
            "strategy_engine", # 辅2：策略员（依赖数据员）
            "backtester",      # 辅3：回测员（依赖策略员）
            "risk_manager",    # 辅4：风控员（依赖策略员和回测员）
            "master_agent",    # 主Agent（依赖所有辅Agent）
        ]
        
        success_count = 0
        failed_agents = []
        
        for agent_name in startup_order:
            agent_info = next((a for a in self.agents if a["name"] == agent_name), None)
            if not agent_info:
                logger.error(f"❌ 未知的Agent: {agent_name}")
                failed_agents.append(agent_name)
                continue
            
            logger.info(f"🔧 启动 {agent_info['desc']}...")
            
            if self.start_agent(agent_info):
                success_count += 1
                logger.info(f"✅ {agent_info['desc']} 启动成功")
            else:
                failed_agents.append(agent_name)
                logger.error(f"❌ {agent_info['desc']} 启动失败")
            
            # 等待一小段时间让进程稳定
            time.sleep(3)
        
        # 等待所有Agent完全启动
        logger.info("⏳ 等待Agent完全启动...")
        time.sleep(10)
        
        # 检查健康状态
        logger.info("🔍 检查Agent健康状态...")
        healthy_count = 0
        for agent_info in self.agents:
            if self.check_agent_health(agent_info):
                healthy_count += 1
        
        # 输出启动结果
        logger.info("=" * 60)
        logger.info("📊 启动结果汇总:")
        logger.info(f"  总Agent数: {len(self.agents)}")
        logger.info(f"  成功启动: {success_count}")
        logger.info(f"  健康运行: {healthy_count}")
        logger.info(f"  失败Agent: {', '.join(failed_agents) if failed_agents else '无'}")
        
        if failed_agents:
            logger.error("❌ 部分Agent启动失败，系统可能无法正常工作")
            return False
        elif healthy_count < len(self.agents):
            logger.warning("⚠️ 部分Agent健康检查未通过，但进程已启动")
            return True
        else:
            logger.info("✅ 所有Agent启动成功且健康运行!")
            return True
    
    def stop_all_agents(self):
        """停止所有Agent"""
        logger.info("🛑 正在停止所有Agent...")
        
        for agent_name, info in list(self.processes.items()):
            try:
                process = info["process"]
                desc = info["desc"]
                
                if process.poll() is None:  # 进程还在运行
                    logger.info(f"🛑 停止 {desc} (PID: {process.pid})...")
                    process.terminate()
                    
                    # 等待进程结束
                    try:
                        process.wait(timeout=10)
                        logger.info(f"✅ {desc} 已停止")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"⚠️ {desc} 未正常退出，强制终止")
                        process.kill()
                        
            except Exception as e:
                logger.error(f"❌ 停止 {agent_name} 失败: {str(e)}")
        
        self.processes.clear()
        logger.info("✅ 所有Agent已停止")
    
    def monitor_agents(self):
        """监控Agent运行状态"""
        logger.info("👀 开始监控Agent运行状态...")
        logger.info("按 Ctrl+C 停止系统")
        
        try:
            while True:
                time.sleep(30)  # 每30秒检查一次
                
                # 检查进程状态
                for agent_name, info in list(self.processes.items()):
                    process = info["process"]
                    desc = info["desc"]
                    
                    if process.poll() is not None:  # 进程已退出
                        logger.error(f"❌ {desc} 进程已退出 (退出码: {process.returncode})")
                        
                        # 尝试重新启动
                        logger.info(f"🔄 尝试重新启动 {desc}...")
                        agent_info = next((a for a in self.agents if a["name"] == agent_name), None)
                        if agent_info and self.start_agent(agent_info):
                            logger.info(f"✅ {desc} 重新启动成功")
                        else:
                            logger.error(f"❌ {desc} 重新启动失败")
                
                # 输出状态摘要
                running_count = sum(1 for info in self.processes.values() if info["process"].poll() is None)
                logger.info(f"📈 运行状态: {running_count}/{len(self.agents)}个Agent运行中")
                
        except KeyboardInterrupt:
            logger.info("👋 收到停止信号")
            self.stop_all_agents()
    
    def run(self):
        """运行启动器"""
        try:
            # 启动所有Agent
            if not self.start_all_agents():
                logger.error("❌ 系统启动失败，请检查日志")
                self.stop_all_agents()
                return False
            
            # 启动监控
            self.monitor_agents()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("👋 收到停止信号")
            self.stop_all_agents()
            return True
        except Exception as e:
            logger.error(f"❌ 系统运行异常: {str(e)}")
            self.stop_all_agents()
            return False

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 OpenClaw 一主四辅股票系统")
    print("=" * 60)
    print("系统架构:")
    print("  主Agent (18789): 总指挥 - 任务调度、结果聚合、报告生成")
    print("  辅1数据员 (18790): 数据采集 - 热门板块、龙虎榜、基础数据")
    print("  辅2策略员 (18791): 策略引擎 - 选股规则、信号生成、交易计划")
    print("  辅3回测员 (18792): 回测验证 - 历史验证、胜率计算、风险收益")
    print("  辅4风控员 (18793): 风险控制 - 仓位管理、止损监控、风险过滤")
    print("=" * 60)
    
    starter = StockSystemStarter()
    
    # 检查端口占用
    import socket
    ports = [18789, 18790, 18791, 18792, 18793]
    occupied_ports = []
    
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        if result == 0:
            occupied_ports.append(port)
    
    if occupied_ports:
        print(f"⚠️  警告: 以下端口已被占用: {occupied_ports}")
        print("   请先停止占用这些端口的进程，或修改config.py中的端口配置")
        choice = input("是否继续启动？(y/n): ")
        if choice.lower() != 'y':
            print("👋 退出启动")
            return
    
    print("开始启动系统...")
    print("详细日志请查看 logs/ 目录")
    print("-" * 60)
    
    success = starter.run()
    
    if success:
        print("✅ 系统正常退出")
    else:
        print("❌ 系统启动或运行失败")
        sys.exit(1)

if __name__ == "__main__":
    main()