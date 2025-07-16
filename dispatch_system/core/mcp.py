"""
MCP服务器集成 - 真实MCP工具封装
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.tool.mcp import MCPClients

@dataclass
class MCPResult:
    """MCP工具调用结果"""
    success: bool
    data: Any = None
    error: str = None
    tool_name: str = None
    parameters: Dict = None
    execution_time: float = 0.0

class MCPToolManager:
    """MCP工具管理器 - 连接真实MCP服务器"""
    
    def __init__(self, server_url: str = "http://localhost:4000/mcp"):
        """初始化MCP工具管理器
        
        Args:
            server_url: MCP服务器URL
        """
        self.server_url = server_url
        self.mcp_clients = MCPClients()
        self.connected = False
        self.tools: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self) -> bool:
        """连接到MCP服务器"""
        try:
            await self.mcp_clients.connect_streamable_http(
                server_url=self.server_url,
                server_id="dispatch_mcp_server"
            )
            
            # 获取工具列表
            tools_response = await self.mcp_clients.list_tools()
            self.tools = {
                tool.name: {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                    "original_name": tool.name
                }
                for tool in tools_response.tools
            }
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"MCP连接失败: {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        """断开MCP服务器连接"""
        try:
            await self.mcp_clients.disconnect("dispatch_mcp_server")
            self.connected = False
            self.tools.clear()
            return True
        except Exception as e:
            print(f"MCP断开失败: {e}")
            return False
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return list(self.tools.values())
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPResult:
        """执行MCP工具
        
        Args:
            tool_name: 工具名称
            parameters: 参数字典
            
        Returns:
            执行结果
        """
        import time
        start_time = time.time()
        
        if not self.connected:
            await self.connect()
            if not self.connected:
                return MCPResult(
                    success=False,
                    error="无法连接到MCP服务器",
                    tool_name=tool_name,
                    parameters=parameters
                )
        
        try:
            # 构建完整工具名
            full_tool_name = f"mcp_dispatch_mcp_server_{tool_name}"
            
            if full_tool_name not in self.mcp_clients.tool_map:
                available_tools = list(self.mcp_clients.tool_map.keys())
                return MCPResult(
                    success=False,
                    error=f"工具 {tool_name} 不可用。可用工具: {[t.split('_')[-1] for t in available_tools]}",
                    tool_name=tool_name,
                    parameters=parameters
                )
            
            # 执行工具
            tool = self.mcp_clients.tool_map[full_tool_name]
            result = await tool.execute(**parameters)
            
            execution_time = time.time() - start_time
            
            if result.error:
                return MCPResult(
                    success=False,
                    error=result.error,
                    tool_name=tool_name,
                    parameters=parameters,
                    execution_time=execution_time
                )
            else:
                return MCPResult(
                    success=True,
                    data=result.output,
                    tool_name=tool_name,
                    parameters=parameters,
                    execution_time=execution_time
                )
                
        except Exception as e:
            return MCPResult(
                success=False,
                error=f"工具执行异常: {str(e)}",
                tool_name=tool_name,
                parameters=parameters,
                execution_time=time.time() - start_time
            )
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected

# 全局MCP工具管理器
mcp_tool_manager = MCPToolManager()

# 便捷函数
async def initialize_mcp_tools() -> bool:
    """初始化MCP工具"""
    return await mcp_tool_manager.connect()

async def get_available_mcp_tools() -> List[Dict[str, Any]]:
    """获取可用MCP工具"""
    return mcp_tool_manager.get_tools()

async def execute_mcp_tool(tool_name: str, parameters: Dict[str, Any]) -> MCPResult:
    """执行MCP工具"""
    return await mcp_tool_manager.execute_tool(tool_name, parameters)

async def cleanup_mcp_tools():
    """清理MCP资源"""
    await mcp_tool_manager.disconnect()