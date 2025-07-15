"""
动态工具注册和管理系统
支持30+ MCP工具的动态注册和发现
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import inspect
import asyncio


class ToolCategory(str, Enum):
    SURVEILLANCE = "监控类"
    PERSONNEL = "人员类"
    COMMUNICATION = "通信类"
    DISPATCH = "调度类"
    EMERGENCY = "应急类"
    MEDICAL = "医疗类"
    TRAFFIC = "交通类"
    INTELLIGENCE = "情报类"
    FORENSICS = "技术类"
    ADMINISTRATIVE = "行政类"


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str  # string, number, boolean, array, object
    description: str = ""
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None
    validation: Optional[Dict[str, Any]] = None  # min, max, pattern等
    examples: Optional[List[Any]] = None


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    display_name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter]
    return_type: str = "object"
    timeout: int = 30
    retry_count: int = 2
    permissions: List[str] = None
    tags: List[str] = None
    examples: List[Dict[str, Any]] = None
    deprecation_message: Optional[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
        if self.tags is None:
            self.tags = []
        if self.examples is None:
            self.examples = []


@dataclass
class ToolExecutionResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0


class MCPClientAdapter:
    """MCP客户端适配器"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.connected = False
    
    async def connect(self) -> bool:
        """连接到MCP服务器"""
        # 实际实现会连接到MCP服务器
        self.connected = True
        return True
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """执行MCP工具"""
        # 模拟执行
        await asyncio.sleep(0.1)  # 模拟网络延迟
        
        # 根据工具名称返回模拟结果
        if tool_name == "getPOI":
            return ToolExecutionResult(
                success=True,
                data={
                    "status": "success",
                    "monitors": [
                        {"id": "CAM001", "location": "路口东北角"},
                        {"id": "CAM002", "location": "路口西南角"}
                    ]
                }
            )
        elif tool_name == "showQw":
            return ToolExecutionResult(
                success=True,
                data={
                    "staff_count": 2,
                    "primary_contact": "13800138000",
                    "staff_list": [
                        {"name": "张三", "phone": "13800138000", "role": "巡警"},
                        {"name": "李四", "phone": "13900139000", "role": "值班长"}
                    ]
                }
            )
        elif tool_name == "callPhone":
            return ToolExecutionResult(
                success=True,
                data={
                    "status": "connected",
                    "duration": 45,
                    "contact_info": {"name": "张三", "role": "巡警"}
                }
            )
        
        return ToolExecutionResult(
            success=False,
            error_message=f"未知工具: {tool_name}"
        )


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.categories: Dict[ToolCategory, List[str]] = {}
        self.mcp_adapters: Dict[str, MCPClientAdapter] = {}
        self.current_tools = 3  # 当前工具数量
        self.max_tools = 30     # 最大支持工具数量
    
    def register_builtin_tools(self):
        """注册内置的3个基础工具"""
        
        # 1. 打开周边监控
        get_poi_tool = ToolDefinition(
            name="getPOI",
            display_name="打开周边监控",
            description="根据案发地点坐标打开周边监控设备",
            category=ToolCategory.SURVEILLANCE,
            parameters=[
                ToolParameter(
                    name="x_position",
                    type="number",
                    description="案发地点X坐标",
                    required=True,
                    examples=[116.3974, 121.4737]
                ),
                ToolParameter(
                    name="y_position",
                    type="number",
                    description="案发地点Y坐标",
                    required=True,
                    examples=[39.9093, 31.2304]
                ),
                ToolParameter(
                    name="afdd",
                    type="string",
                    description="案发地点详细地址",
                    required=True,
                    examples=["北京市朝阳区建国门外大街1号"]
                )
            ],
            return_type="object",
            timeout=30,
            tags=["监控", "定位", "视频"],
            examples=[
                {
                    "description": "打开指定位置的周边监控",
                    "parameters": {
                        "x_position": 116.3974,
                        "y_position": 39.9093,
                        "afdd": "北京市朝阳区建国门外大街1号"
                    }
                }
            ]
        )
        
        # 2. 查看值班人员
        show_qw_tool = ToolDefinition(
            name="showQw",
            display_name="查看值班人员",
            description="根据管辖单位代码查看值班人员信息",
            category=ToolCategory.PERSONNEL,
            parameters=[
                ToolParameter(
                    name="gxdwdm",
                    type="string",
                    description="管辖单位代码",
                    required=True,
                    validation={"pattern": "^\d{6}$"},
                    examples=["110105", "310101"]
                )
            ],
            return_type="object",
            timeout=15,
            tags=["人员", "值班", "调度"],
            examples=[
                {
                    "description": "查看指定单位的值班人员",
                    "parameters": {
                        "gxdwdm": "110105"
                    }
                }
            ]
        )
        
        # 3. 拨打电话
        call_phone_tool = ToolDefinition(
            name="callPhone",
            display_name="拨打电话",
            description="拨打指定电话号码联系值班人员",
            category=ToolCategory.COMMUNICATION,
            parameters=[
                ToolParameter(
                    name="phone",
                    type="string",
                    description="电话号码",
                    required=True,
                    validation={"pattern": "^1[3-9]\d{9}$"},
                    examples=["13800138000", "13900139000"]
                )
            ],
            return_type="object",
            timeout=20,
            tags=["通信", "联系", "通知"],
            examples=[
                {
                    "description": "联系值班人员",
                    "parameters": {
                        "phone": "13800138000"
                    }
                }
            ]
        )
        
        self.register_tool(get_poi_tool)
        self.register_tool(show_qw_tool)
        self.register_tool(call_phone_tool)
    
    def register_tool(self, tool: ToolDefinition):
        """注册工具"""
        if len(self.tools) >= self.max_tools:
            raise ValueError(f"工具数量超过最大限制: {self.max_tools}")
        
        self.tools[tool.name] = tool
        
        if tool.category not in self.categories:
            self.categories[tool.category] = []
        self.categories[tool.category].append(tool.name)
    
    def register_future_tools(self):
        """注册未来扩展的30个工具"""
        
        future_tools = [
            # 监控类扩展
            ToolDefinition(
                name="assessThreatLevel",
                display_name="威胁等级评估",
                description="评估警情威胁等级",
                category=ToolCategory.INTELLIGENCE,
                parameters=[
                    ToolParameter("incident_type", "string", required=True),
                    ToolParameter("location", "object", required=True),
                    ToolParameter("intensity", "number", default=1, validation={"min": 1, "max": 10})
                ],
                tags=["评估", "威胁", "等级"]
            ),
            
            # 调度类扩展
            ToolDefinition(
                name="dispatchSWAT",
                display_name="派遣特警",
                description="派遣特警支援",
                category=ToolCategory.DISPATCH,
                parameters=[
                    ToolParameter("location", "object", required=True),
                    ToolParameter("unit_count", "number", default=1, validation={"min": 1, "max": 10}),
                    ToolParameter("specialization", "string", enum=["anti_terror", "hostage", "high_risk"])
                ],
                tags=["特警", "支援", "专业"]
            ),
            
            ToolDefinition(
                name="coordinateEMS",
                display_name="协调急救",
                description="协调医疗急救服务",
                category=ToolCategory.MEDICAL,
                parameters=[
                    ToolParameter("location", "object", required=True),
                    ToolParameter("casualty_count", "number", required=True),
                    ToolParameter("severity", "string", enum=["minor", "moderate", "severe", "critical"])
                ],
                tags=["医疗", "急救", "协调"]
            ),
            
            # 交通类扩展
            ToolDefinition(
                name="controlTraffic",
                display_name="交通管制",
                description="实施交通管制措施",
                category=ToolCategory.TRAFFIC,
                parameters=[
                    ToolParameter("location", "object", required=True),
                    ToolParameter("radius", "number", default=500),
                    ToolParameter("actions", "array", required=True)
                ],
                tags=["交通", "管制", "疏导"]
            ),
            
            ToolDefinition(
                name="establishPerimeter",
                display_name="建立警戒线",
                description="建立安全警戒线",
                category=ToolCategory.EMERGENCY,
                parameters=[
                    ToolParameter("location", "object", required=True),
                    ToolParameter("radius", "number", default=300),
                    ToolParameter("units_needed", "number", default=6)
                ],
                tags=["警戒", "安全", "封锁"]
            )
        ]
        
        # 注册基础扩展工具
        for tool in future_tools:
            self.register_tool(tool)
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[ToolDefinition]:
        """列出工具"""
        if category:
            tool_names = self.categories.get(category, [])
            return [self.tools[name] for name in tool_names if name in self.tools]
        return list(self.tools.values())
    
    def search_tools(self, keyword: str, category: Optional[ToolCategory] = None) -> List[ToolDefinition]:
        """搜索工具"""
        tools = self.list_tools(category)
        keyword = keyword.lower()
        
        return [
            tool for tool in tools
            if keyword in tool.name.lower() or
               keyword in tool.display_name.lower() or
               keyword in tool.description.lower() or
               any(keyword in tag.lower() for tag in tool.tags)
        ]
    
    def validate_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> List[str]:
        """验证参数"""
        errors = []
        tool = self.get_tool(tool_name)
        
        if not tool:
            errors.append(f"工具不存在: {tool_name}")
            return errors
        
        # 检查必需参数
        for param in tool.parameters:
            if param.required and param.name not in parameters:
                errors.append(f"缺少必需参数: {param.name}")
        
        # 检查参数类型和验证规则
        for param_name, value in parameters.items():
            param_def = next((p for p in tool.parameters if p.name == param_name), None)
            if param_def:
                errors.extend(self._validate_parameter_type(param_def, value))
                errors.extend(self._validate_parameter_rules(param_def, value))
        
        return errors
    
    def _validate_parameter_type(self, param: ToolParameter, value: Any) -> List[str]:
        """验证参数类型"""
        errors = []
        
        type_map = {
            "string": str,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_types = type_map.get(param.type, str)
        if not isinstance(value, expected_types):
            errors.append(f"参数 {param.name} 类型错误，期望 {param.type}，实际 {type(value)}")
        
        return errors
    
    def _validate_parameter_rules(self, param: ToolParameter, value: Any) -> List[str]:
        """验证参数规则"""
        errors = []
        
        if param.validation:
            if "min" in param.validation and isinstance(value, (int, float)):
                if value < param.validation["min"]:
                    errors.append(f"参数 {param.name} 小于最小值 {param.validation['min']}")
            
            if "max" in param.validation and isinstance(value, (int, float)):
                if value > param.validation["max"]:
                    errors.append(f"参数 {param.name} 大于最大值 {param.validation['max']}")
            
            if "pattern" in param.validation and isinstance(value, str):
                import re
                if not re.match(param.validation["pattern"], value):
                    errors.append(f"参数 {param.name} 格式不匹配")
            
            if "enum" in param.validation and value not in param.validation["enum"]:
                errors.append(f"参数 {param.name} 值不在允许范围内")
        
        if param.enum and value not in param.enum:
            errors.append(f"参数 {param.name} 值不在枚举范围内: {param.enum}")
        
        return errors
    
    def export_tool_catalog(self, format: str = "json") -> str:
        """导出工具目录"""
        catalog = {
            "version": "1.0",
            "total_tools": len(self.tools),
            "categories": {cat.value: tools for cat, tools in self.categories.items()},
            "tools": [asdict(tool) for tool in self.tools.values()]
        }
        
        if format == "json":
            return json.dumps(catalog, indent=2, ensure_ascii=False)
        elif format == "yaml":
            return yaml.dump(catalog, allow_unicode=True, default_flow_style=False)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            "total_tools": len(self.tools),
            "by_category": {cat.value: len(tools) for cat, tools in self.categories.items()},
            "current_tools": self.current_tools,
            "max_capacity": self.max_tools,
            "capacity_utilization": f"{len(self.tools) / self.max_tools * 100:.1f}%"
        }


class ToolManager:
    """工具管理器"""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.mcp_client = MCPClientAdapter("http://localhost:4000/mcp")
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """执行工具"""
        # 验证参数
        errors = self.registry.validate_parameters(tool_name, parameters)
        if errors:
            return ToolExecutionResult(
                success=False,
                error_message=f"参数验证失败: {'; '.join(errors)}"
            )
        
        # 获取工具定义
        tool = self.registry.get_tool(tool_name)
        if not tool:
            return ToolExecutionResult(
                success=False,
                error_message=f"工具未找到: {tool_name}"
            )
        
        # 执行工具
        try:
            result = await self.mcp_client.execute_tool(tool_name, parameters)
            return result
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error_message=str(e)
            )


# 全局工具注册表
_global_registry = None

def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
        _global_registry.register_builtin_tools()
        _global_registry.register_future_tools()
    return _global_registry


# 使用示例
if __name__ == "__main__":
    registry = get_tool_registry()
    
    # 列出所有工具
    print("=== 所有工具 ===")
    for tool in registry.list_tools():
        print(f"{tool.name}: {tool.display_name}")
    
    # 按类别列出
    print("\n=== 按类别 ===")
    for category in ToolCategory:
        tools = registry.list_tools(category)
        print(f"{category.value}: {len(tools)}")
    
    # 搜索工具
    print("\n=== 搜索监控类工具 ===")
    surveillance_tools = registry.search_tools("监控", ToolCategory.SURVEILLANCE)
    for tool in surveillance_tools:
        print(f"- {tool.name}: {tool.description}")
    
    # 使用统计
    print("\n=== 使用统计 ===")
    stats = registry.get_usage_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))