"""
DispatcherAgent - 调度执行代理
"""

import asyncio
from typing import Dict, Any, List, Optional
import uuid
from dataclasses import dataclass
from mcp_bridge import MCPBridge, ToolResult

@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: str
    description: str
    tool_name: str
    parameters: Dict[str, Any]
    status: str = "pending"  # pending, running, success, failed
    result: Optional[ToolResult] = None
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

class DispatcherAgent:
    """调度执行代理"""
    
    def __init__(self, session_id: str, mcp_bridge: Optional[MCPBridge] = None):
        """初始化调度代理
        
        Args:
            session_id: 会话ID
            mcp_bridge: MCP桥接实例
        """
        self.session_id = session_id
        self.mcp_bridge = mcp_bridge or MCPBridge()
        self.execution_steps: List[ExecutionStep] = []
        self.current_step_index = 0
        self.status = "initialized"  # initialized, running, paused, completed, failed
        
    async def initialize(self) -> bool:
        """初始化代理"""
        try:
            await self.mcp_bridge.initialize_tools(self.session_id)
            self.status = "ready"
            return True
        except Exception as e:
            self.status = "failed"
            return False
    
    def create_plan(self, steps: List[Dict[str, Any]]) -> List[ExecutionStep]:
        """创建执行计划
        
        Args:
            steps: 步骤列表，每个步骤包含tool_name和parameters
            
        Returns:
            执行步骤列表
        """
        import time
        
        self.execution_steps = []
        for i, step_data in enumerate(steps):
            step = ExecutionStep(
                step_id=f"{self.session_id}_step_{i+1}",
                description=step_data.get("description", f"步骤 {i+1}"),
                tool_name=step_data["tool_name"],
                parameters=step_data["parameters"],
                created_at=time.time()
            )
            self.execution_steps.append(step)
        
        return self.execution_steps
    
    async def execute_step(self, step: ExecutionStep) -> ToolResult:
        """执行单个步骤
        
        Args:
            step: 要执行的步骤
            
        Returns:
            执行结果
        """
        import time
        
        step.status = "running"
        step.started_at = time.time()
        
        try:
            result = await self.mcp_bridge.call_tool(
                self.session_id,
                step.tool_name,
                step.parameters
            )
            
            step.result = result
            step.status = "success" if result.success else "failed"
            step.completed_at = time.time()
            
            return result
            
        except Exception as e:
            step.status = "failed"
            step.result = ToolResult(
                success=False,
                error=str(e),
                tool_name=step.tool_name,
                parameters=step.parameters
            )
            step.completed_at = time.time()
            return step.result
    
    async def execute_plan(self) -> List[ToolResult]:
        """顺序执行整个计划
        
        Returns:
            所有步骤的执行结果
        """
        if self.status != "ready":
            await self.initialize()
        
        self.status = "running"
        results = []
        
        try:
            for i, step in enumerate(self.execution_steps):
                if self.status == "paused":
                    break
                    
                self.current_step_index = i
                result = await self.execute_step(step)
                results.append(result)
                
                if not result.success:
                    self.status = "failed"
                    break
            
            if self.status == "running":
                self.status = "completed"
                
        except Exception as e:
            self.status = "failed"
            
        return results
    
    def get_plan_status(self) -> Dict[str, Any]:
        """获取计划执行状态"""
        total_steps = len(self.execution_steps)
        completed_steps = sum(1 for step in self.execution_steps if step.status in ["success", "failed"])
        success_steps = sum(1 for step in self.execution_steps if step.status == "success")
        
        return {
            "session_id": self.session_id,
            "status": self.status,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "success_steps": success_steps,
            "current_step_index": self.current_step_index,
            "steps": [
                {
                    "step_id": step.step_id,
                    "description": step.description,
                    "tool_name": step.tool_name,
                    "status": step.status,
                    "result": {
                        "success": step.result.success if step.result else None,
                        "data": step.result.data if step.result else None,
                        "error": step.result.error if step.result else None
                    } if step.result else None
                }
                for step in self.execution_steps
            ]
        }
    
    def reset(self):
        """重置代理状态"""
        self.execution_steps = []
        self.current_step_index = 0
        self.status = "initialized"
    
    async def execute_single_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """执行单个工具调用（用于简单指令）
        
        Args:
            tool_name: 工具名称
            parameters: 参数
            
        Returns:
            执行结果
        """
        await self.initialize()
        
        step = ExecutionStep(
            step_id=f"{self.session_id}_single",
            description=f"执行 {tool_name}",
            tool_name=tool_name,
            parameters=parameters
        )
        
        return await self.execute_step(step)