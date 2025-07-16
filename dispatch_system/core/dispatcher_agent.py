"""
DispatcherAgent - 支持真实MCP服务器的调度执行代理
"""

import asyncio
from typing import Dict, Any, List, Optional
import uuid
from dataclasses import dataclass
from real_mcp_bridge import RealMCPBridge, RealToolResult

@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: str
    description: str
    tool_name: str
    parameters: Dict[str, Any]
    status: str = "pending"  # pending, running, success, failed
    result: Optional[RealToolResult] = None
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

class RealDispatcherAgent:
    """真实MCP服务器支持的调度执行代理"""
    
    def __init__(self, session_id: str, mcp_bridge: Optional[RealMCPBridge] = None):
        """初始化调度代理
        
        Args:
            session_id: 会话ID
            mcp_bridge: 真实MCP桥接实例
        """
        self.session_id = session_id
        self.mcp_bridge = mcp_bridge or RealMCPBridge("http://localhost:4000/mcp")
        self.execution_steps: List[ExecutionStep] = []
        self.current_step_index = 0
        self.status = "initialized"  # initialized, connecting, ready, running, paused, completed, failed
    
    async def initialize(self) -> bool:
        """初始化代理并连接MCP服务器"""
        self.status = "connecting"
        try:
            success = await self.mcp_bridge.connect()
            if success:
                self.status = "ready"
                print(f"✅ 调度代理 {self.session_id} 已就绪")
                return True
            else:
                self.status = "failed"
                print(f"❌ 调度代理 {self.session_id} 初始化失败")
                return False
        except Exception as e:
            self.status = "failed"
            print(f"❌ 调度代理 {self.session_id} 连接异常: {e}")
            return False
    
    async def discover_tools(self) -> List[Dict[str, Any]]:
        """发现可用工具"""
        if not self.mcp_bridge.is_connected():
            await self.initialize()
        
        if not self.mcp_bridge.is_connected():
            return []
        
        return await self.mcp_bridge.list_tools()
    
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
    
    async def execute_step(self, step: ExecutionStep) -> RealToolResult:
        """执行单个步骤"""
        import time
        
        if not self.mcp_bridge.is_connected():
            success = await self.initialize()
            if not success:
                return RealToolResult(
                    success=False,
                    error="无法连接到MCP服务器",
                    tool_name=step.tool_name,
                    parameters=step.parameters
                )
        
        step.status = "running"
        step.started_at = time.time()
        
        try:
            result = await self.mcp_bridge.call_tool(
                step.tool_name,
                step.parameters
            )
            
            step.result = result
            step.status = "success" if result.success else "failed"
            step.completed_at = time.time()
            
            return result
            
        except Exception as e:
            step.status = "failed"
            step.result = RealToolResult(
                success=False,
                error=str(e),
                tool_name=step.tool_name,
                parameters=step.parameters
            )
            step.completed_at = time.time()
            return step.result
    
    async def execute_plan(self) -> List[RealToolResult]:
        """顺序执行整个计划"""
        if self.status not in ["ready", "running"]:
            await self.initialize()
        
        if not self.mcp_bridge.is_connected():
            self.status = "failed"
            return []
        
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
    
    async def execute_single_tool(self, tool_name: str, parameters: Dict[str, Any]) -> RealToolResult:
        """执行单个工具调用"""
        if not self.mcp_bridge.is_connected():
            await self.initialize()
        
        if not self.mcp_bridge.is_connected():
            return RealToolResult(
                success=False,
                error="无法连接到MCP服务器",
                tool_name=tool_name,
                parameters=parameters
            )
        
        step = ExecutionStep(
            step_id=f"{self.session_id}_single",
            description=f"执行 {tool_name}",
            tool_name=tool_name,
            parameters=parameters
        )
        
        return await self.execute_step(step)
    
    def get_plan_status(self) -> Dict[str, Any]:
        """获取计划执行状态"""
        total_steps = len(self.execution_steps)
        completed_steps = sum(1 for step in self.execution_steps if step.status in ["success", "failed"])
        success_steps = sum(1 for step in self.execution_steps if step.status == "success")
        
        return {
            "session_id": self.session_id,
            "status": self.status,
            "connected": self.mcp_bridge.is_connected(),
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
    
    async def cleanup(self):
        """清理资源"""
        await self.mcp_bridge.disconnect()
        self.status = "disconnected"
    
    def reset(self):
        """重置代理状态"""
        self.execution_steps = []
        self.current_step_index = 0
        self.status = "initialized"

# 测试函数
async def test_real_dispatcher():
    """测试真实调度代理"""
    agent = RealDispatcherAgent("test-session-001")
    
    try:
        # 初始化
        success = await agent.initialize()
        if not success:
            print("❌ 初始化失败")
            return
        
        # 发现工具
        tools = await agent.discover_tools()
        print(f"📋 发现工具：{len(tools)} 个")
        
        if not tools:
            print("❌ 没有发现可用工具")
            return
        
        # 测试调度流程
        if any('getPOI' in str(tool.get('name', '')) for tool in tools):
            print("\n🧪 测试调度流程...")
            
            steps = [
                {
                    "description": "打开案发地周边监控",
                    "tool_name": "getPOI",
                    "parameters": {
                        "x_position": 116.3974,
                        "y_position": 39.9093,
                        "afdd": "北京市朝阳区测试地址"
                    }
                }
            ]
            
            agent.create_plan(steps)
            results = await agent.execute_plan()
            
            print(f"✅ 执行完成：{len(results)} 个结果")
            
        await agent.cleanup()
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_real_dispatcher())