"""
MCP桥接工具 - 连接调度系统与MCP工具
"""

import asyncio
from typing import Dict, Any, List, Optional
import uuid
from dataclasses import dataclass

@dataclass
class ToolResult:
    """工具调用结果"""
    success: bool
    data: Any = None
    error: str = None
    tool_name: str = None
    parameters: Dict = None
    execution_time: float = 0.0

class MCPBridge:
    """MCP桥接类，管理工具调用和会话"""
    
    def __init__(self, client=None):
        """初始化桥接
        
        Args:
            client: MCP客户端实例，默认为mock客户端
        """
        if client is None:
            from test.mock_mcp_client import mock_mcp_client
            self.client = mock_mcp_client
        else:
            self.client = client
        
        self.session_tools = {}  # 会话级工具缓存
    
    async def initialize_tools(self, session_id: str) -> List[Dict[str, Any]]:
        """为会话初始化可用工具
        
        Args:
            session_id: 会话ID
            
        Returns:
            可用工具列表
        """
        tools = self.client.list_tools()
        self.session_tools[session_id] = {
            tool["name"]: tool for tool in tools
        }
        return tools
    
    async def call_tool(self, session_id: str, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """调用指定工具
        
        Args:
            session_id: 会话ID
            tool_name: 工具名称
            parameters: 参数
            
        Returns:
            工具调用结果
        """
        import time
        start_time = time.time()
        
        try:
            # 验证工具是否存在
            if session_id not in self.session_tools:
                await self.initialize_tools(session_id)
            
            available_tools = self.session_tools[session_id]
            if tool_name not in available_tools:
                return ToolResult(
                    success=False,
                    error=f"会话 {session_id} 中工具 {tool_name} 不可用",
                    tool_name=tool_name,
                    parameters=parameters
                )
            
            # 调用工具
            result = await self.client.call_tool(tool_name, parameters)
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=result.success,
                data=result.data,
                error=result.error,
                tool_name=tool_name,
                parameters=parameters,
                execution_time=execution_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"工具调用异常: {str(e)}",
                tool_name=tool_name,
                parameters=parameters,
                execution_time=time.time() - start_time
            )
    
    def get_available_tools(self, session_id: str) -> List[str]:
        """获取会话可用工具列表
        
        Args:
            session_id: 会话ID
            
        Returns:
            工具名称列表
        """
        if session_id in self.session_tools:
            return list(self.session_tools[session_id].keys())
        return []
    
    def get_tool_schema(self, session_id: str, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具schema
        
        Args:
            session_id: 会话ID
            tool_name: 工具名称
            
        Returns:
            工具schema或None
        """
        if session_id in self.session_tools and tool_name in self.session_tools[session_id]:
            return self.session_tools[session_id][tool_name]
        return None

# 全局桥接实例
mcp_bridge = MCPBridge()