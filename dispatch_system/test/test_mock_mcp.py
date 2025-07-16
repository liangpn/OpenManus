"""
单元测试：Mock MCP客户端测试
"""

import pytest
import asyncio
from test.mock_mcp_client import mock_mcp_client, MockToolResult

class TestMockMCP:
    """测试Mock MCP客户端"""
    
    @pytest.mark.asyncio
    async def test_get_poi_success(self):
        """测试getPOI工具成功调用"""
        result = await mock_mcp_client.call_tool(
            "getPOI",
            {
                "x_position": 116.3974,
                "y_position": 39.9093,
                "afdd": "北京市朝阳区测试地址"
            }
        )
        
        assert isinstance(result, MockToolResult)
        assert result.success == True
        assert "camera_count" in result.data
        assert result.data["camera_count"] == 5
    
    @pytest.mark.asyncio
    async def test_get_poi_missing_params(self):
        """测试getPOI工具缺少参数"""
        result = await mock_mcp_client.call_tool(
            "getPOI",
            {"x_position": 116.3974}  # 缺少y_position和afdd
        )
        
        assert result.success == False
        assert "缺少必需参数" in result.error
    
    @pytest.mark.asyncio
    async def test_show_qw_success(self):
        """测试showQw工具成功调用"""
        result = await mock_mcp_client.call_tool(
            "showQw",
            {"gxdwdm": "110105"}
        )
        
        assert result.success == True
        assert "personnel" in result.data
        assert len(result.data["personnel"]) == 2
    
    @pytest.mark.asyncio
    async def test_call_phone_success(self):
        """测试callPhone工具成功调用"""
        result = await mock_mcp_client.call_tool(
            "callPhone",
            {"phone": "13800138000"}
        )
        
        assert result.success == True
        assert "call_duration" in result.data
        assert result.data["status"] == "通话已建立"
    
    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        """测试不存在的工具"""
        result = await mock_mcp_client.call_tool(
            "invalid_tool",
            {}
        )
        
        assert result.success == False
        assert "不存在" in result.error
    
    def test_list_tools(self):
        """测试工具列表"""
        tools = mock_mcp_client.list_tools()
        assert len(tools) == 3
        tool_names = [tool["name"] for tool in tools]
        assert "getPOI" in tool_names
        assert "showQw" in tool_names
        assert "callPhone" in tool_names
    
    def test_get_tool_schema(self):
        """测试获取工具Schema"""
        schema = mock_mcp_client.get_tool_schema("getPOI")
        assert schema["name"] == "getPOI"
        assert "input_schema" in schema
        assert "x_position" in schema["input_schema"]["properties"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])