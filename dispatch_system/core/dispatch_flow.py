"""
DispatchFlow - 基于OpenManus的调度流程
"""

import asyncio
from typing import Dict, Any, List, Optional
import uuid
from dataclasses import dataclass
from dispatcher_agent import DispatcherAgent
from mcp_bridge import MCPBridge

@dataclass
class EmergencyData:
    """警情数据"""
    coordinates: Dict[str, float]
    address: str
    unit_code: str
    emergency_type: str
    description: str = ""

class DispatchFlow:
    """调度流程类"""
    
    def __init__(self):
        """初始化调度流程"""
        self.mcp_bridge = MCPBridge()
        self.sessions: Dict[str, DispatcherAgent] = {}
    
    async def create_session(self, emergency_data: EmergencyData) -> str:
        """创建新的调度会话
        
        Args:
            emergency_data: 警情数据
            
        Returns:
            会话ID
        """
        session_id = str(uuid.uuid4())
        
        # 创建新的调度代理
        agent = DispatcherAgent(session_id, self.mcp_bridge)
        success = await agent.initialize()
        
        if success:
            self.sessions[session_id] = agent
            return session_id
        else:
            raise Exception("无法初始化调度代理")
    
    async def execute_simple_command(self, session_id: str, command: str, emergency_data: EmergencyData) -> Dict[str, Any]:
        """执行简单指令
        
        Args:
            session_id: 会话ID
            command: 用户指令
            emergency_data: 警情数据
            
        Returns:
            执行结果
        """
        if session_id not in self.sessions:
            raise Exception(f"会话 {session_id} 不存在")
        
        agent = self.sessions[session_id]
        
        # 基于指令和警情数据生成工具调用
        if "监控" in command or "摄像头" in command:
            return await self._execute_get_poi(agent, emergency_data)
        elif "值班" in command or "人员" in command:
            return await self._execute_show_qw(agent, emergency_data)
        elif "电话" in command or "联系" in command:
            return await self._execute_call_phone(agent, emergency_data)
        else:
            # 默认执行完整流程
            return await self._execute_full_flow(agent, emergency_data)
    
    async def _execute_get_poi(self, agent: DispatcherAgent, emergency_data: EmergencyData) -> Dict[str, Any]:
        """执行getPOI工具"""
        result = await agent.execute_single_tool(
            "getPOI",
            {
                "x_position": emergency_data.coordinates["x"],
                "y_position": emergency_data.coordinates["y"],
                "afdd": emergency_data.address
            }
        )
        
        return {
            "tool_name": "getPOI",
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "session_id": agent.session_id
        }
    
    async def _execute_show_qw(self, agent: DispatcherAgent, emergency_data: EmergencyData) -> Dict[str, Any]:
        """执行showQw工具"""
        result = await agent.execute_single_tool(
            "showQw",
            {"gxdwdm": emergency_data.unit_code}
        )
        
        return {
            "tool_name": "showQw",
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "session_id": agent.session_id
        }
    
    async def _execute_call_phone(self, agent: DispatcherAgent, emergency_data: EmergencyData) -> Dict[str, Any]:
        """执行callPhone工具"""
        # 这里简化处理，实际应该从showQw结果中获取电话
        phone = "13800138000"  # 示例电话
        
        result = await agent.execute_single_tool(
            "callPhone",
            {"phone": phone}
        )
        
        return {
            "tool_name": "callPhone",
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "session_id": agent.session_id
        }
    
    async def _execute_full_flow(self, agent: DispatcherAgent, emergency_data: EmergencyData) -> Dict[str, Any]:
        """执行完整调度流程"""
        steps = [
            {
                "description": "打开案发地周边监控",
                "tool_name": "getPOI",
                "parameters": {
                    "x_position": emergency_data.coordinates["x"],
                    "y_position": emergency_data.coordinates["y"],
                    "afdd": emergency_data.address
                }
            },
            {
                "description": "查看管辖单位值班人员",
                "tool_name": "showQw",
                "parameters": {"gxdwdm": emergency_data.unit_code}
            },
            {
                "description": "联系值班人员",
                "tool_name": "callPhone",
                "parameters": {"phone": "13800138000"}
            }
        ]
        
        agent.create_plan(steps)
        results = await agent.execute_plan()
        
        return {
            "flow_type": "full",
            "total_steps": len(steps),
            "completed_steps": len(results),
            "status": agent.status,
            "steps": agent.get_plan_status(),
            "session_id": agent.session_id
        }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        if session_id not in self.sessions:
            return {"error": "会话不存在", "session_id": session_id}
        
        agent = self.sessions[session_id]
        return agent.get_plan_status()
    
    def cleanup_session(self, session_id: str):
        """清理会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def list_sessions(self) -> List[str]:
        """列出所有活跃会话"""
        return list(self.sessions.keys())

# 全局调度流程实例
dispatch_flow = DispatchFlow()