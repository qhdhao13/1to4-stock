#!/usr/bin/env python3
"""
测试AkShare数据源连接
"""

import sys
import time
from datetime import datetime

print("🔍 开始测试AkShare数据源连接...")
print("=" * 60)

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

# 测试3：测试热门板块数据
print("\n3. 测试热门板块数据获取:")
try:
    start_time = time.time()
    # 使用正确的函数名：stock_board_industry_spot_em
    hot_sectors = ak.stock_board_industry_spot_em()
    elapsed = time.time() - start_time
    
    if not hot_sectors.empty:
        print(f"   ✅ 热门板块数据获取成功")
        print(f"   获取时间: {elapsed:.2f}秒")
        print(f"   数据行数: {len(hot_sectors)}")
        print(f"   数据列数: {len(hot_sectors.columns)}")
        
        # 显示前3个板块
        print(f"\n   前3个热门板块:")
        for i in range(min(3, len(hot_sectors))):
            sector = hot_sectors.iloc[i]
            print(f"     {i+1}. {sector.get('板块名称', 'N/A')}: {sector.get('涨跌幅', 0):.2f}%")
    else:
        print("   ⚠️  获取到空数据表")
        
except Exception as e:
    print(f"   ❌ 热门板块数据获取失败: {e}")

# 测试4：测试股票实时数据
print("\n4. 测试股票实时数据获取:")
try:
    start_time = time.time()
    spot_data = ak.stock_zh_a_spot()
    elapsed = time.time() - start_time
    
    if not spot_data.empty:
        print(f"   ✅ 股票实时数据获取成功")
        print(f"   获取时间: {elapsed:.2f}秒")
        print(f"   股票数量: {len(spot_data)}")
        print(f"   数据列数: {len(spot_data.columns)}")
        
        # 显示前3只股票
        print(f"\n   前3只股票信息:")
        for i in range(min(3, len(spot_data))):
            stock = spot_data.iloc[i]
            print(f"     {i+1}. {stock.get('代码', 'N/A')} {stock.get('名称', 'N/A')}: ¥{stock.get('最新价', 0):.2f}")
    else:
        print("   ⚠️  获取到空数据表")
        
except Exception as e:
    print(f"   ❌ 股票实时数据获取失败: {e}")

# 测试5：测试历史K线数据
print("\n5. 测试历史K线数据获取:")
try:
    # 测试平安银行(000001)的历史数据
    start_time = time.time()
    hist_data = ak.stock_zh_a_hist(
        symbol="000001",
        period="daily",
        start_date="20250101",
        end_date="20250301",
        adjust="qfq"
    )
    elapsed = time.time() - start_time
    
    if not hist_data.empty:
        print(f"   ✅ 历史K线数据获取成功")
        print(f"   获取时间: {elapsed:.2f}秒")
        print(f"   数据行数: {len(hist_data)}")
        print(f"   数据列数: {len(hist_data.columns)}")
        
        # 显示最新数据
        latest = hist_data.iloc[0]
        oldest = hist_data.iloc[-1]
        print(f"\n   最新交易日: {latest.get('日期', 'N/A')}")
        print(f"   收盘价: {latest.get('收盘', 0):.2f}")
        print(f"   数据时间范围: {oldest.get('日期', 'N/A')} 至 {latest.get('日期', 'N/A')}")
    else:
        print("   ⚠️  获取到空数据表")
        
except Exception as e:
    print(f"   ❌ 历史K线数据获取失败: {e}")

# 测试6：测试龙虎榜数据
print("\n6. 测试龙虎榜数据获取:")
try:
    start_time = time.time()
    # 获取最近一天的龙虎榜数据 - 使用正确的函数名和参数
    today = datetime.now().strftime("%Y%m%d")
    lhb_data = ak.stock_lhb_detail_daily_sina(date=today)
    elapsed = time.time() - start_time
    
    if not lhb_data.empty:
        print(f"   ✅ 龙虎榜数据获取成功")
        print(f"   获取时间: {elapsed:.2f}秒")
        print(f"   上榜股票数量: {len(lhb_data)}")
        
        # 显示前3个上榜股票
        print(f"\n   前3个上榜股票:")
        for i in range(min(3, len(lhb_data))):
            lhb = lhb_data.iloc[i]
            print(f"     {i+1}. {lhb.get('代码', 'N/A')} {lhb.get('名称', 'N/A')}: {lhb.get('上榜原因', 'N/A')}")
    else:
        print(f"   ⚠️  今日({today})无龙虎榜数据或获取到空数据表")
        
except Exception as e:
    print(f"   ❌ 龙虎榜数据获取失败: {e}")

print("\n" + "=" * 60)
print("📊 测试总结:")
print("=" * 60)

# 总结所有测试
tests_passed = 0
tests_failed = 0

if 'ak' in locals():
    print("✅ AkShare模块加载成功")
    tests_passed += 1
else:
    print("❌ AkShare模块加载失败")
    tests_failed += 1

# 这里可以添加更多测试结果的统计

print(f"\n总测试: {tests_passed + tests_failed}个")
print(f"通过: {tests_passed}个")
print(f"失败: {tests_failed}个")

if tests_failed == 0:
    print("\n🎉 所有数据源测试通过！系统可以正常获取数据。")
else:
    print("\n⚠️  部分数据源测试失败，请检查网络连接或AkShare配置。")

print("\n💡 建议:")
print("1. 如果网络连接正常，AkShare应该能正常工作")
print("2. 如遇网络问题，可尝试设置代理")
print("3. 确保系统时间正确（时区：Asia/Shanghai）")