# 调度指挥系统架构设计文档 V3.0

## 核心架构

基于OpenManus的PlanningFlow，实现人机交互调度系统。

### 关键特性
- **服务启动时**：连接MCP server获取工具
- **用户指令**：由planner智能规划执行步骤
- **状态追踪**：每个step执行状态实时记录
- **警单集成**：前端传递警情关键数据

## 运行流程

```
系统启动 → MCP连接 → 工具获取 → 用户输入 → Planner规划 → Step顺序执行
```

### 启动时序
1. **服务启动阶段**：系统启动时立即连接MCP server并获取业务工具
2. **会话初始化**：每个用户会话创建独立的PlanningFlow实例
3. **用户输入处理**：接收用户指令和警情数据
4. **规划执行**：Planner基于可用工具进行规划，顺序执行steps

## 工具分层

### 系统预设工具 (PlanManagementTools)
**用途**：用于plan的动态管理，由系统提供，Planner可调用

```python
class PlanManagementTools:
    """计划管理工具集 - 系统预设"""
    
    def pause_plan(self, execution_id: str) -> bool:
        """挂起当前执行计划"""
        pass
    
    def resume_plan(self, execution_id: str) -> bool:
        """恢复被挂起的执行计划"""
        pass
    
    def modify_plan(self, execution_id: str, new_steps: List[str]) -> bool:
        """修改执行中的计划步骤"""
        pass
    
    def cancel_plan(self, execution_id: str) -> bool:
        """取消执行计划"""
        pass
    
    def add_step(self, execution_id: str, step_text: str, position: int = None) -> bool:
        """在当前计划中添加新步骤"""
        pass
    
    def remove_step(self, execution_id: str, step_index: int) -> bool:
        """从计划中移除指定步骤"""
        pass
    
    def retry_step(self, execution_id: str, step_index: int) -> bool:
        """重试失败的步骤"""
        pass
    
    def get_plan_status(self, execution_id: str) -> Dict:
        """获取当前计划执行状态"""
        pass
```

### 业务MCP工具
**用途**：用于执行具体的业务步骤，由MCP server提供

```python
# 业务工具清单
"getPOI": "打开周边监控"
"showQw": "查看值班人员"  
"callPhone": "拨打值班电话"
```

## Prompt层设计

### Planner系统提示词
```
你是调度系统的规划助手，负责将用户指令转化为可执行的计划步骤。

可用工具分为两类：
1. **Plan管理工具**：pause_plan, resume_plan, modify_plan, cancel_plan等 - 用于动态调整计划
2. **业务MCP工具**：getPOI, showQw, callPhone - 用于执行具体业务操作

规划规则：
- 简单指令：直接映射为单个业务工具调用
- 复杂指令：分解为多个业务工具的顺序调用
- 用户中断：使用Plan管理工具进行动态调整

输出格式：
[工具类型] 工具名 参数为 参数名: 参数值
```


### Planner智能判断规则

#### 用户意图识别
Planner需要通过语义判断用户输入，而非依赖确定性关键词：

```
用户输入示例 → Planner判断 → 调用工具

"先停一下" → 意图：暂停执行 → pause_plan
"我想修改一下" → 意图：需要调整计划 → modify_plan  
"刚才的步骤有问题" → 意图：重试上一步 → retry_step
"加一步联系交警" → 意图：添加新步骤 → add_step
"跳过这一步" → 意图：移除当前步骤 → remove_step
"不执行了" → 意图：取消整个计划 → cancel_plan
"继续刚才的" → 意图：恢复执行 → resume_plan
```

#### 提示词更新（Planner）
```
你是调度系统的规划助手，负责将用户指令转化为可执行的计划步骤。

可用工具分为两类：
1. **Plan管理工具**：pause_plan, resume_plan, modify_plan, cancel_plan等 - 用于动态调整计划
2. **业务MCP工具**：getPOI, showQw, callPhone - 用于执行具体业务操作

智能判断规则：
- **语义识别**：根据用户输入的自然语义判断意图，而非关键词匹配
- **上下文感知**：结合当前执行状态判断最适合的管理操作
- **模糊处理**：当用户意图不明确时，可询问确认或使用get_plan_status获取状态

规划规则：
- 简单指令：直接映射为单个业务工具调用
- 复杂指令：分解为多个业务工具的顺序执行
- 用户意图调整：智能识别用户意图并调用对应的管理工具

输出格式：
[工具类型] 工具名 参数为 参数名: 参数值
```

## MCP工具清单

### 1. 打开周边监控 (`getPOI`)
- **用途**: 根据案发地点坐标打开周边监控
- **参数**:
  - `x_position`: 案发地点X坐标
  - `y_position`: 案发地点Y坐标  
  - `afdd`: 案发地点地址

### 2. 查看值班人员 (`showQw`)
- **用途**: 根据管辖单位代码查看值班人员信息
- **参数**:
  - `gxdwdm`: 管辖单位代码

### 3. 拨打值班电话 (`callPhone`)
- **用途**: 拨打指定值班人员电话
- **参数**:
  - `phone`: 值班人员电话

## 会话隔离设计

### 会话管理
- **会话ID**：每个用户会话分配唯一execution_id
- **独立实例**：每个会话创建独立的PlanningFlow和Agent实例
- **资源隔离**：MCP client会话、工具实例、状态数据完全隔离
- **清理机制**：会话结束后自动清理相关资源

### 数据结构

#### 会话级数据
```json
{
  "session_id": "uuid-string",
  "emergency_data": {
    "coordinates": {"x": "123.456789", "y": "39.123456"},
    "address": "北京市朝阳区xxx路xxx号",
    "unit_code": "110105",
    "emergency_type": "重大警情"
  },
  "plan_id": "plan-uuid-string",
  "current_step": 0,
  "status": "running|paused|completed|failed"
}
```

#### 规划输出格式
```
简单指令：
[业务工具] getPOI 参数为 x_position: 123.456789, y_position: 39.123456, afdd: 北京市朝阳区xxx路xxx号

复杂指令：
步骤1: [业务工具] showQw 参数为 gxdwdm: 110105
步骤2: [业务工具] callPhone 参数为 phone: 13800138000

用户中断：
[系统工具] pause_plan 参数为 execution_id: session-uuid-string
```

---

# 附录C：OpenManus-based 实现规范

## 基于OpenManus的完整实现方案

### 架构重新设计

基于OpenManus框架，我们将调度系统重新设计为以下架构：

```
dispatch_system/
├── app/
│   ├── agent/
│   │   ├── dispatcher.py          # 调度代理 - 继承BaseAgent
│   │   └── dispatcher_prompt.py   # 调度代理提示词
│   ├── tool/
│   │   ├── dispatch_tools.py      # 调度工具集合
│   │   └── mcp_bridge.py          # MCP桥接工具
│   └── flow/
│       └── dispatch_flow.py       # 调度流程 - 继承PlanningFlow
├── config/
│   └── dispatch_config.toml       # 调度专用配置
├── tests/
│   └── test_dispatch_integration.py
└── run_dispatch.py                # 调度系统启动入口
```

### 核心组件实现

#### 1. 调度代理 (Dispatcher Agent)

```python
class DispatcherAgent(BaseAgent):
    """调度指挥代理"""
    
    def __init__(self):
        super().__init__()
        self.system_prompt = load_dispatch_prompt()
        self.tools = [
            MCPToolBridge("getPOI"),      # 周边监控
            MCPToolBridge("showQw"),      # 值班人员
            MCPToolBridge("callPhone"),   # 拨打电话
        ]
    
    async def execute(self, emergency_data: dict, command: str):
        """执行调度指令"""
        context = {
            "emergency": emergency_data,
            "command": command,
            "available_tools": [tool.name for tool in self.tools]
        }
        
        # 使用OpenManus的规划能力
        response = await self.llm.achat(
            messages=[
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=json.dumps(context))
            ],
            tools=[tool.schema for tool in self.tools]
        )
        
        return await self.execute_tool_calls(response)
```

#### 2. 调度流程 (Dispatch Flow)

```python
class DispatchFlow(PlanningFlow):
    """调度指挥流程"""
    
    def __init__(self):
        super().__init__()
        self.dispatch_agent = DispatcherAgent()
    
    async def execute(self, emergency_data: dict, command: str) -> dict:
        """执行调度流程"""
        # 初始化执行记录
        execution_id = generate_execution_id()
        
        # 使用PlanningFlow的规划能力
        plan = await self.create_plan(
            objective=f"处理调度指令: {command}",
            context={"emergency_data": emergency_data},
            agent=self.dispatch_agent
        )
        
        # 执行计划
        result = await self.execute_plan(plan)
        
        return {
            "execution_id": execution_id,
            "plan": plan,
            "result": result
        }
```

#### 3. MCP桥接工具

```python
class MCPToolBridge(BaseTool):
    """MCP工具桥接器"""
    
    def __init__(self, tool_name: str):
        self.name = tool_name
        self.mcp_client = MCPClient()
    
    async def execute(self, **kwargs):
        """通过MCP调用工具"""
        return await self.mcp_client.call_tool(self.name, kwargs)
    
    @property
    def schema(self):
        """返回工具Schema"""
        return self.mcp_client.get_tool_schema(self.name)
```

### 配置规范

#### 调度配置 (dispatch_config.toml)

```toml
[llm]
model = "claude-3-7-sonnet-20250219"
base_url = "https://api.anthropic.com/v1/"
api_key = "YOUR_API_KEY"

[mcp]
server_url = "http://localhost:8080/mcp"
timeout = 30

[dispatch]
max_retries = 3
retry_delay = 1.0
execution_timeout = 300
```

### 启动入口

#### run_dispatch.py

```python
async def main():
    """调度系统主入口"""
    
    # 初始化配置
    config = Config()
    
    # 创建调度流程
    dispatch_flow = DispatchFlow()
    
    # 示例警情数据
    emergency_data = {
        "coordinates": {"x": 116.3974, "y": 39.9093},
        "address": "北京市东城区xxx路xxx号",
        "unit_code": "110101",
        "emergency_type": "交通事故",
        "description": "两车相撞，有人受伤"
    }
    
    # 执行调度
    result = await dispatch_flow.execute(
        emergency_data=emergency_data,
        command="一键处置"
    )
    
    print(f"执行完成: {result['execution_id']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 集成测试

#### test_dispatch_integration.py

```python
@pytest.mark.asyncio
async def test_dispatch_workflow():
    """测试完整调度流程"""
    
    dispatch_flow = DispatchFlow()
    
    emergency_data = {
        "coordinates": {"x": 116.3974, "y": 39.9093},
        "address": "测试地址",
        "unit_code": "110101",
        "emergency_type": "测试警情",
        "description": "测试描述"
    }
    
    result = await dispatch_flow.execute(
        emergency_data=emergency_data,
        command="测试调度"
    )
    
    assert result["execution_id"] is not None
    assert "plan" in result
    assert "result" in result
```

### 部署方案

#### 1. 开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 启动MCP服务器
python run_mcp_server.py

# 运行调度系统
python run_dispatch.py
```

#### 2. 生产环境

```bash
# 使用Docker部署
docker-compose up -d

# 或者使用systemd服务
systemctl start dispatch-system
```

### 状态管理增强

#### 基于OpenManus的状态追踪

```python
class DispatchStateTracker:
    """调度状态追踪器"""
    
    def __init__(self):
        self.memory = Memory()
    
    def record_step(self, execution_id: str, step_data: dict):
        """记录步骤执行状态"""
        message = Message(
            role="system",
            content=json.dumps(step_data),
            metadata={"execution_id": execution_id}
        )
        self.memory.add_message(message)
    
    def get_execution_history(self, execution_id: str) -> List[dict]:
        """获取执行历史"""
        return self.memory.get_messages_by_metadata(
            metadata_key="execution_id",
            metadata_value=execution_id
        )
```

### 错误处理与重试

#### 基于OpenManus的容错机制

```python
class DispatchErrorHandler:
    """调度错误处理器"""
    
    async def handle_tool_error(self, error: Exception, context: dict) -> dict:
        """处理工具调用错误"""
        
        if isinstance(error, NetworkError):
            # 网络错误，重试
            return {"action": "retry", "delay": 1}
        
        elif isinstance(error, ToolNotFoundError):
            # 工具不存在，通知用户
            return {"action": "notify", "message": "工具不可用，请联系管理员"}
        
        else:
            # 其他错误，记录并跳过
            return {"action": "skip", "reason": str(error)}
```

### 性能优化

#### 1. 并发执行

```python
class ConcurrentDispatchExecutor:
    """并发调度执行器"""
    
    async def execute_parallel(self, steps: List[dict]) -> List[dict]:
        """并行执行独立步骤"""
        
        # 分析步骤依赖关系
        dependency_graph = self.build_dependency_graph(steps)
        
        # 按依赖层级并发执行
        results = []
        for level in dependency_graph.get_levels():
            level_results = await asyncio.gather(*[
                self.execute_step(step) for step in level
            ])
            results.extend(level_results)
        
        return results
```

#### 2. 缓存优化

```python
class DispatchCache:
    """调度缓存管理"""
    
    def __init__(self):
        self.tool_cache = TTLCache(maxsize=1000, ttl=300)
        self.location_cache = TTLCache(maxsize=500, ttl=600)
    
    def cache_tool_result(self, tool_name: str, params: dict, result: Any):
        """缓存工具调用结果"""
        key = f"{tool_name}:{hash_dict(params)}"
        self.tool_cache[key] = result
    
    def get_cached_result(self, tool_name: str, params: dict) -> Optional[Any]:
        """获取缓存结果"""
        key = f"{tool_name}:{hash_dict(params)}"
        return self.tool_cache.get(key)
```

### 监控与日志

#### 基于OpenManus的监控集成

```python
class DispatchMonitor:
    """调度监控器"""
    
    def __init__(self):
        self.logger = Logger("dispatch")
        self.metrics = MetricsCollector()
    
    def record_execution(self, execution_id: str, duration: float, success: bool):
        """记录执行指标"""
        self.metrics.record(
            "dispatch_execution",
            value=duration,
            tags={"execution_id": execution_id, "success": success}
        )
    
    def log_step_completion(self, step_name: str, result: Any):
        """记录步骤完成"""
        self.logger.info(f"Step completed: {step_name}", extra={"result": result})
```

### 扩展接口

#### 1. 自定义工具扩展

```python
class CustomToolExtension:
    """自定义工具扩展"""
    
    def register_tool(self, tool_name: str, tool_schema: dict, tool_handler: Callable):
        """注册自定义工具"""
        ToolRegistry.register(tool_name, tool_schema, tool_handler)
```

#### 2. 流程扩展

```python
class CustomDispatchFlow(DispatchFlow):
    """自定义调度流程"""
    
    async def custom_planning(self, emergency_data: dict) -> List[dict]:
        """自定义规划逻辑"""
        # 实现特定的规划算法
        pass
```

### 总结

基于OpenManus的调度系统实现具有以下优势：

1. **架构一致性**：与OpenManus框架完全兼容
2. **功能完整性**：复用OpenManus的所有核心能力
3. **扩展灵活性**：支持自定义工具和流程扩展
4. **维护简单性**：统一的技术栈和开发模式
5. **性能优化**：利用OpenManus的并发和缓存机制

此方案提供了从原型到生产的完整实现路径，确保调度系统的稳定性和可扩展性。