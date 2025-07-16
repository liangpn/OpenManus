"""
测试真实MCP连接
"""

import asyncio
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_mcp_bridge import RealMCPBridge

async def test_real_mcp_connection():
    """测试真实MCP连接"""
    bridge = RealMCPBridge("http://localhost:4000/mcp")
    
    print("🧪 开始真实MCP连接测试...")
    
    try:
        # 测试连接
        success = await bridge.connect()
        
        if success:
            print("✅ 连接成功！")
            
            # 获取工具列表
            tools = await bridge.list_tools()
            print(f"📋 可用工具数量：{len(tools)}")
            
            for tool in tools:
                print(f"   🔧 {tool['name']}: {tool['description']}")
            
            # 测试特定工具（如果存在）
            tool_names = [t['name'] for t in tools]
            
            # 测试getPOI工具
            if 'getPOI' in tool_names:
                print("\n🧪 测试 getPOI 工具...")
                result = await bridge.call_tool(
                    "getPOI",
                    {
                        "x_position": "116.3974",  # 改为字符串类型
                        "y_position": "39.9093",
                        "afdd": "北京市朝阳区测试地址"
                    }
                )
                
                print(f"   结果：{result.success}")
                if result.success:
                    print(f"   数据：{result.data}")
                else:
                    print(f"   错误：{result.error}")
            
            # 测试showQw工具
            if 'showQw' in tool_names:
                print("\n🧪 测试 showQw 工具...")
                result = await bridge.call_tool(
                    "showQw",
                    {"gxdwdm": "110105"}
                )
                
                print(f"   结果：{result.success}")
                if result.success:
                    print(f"   数据：{result.data}")
                else:
                    print(f"   错误：{result.error}")
            
            # 测试callPhone工具
            if 'callPhone' in tool_names:
                print("\n🧪 测试 callPhone 工具...")
                result = await bridge.call_tool(
                    "callPhone",
                    {"phone": "13800138000"}
                )
                
                print(f"   结果：{result.success}")
                if result.success:
                    print(f"   数据：{result.data}")
                else:
                    print(f"   错误：{result.error}")
            
        else:
            print("❌ 连接失败")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bridge.disconnect()
        print("🔌 连接已关闭")

async def test_connection_fallback():
    """测试连接失败回退"""
    print("\n🧪 测试连接失败回退...")
    
    # 测试无效的MCP服务器
    bridge = RealMCPBridge("http://localhost:9999/mcp")
    
    try:
        success = await bridge.connect()
        if not success:
            print("✅ 正确处理了连接失败")
        
        # 测试工具调用在连接失败时
        result = await bridge.call_tool("test", {})
        print(f"✅ 正确处理了工具调用失败：{result.error}")
        
    except Exception as e:
        print(f"✅ 正确处理了异常: {e}")
    finally:
        await bridge.disconnect()

async def main():
    """主测试函数"""
    print("🚀 开始真实MCP服务器测试...")
    print("=" * 50)
    
    # 测试真实MCP连接
    await test_real_mcp_connection()
    
    # 测试连接失败回退
    await test_connection_fallback()
    
    print("\n🎯 测试完成！")

if __name__ == "__main__":
    asyncio.run(main())