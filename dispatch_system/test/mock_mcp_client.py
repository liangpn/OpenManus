"""
Mock MCP Client for testing dispatch system
"""

import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class MockToolResult:
    """模拟工具调用结果"""
    success: bool
    data: Any
    error: str = None

class MockMCPClient:
    """模拟MCP客户端，用于测试"""
    
    def __init__(self):
        self.tools = {
            "getPOI": {
                "name": "getPOI",
                "description": "根据坐标打开周边监控",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "x_position": {"type": "number"},
                        "y_position": {"type": "number"},
                        "afdd": {"type": "string"}
                    },
                    "required": ["x_position", "y_position", "afdd"]
                }
            },
            "showQw": {
                "name": "showQw",
                "description": "查看值班人员信息",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "gxdwdm": {"type": "string"}
                    },
                    "required": ["gxdwdm"]
                }
            },
            "callPhone": {
                "name": "callPhone",
                "description": "拨打值班电话",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "phone": {"type": "string"}
                    },
                    "required": ["phone"]
                }
            }
        }
        
        self.mock_responses = {
            "getPOI": {
                "success": {
                    "message": "已成功打开北京市朝阳区xxx路xxx号的周边监控",
                    "camera_count": 5,
                    "camera_ids": ["CAM001", "CAM002", "CAM003", "CAM004", "CAM005"]
                },
                "error": {
                    "message": "无法连接到监控系统",
                    "error_code": "NETWORK_TIMEOUT"
                }
            },
            "showQw": {
                "success": {
                    "message": "值班人员信息获取成功",
                    "personnel": [
                        {"name": "张三", "phone": "13800138000", "role": "值班民警"},
                        {"name": "李四", "phone": "13800138001", "role": "值班辅警"}
                    ]
                },
                "error": {
                    "message": "无法获取值班人员信息",
                    "error_code": "SYSTEM_ERROR"
                }
            },
            "callPhone": {
                "success": {
                    "message": "已成功联系值班人员张三",
                    "call_duration": 45,
                    "status": "通话已建立"
                },
                "error": {
                    "message": "电话无法接通",
                    "error_code": "CALL_FAILED"
                }
            }
        }
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MockToolResult:
        """模拟工具调用"""
        if tool_name not in self.tools:
            return MockToolResult(
                success=False,
                data=None,
                error=f"工具 {tool_name} 不存在"
            )
        
        # 验证参数
        tool_schema = self.tools[tool_name]
        required_params = tool_schema["input_schema"]["required"]
        missing_params = [p for p in required_params if p not in parameters]
        
        if missing_params:
            return MockToolResult(
                success=False,
                data=None,
                error=f"缺少必需参数: {missing_params}"
            )
        
        # 模拟随机成功/失败
        import random
        success_rate = 0.9  # 90%成功率
        
        if random.random() < success_rate:
            return MockToolResult(
                success=True,
                data=self.mock_responses[tool_name]["success"]
            )
        else:
            return MockToolResult(
                success=False,
                data=self.mock_responses[tool_name]["error"],
                error="模拟网络错误"
            )
    
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """获取工具Schema"""
        return self.tools.get(tool_name, {})
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        return list(self.tools.values())

# 全局mock实例
mock_mcp_client = MockMCPClient()