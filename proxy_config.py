#!/usr/bin/env python3
"""
代理配置工具 - 解决AkShare网络连接问题
"""

import os
import sys
import logging
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProxyConfig")

class ProxyConfigurator:
    """代理配置器"""
    
    def __init__(self):
        self.proxy_configs = {
            "http": None,
            "https": None,
            "socks5": None
        }
        
        # 常见代理服务器（示例）
        self.common_proxies = {
            "local_socks5": "socks5://127.0.0.1:1080",
            "local_http": "http://127.0.0.1:1081",
            "test_proxy": "http://proxy.example.com:8080"
        }
    
    def detect_system_proxy(self):
        """检测系统代理设置"""
        env_vars = [
            "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
            "all_proxy", "ALL_PROXY"
        ]
        
        proxies = {}
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                proxies[var] = value
                logger.info(f"检测到环境变量 {var}: {value}")
        
        return proxies
    
    def configure_akshare_proxy(self, proxy_url: Optional[str] = None):
        """配置AkShare代理"""
        try:
            import akshare as ak
            
            if proxy_url:
                # 设置代理
                logger.info(f"设置AkShare代理: {proxy_url}")
                
                # 方法1: 通过环境变量
                os.environ["http_proxy"] = proxy_url
                os.environ["https_proxy"] = proxy_url
                
                # 方法2: 尝试直接配置（如果AkShare支持）
                try:
                    # 某些版本的AkShare可能支持直接配置
                    ak.set_proxy(proxy_url)
                    logger.info("通过ak.set_proxy()设置代理成功")
                except AttributeError:
                    logger.info("当前AkShare版本不支持直接设置代理，使用环境变量")
                
                return True
            else:
                # 清除代理设置
                os.environ.pop("http_proxy", None)
                os.environ.pop("https_proxy", None)
                logger.info("清除代理设置")
                return True
                
        except ImportError:
            logger.error("AkShare未安装")
            return False
        except Exception as e:
            logger.error(f"配置代理失败: {e}")
            return False
    
    def test_connection(self, test_url: str = "https://www.baidu.com"):
        """测试网络连接"""
        import requests
        
        proxies = {}
        if os.environ.get("http_proxy"):
            proxies = {
                "http": os.environ.get("http_proxy"),
                "https": os.environ.get("https_proxy")
            }
        
        try:
            logger.info(f"测试连接: {test_url}")
            response = requests.get(test_url, proxies=proxies, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ 连接成功 (状态码: {response.status_code})")
                return True
            else:
                logger.warning(f"⚠️  连接异常 (状态码: {response.status_code})")
                return False
                
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False
    
    def test_akshare_with_proxy(self, proxy_url: Optional[str] = None):
        """使用代理测试AkShare连接"""
        # 配置代理
        if proxy_url:
            self.configure_akshare_proxy(proxy_url)
        
        try:
            import akshare as ak
            
            logger.info("测试AkShare简单数据获取...")
            
            # 测试简单的数据获取
            stock_list = ak.stock_info_a_code_name()
            
            if not stock_list.empty:
                logger.info(f"✅ AkShare连接成功，获取到 {len(stock_list)} 只股票")
                return True
            else:
                logger.warning("⚠️  AkShare返回空数据")
                return False
                
        except Exception as e:
            logger.error(f"❌ AkShare测试失败: {e}")
            return False
    
    def auto_configure(self):
        """自动配置代理"""
        logger.info("=" * 60)
        logger.info("🔄 开始自动代理配置")
        logger.info("=" * 60)
        
        # 1. 检测当前网络状态
        logger.info("1. 检测当前网络状态...")
        direct_connection = self.test_connection()
        
        if direct_connection:
            logger.info("   ✅ 直接连接正常")
            
            # 测试AkShare
            logger.info("2. 测试AkShare直接连接...")
            akshare_direct = self.test_akshare_with_proxy(None)
            
            if akshare_direct:
                logger.info("   ✅ AkShare直接连接正常，无需代理")
                return {"status": "success", "proxy_required": False}
            else:
                logger.info("   ❌ AkShare直接连接失败，尝试代理")
        else:
            logger.info("   ❌ 直接连接失败，需要代理")
        
        # 2. 尝试常见代理
        logger.info("3. 尝试常见代理配置...")
        
        for proxy_name, proxy_url in self.common_proxies.items():
            logger.info(f"   尝试代理: {proxy_name} ({proxy_url})")
            
            # 测试代理连接
            self.configure_akshare_proxy(proxy_url)
            proxy_test = self.test_connection()
            
            if proxy_test:
                logger.info(f"      ✅ 代理连接正常")
                
                # 测试AkShare
                akshare_with_proxy = self.test_akshare_with_proxy(proxy_url)
                if akshare_with_proxy:
                    logger.info(f"      ✅ AkShare通过代理连接成功")
                    return {
                        "status": "success",
                        "proxy_required": True,
                        "proxy_name": proxy_name,
                        "proxy_url": proxy_url
                    }
                else:
                    logger.info(f"      ❌ AkShare通过代理仍然失败")
            else:
                logger.info(f"      ❌ 代理连接失败")
        
        logger.info("❌ 所有代理配置尝试失败")
        return {"status": "failed", "proxy_required": True}

def main():
    """主函数"""
    configurator = ProxyConfigurator()
    
    print("=" * 60)
    print("🔧 AkShare代理配置工具")
    print("=" * 60)
    print("选项:")
    print("  1. 自动配置代理")
    print("  2. 测试当前连接")
    print("  3. 设置指定代理")
    print("  4. 清除代理设置")
    print("  5. 退出")
    
    try:
        choice = input("\n请选择 (1-5): ").strip()
        
        if choice == "1":
            result = configurator.auto_configure()
            print(f"\n配置结果: {result}")
            
        elif choice == "2":
            print("\n测试网络连接...")
            configurator.test_connection()
            print("\n测试AkShare连接...")
            configurator.test_akshare_with_proxy()
            
        elif choice == "3":
            proxy_url = input("请输入代理URL (如 http://127.0.0.1:1080): ").strip()
            if proxy_url:
                configurator.configure_akshare_proxy(proxy_url)
                print(f"已设置代理: {proxy_url}")
                
        elif choice == "4":
            configurator.configure_akshare_proxy(None)
            print("已清除代理设置")
            
        elif choice == "5":
            print("退出")
            
        else:
            print("无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 已取消")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()