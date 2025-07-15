"""
公安大厅警情调度系统 - 主调度器
整合业务指导、命令解析、工具执行
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from simple_planner import SimplePlanner, PlanningStep
from tool_registry import ToolRegistry
from dependency_manager import DependencyManager


@dataclass
class DispatchStatus:
    """调度状态"""
    dispatch_id: str
    command: str
    current_step: int
    total_steps: int
    status: str  # "running", "completed", "failed", "waiting"
    step_details: List[Dict[str, Any]]
    start_time: datetime
    last_update: datetime
    error_message: Optional[str] = None


class PoliceDispatcher:
    """公安调度系统主调度器"""
    
    def __init__(self):
        self.planner = SimplePlanner()
        self.tool_registry = ToolRegistry()
        self.dependency_manager = DependencyManager()
        self.active_dispatches: Dict[str, DispatchStatus] = {}
    
    async def dispatch_command(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行调度命令
        
        Args:
            command: 调度员输入的命令
            context: 警情上下文信息
            
        Returns:
            执行结果和状态
        """
        dispatch_id = f"dispatch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # 1. 根据命令类型选择执行策略
        if command in ["open_monitor", "show_staff", "call_staff"]:
            result = await self._execute_simple_command(dispatch_id, command, context)
        elif command == "handle_all":
            result = await self._execute_complex_command(dispatch_id, command, context)
        else:
            result = {
                "status": "error",
                "message": f"未知命令: {command}",
                "dispatch_id": dispatch_id
            }
        
        return result
    
    async def _execute_simple_command(self, dispatch_id: str, 
                                    command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行简单命令"""
        # 简单命令直接映射到工具
        tool_mapping = {
            "open_monitor": "getPOI",
            "show_staff": "showQw", 
            "call_staff": "callPhone"
        }
        
        tool_name = tool_mapping[command]
        parameters = self._build_parameters(command, context)
        
        # 初始化状态
        self.active_dispatches[dispatch_id] = DispatchStatus(
            dispatch_id=dispatch_id,
            command=command,
            current_step=1,
            total_steps=1,
            status="running",
            step_details=[{"step": 1, "tool": tool_name, "status": "running"}],
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        try:
            # 执行工具
            result = await self.tool_registry.execute_tool(tool_name, parameters)
            
            # 更新状态
            self.active_dispatches[dispatch_id].status = "completed"
            self.active_dispatches[dispatch_id].step_details[0]["status"] = "completed"
            self.active_dispatches[dispatch_id].last_update = datetime.now()
            
            return {
                "status": "success",
                "dispatch_id": dispatch_id,
                "command": command,
                "result": result,
                "execution_time": str(datetime.now() - self.active_dispatches[dispatch_id].start_time)
            }
            
        except Exception as e:
            self.active_dispatches[dispatch_id].status = "failed"
            self.active_dispatches[dispatch_id].error_message = str(e)
            self.active_dispatches[dispatch_id].last_update = datetime.now()
            
            return {
                "status": "error",
                "dispatch_id": dispatch_id,
                "command": command,
                "error": str(e)
            }
    
    async def _execute_complex_command(self, dispatch_id: str, 
                                     command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行复杂命令"""
        # 使用planner生成步骤
        steps = self.planner.plan_dispatch(context)
        
        # 初始化状态
        self.active_dispatches[dispatch_id] = DispatchStatus(
            dispatch_id=dispatch_id,
            command=command,
            current_step=0,
            total_steps=len(steps),
            status="running",
            step_details=[
                {"step": i+1, "tool": step.tool_name, "status": "waiting", "description": step.description}
                for i, step in enumerate(steps)
            ],
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        results = []
        step_results = {}  # 存储每一步的结果用于参数传递
        
        try:
            for i, step in enumerate(steps):
                # 更新当前步骤状态
                self.active_dispatches[dispatch_id].current_step = i + 1
                self.active_dispatches[dispatch_id].step_details[i]["status"] = "running"
                self.active_dispatches[dispatch_id].last_update = datetime.now()
                
                # 处理参数依赖
                parameters = self.dependency_manager.resolve_parameters(
                    step.parameters, step_results
                )
                
                # 执行步骤
                result = await self.tool_registry.execute_tool(step.tool_name, parameters)
                
                # 存储结果
                step_results[step.step_id] = result
                results.append({
                    "step": i + 1,
                    "tool": step.tool_name,
                    "result": result,
                    "status": "success"
                })
                
                # 更新步骤状态
                self.active_dispatches[dispatch_id].step_details[i]["status"] = "completed"
                self.active_dispatches[dispatch_id].last_update = datetime.now()
            
            # 全部完成
            self.active_dispatches[dispatch_id].status = "completed"
            
            return {
                "status": "success",
                "dispatch_id": dispatch_id,
                "command": command,
                "total_steps": len(steps),
                "results": results,
                "execution_time": str(datetime.now() - self.active_dispatches[dispatch_id].start_time)
            }
            
        except Exception as e:
            self.active_dispatches[dispatch_id].status = "failed"
            self.active_dispatches[dispatch_id].error_message = str(e)
            self.active_dispatches[dispatch_id].last_update = datetime.now()
            
            return {
                "status": "error",
                "dispatch_id": dispatch_id,
                "command": command,
                "failed_at_step": self.active_dispatches[dispatch_id].current_step,
                "error": str(e)
            }
    
    def get_dispatch_status(self, dispatch_id: str) -> Optional[Dict[str, Any]]:
        """获取调度状态"""
        if dispatch_id not in self.active_dispatches:
            return None
        
        status = self.active_dispatches[dispatch_id]
        return {
            "dispatch_id": status.dispatch_id,
            "command": status.command,
            "current_step": status.current_step,
            "total_steps": status.total_steps,
            "status": status.status,
            "step_details": status.step_details,
            "start_time": status.start_time.isoformat(),
            "last_update": status.last_update.isoformat(),
            "error_message": status.error_message
        }
    
    def list_active_dispatches(self) -> List[Dict[str, Any]]:
        """列出所有活动调度"""
        return [
            {
                "dispatch_id": ds.dispatch_id,
                "command": ds.command,
                "status": ds.status,
                "progress": f"{ds.current_step}/{ds.total_steps}",
                "start_time": ds.start_time.isoformat()
            }
            for ds in self.active_dispatches.values()
        ]
    
    def _build_parameters(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """构建工具参数"""
        if command == "open_monitor":
            return {
                "x_position": context.get("coordinates", {}).get("x", 116.3974),
                "y_position": context.get("coordinates", {}).get("y", 39.9093),
                "afdd": context.get("address", "北京市朝阳区建国门外大街1号")
            }
        elif command == "show_staff":
            return {
                "gxdwdm": context.get("unit_code", "110105")
            }
        elif command == "call_staff":
            return {
                "phone": context.get("target_phone", "13800138000")
            }
        
        return {}


# 使用示例和测试
async def demo_dispatcher():
    """演示调度系统"""
    dispatcher = PoliceDispatcher()
    
    print("=== 公安大厅警情调度系统演示 ===\n")
    
    # 测试场景1：简单命令
    print("1. 测试简单命令 - 打开监控")
    simple_context = {
        "coordinates": {"x": 116.3974, "y": 39.9093},
        "address": "北京市朝阳区建国门外大街1号"
    }
    result1 = await dispatcher.dispatch_command("open_monitor", simple_context)
    print(f"结果: {json.dumps(result1, ensure_ascii=False, indent=2)}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试场景2：复杂命令
    print("2. 测试复杂命令 - 一键处置")
    complex_context = {
        "emergency_type": "一般交通事故",
        "coordinates": {"x": 116.3974, "y": 39.9093},
        "address": "北京市朝阳区建国门外大街1号",
        "unit_code": "110105"
    }
    result2 = await dispatcher.dispatch_command("handle_all", complex_context)
    print(f"结果: {json.dumps(result2, ensure_ascii=False, indent=2)}")
    
    print("\n" + "="*50 + "\n")
    
    # 显示当前活动调度
    print("3. 当前活动调度")
    active_dispatches = dispatcher.list_active_dispatches()
    print(f"活动调度: {json.dumps(active_dispatches, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    asyncio.run(demo_dispatcher())