"""
单元测试：MCP桥接工具测试
"""

import asyncio
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_bridge import MCPBridge, ToolResult
from test.mock_mcp_client import mock_mcp_client

async def test_mcp_bridge_initialization():
    """测试桥接初始化"""
    bridge = MCPBridge()
    session_id = "test-session-001"
    
    # 测试工具初始化
    tools = await bridge.initialize_tools(session_id)
    
    assert len(tools) == 3
    assert "getPOI" in [tool["name"] for tool in tools]
    assert "showQw" in [tool["name"] for tool in tools]
    assert "callPhone" in [tool["name"] for tool in tools]
    
    print("✅ 测试通过：桥接初始化")

async def test_get_poi_tool_call():
    """测试getPOI工具调用"""
    bridge = MCPBridge()
    session_id = "test-session-002"
    
    # 初始化会话工具
    await bridge.initialize_tools(session_id)
    
    # 调用工具
    result = await bridge.call_tool(
        session_id,
        "getPOI",
        {
            "x_position": 116.3974,
            "y_position": 39.9093,
            "afdd": "北京市朝阳区测试地址"
        }
    )
    
    assert isinstance(result, ToolResult)
    assert result.tool_name == "getPOI"
    assert result.parameters["x_position"] == 116.3974
    assert result.execution_time >= 0
    
    print(f"✅ 测试通过：getPOI工具调用，执行时间：{result.execution_time:.3f}s")
    if result.success:
        print(f"   结果：{result.data.get('message', '成功')}")
    else:
        print(f"   错误：{result.error}")

async def test_show_qw_tool_call():
    """测试showQw工具调用"""
    bridge = MCPBridge()
    session_id = "test-session-003"
    
    await bridge.initialize_tools(session_id)
    
    result = await bridge.call_tool(
        session_id,
        "showQw",
        {"gxdwdm": "110105"}
    )
    
    assert isinstance(result, ToolResult)
    assert result.tool_name == "showQw"
    assert result.parameters["gxdwdm"] == "110105"
    
    print(f"✅ 测试通过：showQw工具调用")

async def test_call_phone_tool_call():
    """测试callPhone工具调用"""
    bridge = MCPBridge()
    session_id = "test-session-004"
    
    await bridge.initialize_tools(session_id)
    
    result = await bridge.call_tool(
        session_id,
        "callPhone",
        {"phone": "13800138000"}
    )
    
    assert isinstance(result, ToolResult)
    assert result.tool_name == "callPhone"
    assert result.parameters["phone"] == "13800138000"
    
    print(f"✅ 测试通过：callPhone工具调用")

async def test_tool_not_found():
    """测试工具不存在的情况"""
    bridge = MCPBridge()
    session_id = "test-session-005"
    
    await bridge.initialize_tools(session_id)
    
    result = await bridge.call_tool(
        session_id,
        "invalid_tool",
        {}
    )
    
    assert result.success == False
    assert "不可用" in result.error
    
    print(f"✅ 测试通过：工具不存在处理")

async def test_missing_parameters():
    """测试缺少参数的情况"""
    bridge = MCPBridge()
    session_id = "test-session-006"
    
    await bridge.initialize_tools(session_id)
    
    result = await bridge.call_tool(
        session_id,
        "getPOI",
        {"x_position": 116.3974}  # 缺少必需参数
    )
    
    assert result.success == False
    assert "缺少必需参数" in result.error
    
    print(f"✅ 测试通过：缺少参数处理")

async def test_session_isolation():
    """测试会话隔离"""
    bridge = MCPBridge()
    
    session1 = "session-001"
    session2 = "session-002"
    
    # 初始化两个会话
    await bridge.initialize_tools(session1)
    await bridge.initialize_tools(session2)
    
    # 验证工具列表隔离
    tools1 = bridge.get_available_tools(session1)
    tools2 = bridge.get_available_tools(session2)
    
    assert set(tools1) == set(tools2)
    assert len(tools1) == 3
    
    print(f"✅ 测试通过：会话隔离验证")

async def main():
    """运行所有测试"""
    print("🧪 开始MCP桥接测试...")
    
    try:
        await test_mcp_bridge_initialization()
        await test_get_poi_tool_call()
        await test_show_qw_tool_call()
        await test_call_phone_tool_call()
        await test_tool_not_found()
        await test_missing_parameters()
        await test_session_isolation()
        
        print("\n🎉 所有测试通过！MCP桥接功能正常")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())