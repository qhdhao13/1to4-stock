#!/usr/bin/env python3
"""
优化版AkShare测试 - 添加超时和重试机制
"""

import sys
import time
import asyncio
import aiohttp
from datetime import datetime
import signal
from functools import wraps

print("🔍 优化版AkShare数据源连接测试")
print("=" * 60)

# 超时装饰器
def timeout(seconds=10):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def handler(signum, frame):
                raise TimeoutError(f"函数执行超时 ({seconds}秒)")
            
            # 设置信号处理器
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # 取消闹钟
                return result
            except TimeoutError:
                raise
            finally:
                signal.alarm(0)  # 确保总是取消闹钟
        return wrapper
    return decorator

# 测试1：检查Python环境
print("1. 检查Python环境:")
print(f"   Python版本: {sys.version}")
print(f"   当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 测试2：尝试导入AkShare
print("\n2. 测试AkShare导入:")
try:
    import akshare as ak
    print(f"   ✅ AkShare导入成功")
    print(f"   AkShare版本: {ak.__version__}")
except ImportError as e:
    print(f"   ❌ AkShare导入失败: {e}")
    print("   请运行: pip install akshare")
    sys.exit(1)

# 测试3：测试简单数据获取（带超时）
print("\n3. 测试简单数据获取（带10秒超时）:")

@timeout(10)
def test_simple_data():
    """测试简单数据获取"""
    try:
        # 测试股票列表 - 这个通常比较快
        print("   测试股票列表...")
        stock_list = ak.stock_info_a_code_name()
        if not stock_list.empty:
            print(f"   ✅ 股票列表获取成功")
            print(f"   股票数量: {len(stock_list)}")
            return True
        else:
            print("   ⚠️  获取到空数据表")
            return False
    except TimeoutError as e:
        print(f"   ⏰ 超时: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

test_simple_data()

# 测试4：测试异步数据获取
print("\n4. 测试异步数据获取（优化性能）:")

async def fetch_with_retry(session, url, retries=3, timeout=10):
    """带重试的异步获取"""
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"   尝试 {attempt+1}/{retries}: HTTP {response.status}")
        except Exception as e:
            print(f"   尝试 {attempt+1}/{retries}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(1)  # 等待1秒后重试
    return None

async def test_async_data():
    """测试异步数据获取"""
    try:
        # 测试网络连接
        async with aiohttp.ClientSession() as session:
            print("   测试网络连接...")
            result = await fetch_with_retry(session, "https://www.baidu.com", retries=2, timeout=5)
            if result:
                print("   ✅ 网络连接正常")
            else:
                print("   ❌ 网络连接失败")
                
        # 测试简单股票数据
        print("   测试简单股票数据...")
        try:
            # 使用昨天的日期避免实时数据问题
            yesterday = (datetime.now() - time.timedelta(days=1)).strftime("%Y%m%d")
            simple_data = ak.stock_zh_a_hist(
                symbol="000001",
                period="daily",
                start_date="20250101",
                end_date="20250110",  # 只获取少量数据
                adjust="qfq"
            )
            if not simple_data.empty:
                print(f"   ✅ 简单历史数据获取成功")
                print(f"   数据行数: {len(simple_data)}")
            else:
                print("   ⚠️  获取到空数据表")
        except Exception as e:
            print(f"   ⚠️  数据获取警告: {e}")
            
    except Exception as e:
        print(f"   ❌ 异步测试失败: {e}")

# 运行异步测试
try:
    import time as time_module
    asyncio.run(test_async_data())
except ImportError:
    print("   ⚠️  无法导入time模块，跳过异步测试")

# 测试5：数据源健康检查
print("\n5. 数据源健康检查:")

def check_data_source(name, test_func, *args, **kwargs):
    """检查数据源"""
    print(f"   检查 {name}...")
    start_time = time.time()
    try:
        result = test_func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        if result is not None and (not hasattr(result, 'empty') or not result.empty):
            print(f"   ✅ {name} 正常 (耗时: {elapsed:.2f}秒)")
            return True
        else:
            print(f"   ⚠️  {name} 返回空数据 (耗时: {elapsed:.2f}秒)")
            return False
    except TimeoutError:
        elapsed = time.time() - start_time
        print(f"   ⏰ {name} 超时 (耗时: {elapsed:.2f}秒)")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ {name} 失败: {e} (耗时: {elapsed:.2f}秒)")
        return False

# 检查各个数据源
sources_checked = 0
sources_passed = 0

# 检查股票列表
if check_data_source("股票列表", ak.stock_info_a_code_name):
    sources_checked += 1
    sources_passed += 1

# 检查指数数据（如果有）
try:
    if hasattr(ak, 'stock_zh_index_daily'):
        if check_data_source("指数数据", ak.stock_zh_index_daily, symbol="sh000001", start_date="20250101", end_date="20250110"):
            sources_checked += 1
            sources_passed += 1
except:
    print("   ⚠️  跳过指数数据检查")

print("\n" + "=" * 60)
print("📊 优化测试总结:")
print("=" * 60)

print(f"✅ AkShare模块加载成功 (版本: {ak.__version__})")
print(f"📈 数据源检查: {sources_passed}/{sources_checked} 通过")

if sources_passed > 0:
    print("\n🎉 核心数据源可用！系统可以正常获取数据。")
else:
    print("\n⚠️  数据源检查未通过，可能需要:")
    print("   1. 检查网络连接")
    print("   2. 设置代理服务器")
    print("   3. 更新AkShare到最新版本")

print("\n💡 优化建议:")
print("1. 对于实时数据，添加重试机制和超时控制")
print("2. 使用缓存减少重复请求")
print("3. 批量获取数据以提高效率")
print("4. 考虑使用本地数据源备份")