"""
真实MCP桥接工具 - 接入真实MCP服务器
"""

import asyncio
from typing import Dict, Any, List, Optional
import uuid
from dataclasses import dataclass
import sys
import os

# 添加父目录到路径以导入MCP客户端
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tool.mcp import MCPClients

@dataclass
class RealToolResult:
    """真实工具调用结果"""
    success: bool
    data: Any = None
    error: str = None
    tool_name: str = None
    parameters: Dict = None
    execution_time: float = 0.0

class RealMCPBridge:
    """真实MCP桥接类，连接真实MCP服务器"""
    
    def __init__(self, server_url: str = "http://localhost:4000/mcp"):
        """初始化真实MCP桥接
        
        Args:
            server_url: MCP服务器URL
        """
        self.server_url = server_url
        self.mcp_clients = MCPClients()
        self.session_tools: Dict[str, Dict[str, Any]] = {}
        self.connected = False
    
    async def connect(self) -> bool:
        """连接到真实MCP服务器"""
        try:
            print(f"🔗 连接到MCP服务器: {self.server_url}")
            await self.mcp_clients.connect_streamable_http(
                server_url=self.server_url,
                server_id="dispatch_mcp_server"
            )
            
            # 获取可用工具
            tools_response = await self.mcp_clients.list_tools()
            self.session_tools["default"] = {
                tool.name: {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                    "original_name": tool.name
                }
                for tool in tools_response.tools
            }
            
            self.connected = True
            print(f"✅ 已连接到MCP服务器，可用工具：{list(self.session_tools['default'].keys())}")
            return True
            
        except Exception as e:
            print(f"❌ 连接MCP服务器失败: {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        """断开与MCP服务器的连接"""
        try:
            await self.mcp_clients.disconnect("dispatch_mcp_server")
            self.connected = False
            self.session_tools.clear()
            print("🔗 已断开与MCP服务器的连接")
            return True
        except Exception as e:
            print(f"❌ 断开连接失败: {e}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        if not self.connected:
            await self.connect()
        
        if not self.connected:
            return []
        
        return list(self.session_tools.get("default", {}).values())
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> RealToolResult:
        """调用真实MCP工具
        
        Args:
            tool_name: 工具名称
            parameters: 参数
            
        Returns:
            工具调用结果
        """
        import time
        start_time = time.time()
        
        if not self.connected:
            await self.connect()
        
        if not self.connected:
            return RealToolResult(
                success=False,
                error="无法连接到MCP服务器",
                tool_name=tool_name,
                parameters=parameters
            )
        
        try:
            # 获取真实工具
            full_tool_name = f"mcp_dispatch_mcp_server_{tool_name}"
            if full_tool_name not in self.mcp_clients.tool_map:
                available_tools = list(self.mcp_clients.tool_map.keys())
                return RealToolResult(
                    success=False,
                    error=f"工具 {tool_name} 不可用。可用工具: {available_tools}",
                    tool_name=tool_name,
                    parameters=parameters
                )
            
            # 调用真实工具
            tool = self.mcp_clients.tool_map[full_tool_name]
            result = await tool.execute(**parameters)
            
            execution_time = time.time() - start_time
            
            if result.error:
                return RealToolResult(
                    success=False,
                    error=result.error,
                    tool_name=tool_name,
                    parameters=parameters,
                    execution_time=execution_time
                )
            else:
                return RealToolResult(
                    success=True,
                    data=result.output,
                    tool_name=tool_name,
                    parameters=parameters,
                    execution_time=execution_time
                )
                
        except Exception as e:
            return RealToolResult(
                success=False,
                error=f"工具调用异常: {str(e)}",
                tool_name=tool_name,
                parameters=parameters,
                execution_time=time.time() - start_time
            )
    
    def get_available_tools(self) -> List[str]:
        """获取可用工具名称列表"""
        if not self.connected:
            return []
        
        return list(self.session_tools.get("default", {}).keys())
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected

# 全局真实MCP桥接实例
real_mcp_bridge = RealMCPBridge("http://localhost:4000/mcp")

# 测试函数
async def test_real_mcp_connection():
    """测试真实MCP连接"""
    bridge = RealMCPBridge("http://localhost:4000/mcp")
    
    try:
        success = await bridge.connect()
        
        if success:
            tools = await bridge.list_tools()
            print(f"✅ 已连接，可用工具：{len(tools)} 个")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
            
            # 测试调用（如果有工具）
            if tools:
                first_tool = tools[0]
                print(f"\n🧪 测试调用工具：{first_tool['name']}")
                # 这里可以根据实际工具参数进行测试
        else:
            print("❌ 连接失败")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
    finally:
        await bridge.disconnect()

async def main():
    """主测试函数"""
    print("🧪 开始真实MCP连接测试...")
    await test_real_mcp_connection()

if __name__ == "__main__":
    asyncio.run(main())