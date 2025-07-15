"""
参数传递和依赖管理系统
处理SDL执行中的参数依赖、上下文管理和结果传递
"""

import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import jinja2
from datetime import datetime


class DependencyType(str, Enum):
    PARAMETER = "parameter"      # 参数依赖
    RESULT = "result"           # 结果依赖
    CONDITION = "condition"     # 条件依赖
    PARALLEL = "parallel"       # 并行依赖
    SEQUENTIAL = "sequential"   # 顺序依赖


@dataclass
class Dependency:
    """依赖关系定义"""
    step_id: str
    depends_on: str
    dependency_type: DependencyType
    required_fields: List[str] = field(default_factory=list)
    condition: Optional[str] = None
    timeout: int = 30


@dataclass
class ExecutionContext:
    """执行上下文"""
    execution_id: str
    global_parameters: Dict[str, Any]
    step_results: Dict[str, Any] = field(default_factory=dict)
    step_status: Dict[str, str] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    
    def get_available_data(self) -> Dict[str, Any]:
        """获取所有可用数据（参数+步骤结果）"""
        data = self.global_parameters.copy()
        data.update(self.step_results)
        return data


class ParameterResolver:
    """参数解析器"""
    
    def __init__(self):
        self.jinja_env = jinja2.Environment()
        self.template_cache = {}
    
    def resolve_parameters(self, parameters: Dict[str, Any], 
                          context: ExecutionContext) -> Tuple[Dict[str, Any], List[str]]:
        """解析参数模板，返回解析后的参数和依赖列表"""
        resolved = {}
        dependencies = []
        
        for key, value in parameters.items():
            resolved_value, deps = self._resolve_value(value, context)
            resolved[key] = resolved_value
            dependencies.extend(deps)
        
        return resolved, list(set(dependencies))
    
    def _resolve_value(self, value: Any, context: ExecutionContext) -> Tuple[Any, List[str]]:
        """解析单个值"""
        dependencies = []
        
        if isinstance(value, str):
            # 解析模板字符串
            resolved, deps = self._resolve_template_string(value, context)
            dependencies.extend(deps)
            return resolved, dependencies
        
        elif isinstance(value, dict):
            # 递归解析字典
            resolved = {}
            for k, v in value.items():
                resolved_v, deps = self._resolve_value(v, context)
                resolved[k] = resolved_v
                dependencies.extend(deps)
            return resolved, dependencies
        
        elif isinstance(value, list):
            # 递归解析列表
            resolved = []
            for item in value:
                resolved_item, deps = self._resolve_value(item, context)
                resolved.append(resolved_item)
                dependencies.extend(deps)
            return resolved, dependencies
        
        else:
            # 原始值
            return value, []
    
    def _resolve_template_string(self, template: str, 
                                context: ExecutionContext) -> Tuple[str, List[str]]:
        """解析模板字符串"""
        if "{{" not in template:
            return template, []
        
        # 提取依赖
        dependencies = self._extract_dependencies(template)
        
        # 检查依赖是否可用
        available_data = context.get_available_data()
        
        try:
            jinja_template = self.jinja_env.from_string(template)
            resolved = jinja_template.render(**available_data)
            return resolved, dependencies
        except Exception as e:
            raise ValueError(f"模板解析失败: {template}, 错误: {e}")
    
    def _extract_dependencies(self, template: str) -> List[str]:
        """从模板中提取依赖"""
        dependencies = []
        
        # 查找 {{ variable }} 格式的引用
        matches = re.findall(r'\{\{\s*([\w\.]+)\s*\}\}', template)
        for match in matches:
            # 解析如 step1.result.field 的格式
            parts = match.split('.')
            if len(parts) >= 1:
                dependencies.append(parts[0])
        
        return dependencies


class ConditionEvaluator:
    """条件评估器"""
    
    def __init__(self):
        self.jinja_env = jinja2.Environment()
    
    def evaluate_condition(self, condition: str, 
                          context: ExecutionContext) -> bool:
        """评估条件表达式"""
        if not condition:
            return True
        
        available_data = context.get_available_data()
        
        try:
            template = self.jinja_env.from_string(f"{{{{ {condition} }}}}")
            result = template.render(**available_data)
            
            # 安全地评估布尔表达式
            return self._safe_eval(result)
        except Exception as e:
            print(f"条件评估失败: {condition}, 错误: {e}")
            return False
    
    def _safe_eval(self, expression: str) -> bool:
        """安全地评估布尔表达式"""
        # 只允许简单的布尔表达式
        allowed_chars = re.compile(r'^[\w\s\.\[\]\(\)\",\'\=\!\u003c\u003e\&\|]+$')
        if not allowed_chars.match(str(expression)):
            return False
        
        try:
            # 将字符串转换为布尔值
            expr = str(expression).strip().lower()
            if expr in ['true', '1', 'yes', 'on']:
                return True
            elif expr in ['false', '0', 'no', 'off']:
                return False
            
            # 评估数值比较
            return bool(eval(expr))
        except Exception:
            return False


class DependencyAnalyzer:
    """依赖分析器"""
    
    def __init__(self):
        self.dependencies: Dict[str, List[Dependency]] = {}
    
    def analyze_plan(self, plan: Dict[str, Any]) -> Dict[str, List[Dependency]]:
        """分析执行计划中的依赖关系"""
        self.dependencies = {}
        
        # 分析步骤依赖
        for step in plan.get('steps', []):
            self._analyze_step_dependencies(step)
        
        # 分析阶段依赖
        for phase in plan.get('phases', []):
            self._analyze_phase_dependencies(phase)
        
        return self.dependencies
    
    def _analyze_step_dependencies(self, step: Dict[str, Any]):
        """分析步骤依赖"""
        step_id = step.get('id')
        
        # 显式依赖
        for dep_id in step.get('depends_on', []):
            self.add_dependency(step_id, dep_id, DependencyType.SEQUENTIAL)
        
        # 条件依赖
        condition = step.get('condition')
        if condition:
            self._extract_condition_dependencies(step_id, condition)
        
        # 参数依赖
        parameters = step.get('parameters', {})
        self._extract_parameter_dependencies(step_id, parameters)
    
    def _analyze_phase_dependencies(self, phase: Dict[str, Any]):
        """分析阶段依赖"""
        phase_name = phase.get('name')
        
        for dep_name in phase.get('depends_on', []):
            self.add_dependency(phase_name, dep_name, DependencyType.SEQUENTIAL)
    
    def _extract_condition_dependencies(self, step_id: str, condition: str):
        """提取条件中的依赖"""
        dependencies = self._extract_references(condition)
        for dep in dependencies:
            self.add_dependency(step_id, dep, DependencyType.CONDITION)
    
    def _extract_parameter_dependencies(self, step_id: str, parameters: Dict[str, Any]):
        """提取参数中的依赖"""
        def extract_from_value(value):
            if isinstance(value, str):
                return self._extract_references(value)
            elif isinstance(value, dict):
                refs = []
                for v in value.values():
                    refs.extend(extract_from_value(v))
                return refs
            elif isinstance(value, list):
                refs = []
                for item in value:
                    refs.extend(extract_from_value(item))
                return refs
            return []
        
        refs = extract_from_value(parameters)
        for ref in refs:
            self.add_dependency(step_id, ref, DependencyType.PARAMETER)
    
    def _extract_references(self, text: str) -> List[str]:
        """提取引用"""
        refs = []
        
        # 查找 {{ step.field }} 格式的引用
        matches = re.findall(r'\{\{\s*([\w\.]+?)\s*\}\}', str(text))
        for match in matches:
            parts = match.split('.')
            if len(parts) >= 1:
                refs.append(parts[0])
        
        return refs
    
    def add_dependency(self, from_step: str, to_step: str, 
                      dependency_type: DependencyType):
        """添加依赖关系"""
        if from_step not in self.dependencies:
            self.dependencies[from_step] = []
        
        dependency = Dependency(
            step_id=from_step,
            depends_on=to_step,
            dependency_type=dependency_type
        )
        
        # 避免重复依赖
        existing = next((d for d in self.dependencies[from_step] 
                        if d.depends_on == to_step and d.dependency_type == dependency_type), None)
        if not existing:
            self.dependencies[from_step].append(dependency)
    
    def get_execution_order(self, steps: List[Dict[str, Any]]) -> List[str]:
        """计算执行顺序"""
        # 拓扑排序
        graph = {}
        for step in steps:
            step_id = step.get('id')
            graph[step_id] = step.get('depends_on', [])
        
        # 使用Kahn算法进行拓扑排序
        in_degree = {step_id: 0 for step_id in graph}
        for step_id in graph:
            for dep in graph[step_id]:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
        order = []
        
        while queue:
            current = queue.pop(0)
            order.append(current)
            
            for step_id, deps in graph.items():
                if current in deps:
                    in_degree[step_id] -= 1
                    if in_degree[step_id] == 0:
                        queue.append(step_id)
        
        if len(order) != len(steps):
            raise ValueError("存在循环依赖")
        
        return order


class ContextManager:
    """上下文管理器"""
    
    def __init__(self):
        self.contexts: Dict[str, ExecutionContext] = {}
    
    def create_context(self, execution_id: str, 
                      global_parameters: Dict[str, Any]) -> ExecutionContext:
        """创建执行上下文"""
        context = ExecutionContext(
            execution_id=execution_id,
            global_parameters=global_parameters
        )
        self.contexts[execution_id] = context
        return context
    
    def update_step_result(self, execution_id: str, step_id: str, 
                          result: Any, status: str):
        """更新步骤结果"""
        if execution_id in self.contexts:
            context = self.contexts[execution_id]
            context.step_results[step_id] = result
            context.step_status[step_id] = status
    
    def get_context(self, execution_id: str) -> Optional[ExecutionContext]:
        """获取执行上下文"""
        return self.contexts.get(execution_id)
    
    def is_step_ready(self, execution_id: str, step_id: str, 
                     dependencies: List[Dependency]) -> Tuple[bool, List[str]]:
        """检查步骤是否准备好执行"""
        context = self.get_context(execution_id)
        if not context:
            return False, ["上下文不存在"]
        
        ready = True
        missing_deps = []
        
        for dep in dependencies:
            if dep.depends_on not in context.step_status:
                missing_deps.append(dep.depends_on)
            elif context.step_status[dep.depends_on] != "completed":
                ready = False
                missing_deps.append(dep.depends_on)
        
        return ready, missing_deps
    
    def cleanup_context(self, execution_id: str):
        """清理执行上下文"""
        if execution_id in self.contexts:
            del self.contexts[execution_id]


class ResultPropagator:
    """结果传播器"""
    
    def __init__(self):
        self.propagation_rules = {}
    
    def setup_propagation(self, step_id: str, 
                         output_mapping: Dict[str, str]):
        """设置结果传播规则"""
        self.propagation_rules[step_id] = output_mapping
    
    def propagate_results(self, execution_id: str, step_id: str, 
                         result: Any, context: ExecutionContext):
        """传播步骤结果"""
        if step_id not in self.propagation_rules:
            return
        
        rules = self.propagation_rules[step_id]
        propagated = {}
        
        for target_field, source_path in rules.items():
            value = self._extract_nested_value(result, source_path)
            if value is not None:
                propagated[target_field] = value
        
        # 将传播的结果添加到上下文
        context.step_results[f"{step_id}_output"] = propagated
    
    def _extract_nested_value(self, data: Any, path: str) -> Any:
        """提取嵌套值"""
        if not path or not isinstance(data, dict):
            return data
        
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current


class DependencyManager:
    """依赖管理器 - 主类"""
    
    def __init__(self):
        self.analyzer = DependencyAnalyzer()
        self.resolver = ParameterResolver()
        self.evaluator = ConditionEvaluator()
        self.context_manager = ContextManager()
        self.propagator = ResultPropagator()
    
    async def prepare_execution(self, plan: Dict[str, Any], 
                               global_parameters: Dict[str, Any]) -> str:
        """准备执行"""
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # 分析依赖关系
        dependencies = self.analyzer.analyze_plan(plan)
        
        # 创建执行上下文
        context = self.context_manager.create_context(execution_id, global_parameters)
        
        # 计算执行顺序
        execution_order = self.analyzer.get_execution_order(plan.get('steps', []))
        
        return execution_id
    
    async def execute_step_with_dependencies(self, execution_id: str, 
                                           step: Dict[str, Any], 
                                           tool_executor: Callable) -> Dict[str, Any]:
        """执行带依赖的步骤"""
        context = self.context_manager.get_context(execution_id)
        if not context:
            raise ValueError("执行上下文不存在")
        
        step_id = step.get('id')
        
        # 检查条件
        condition = step.get('condition')
        if condition and not self.evaluator.evaluate_condition(condition, context):
            return {
                'step_id': step_id,
                'status': 'skipped',
                'reason': '条件不满足'
            }
        
        # 解析参数
        parameters = step.get('parameters', {})
        try:
            resolved_params, dependencies = self.resolver.resolve_parameters(parameters, context)
        except Exception as e:
            return {
                'step_id': step_id,
                'status': 'failed',
                'error': f"参数解析失败: {e}"
            }
        
        # 执行工具
        try:
            result = await tool_executor(step.get('tool'), resolved_params)
            
            # 更新上下文
            self.context_manager.update_step_result(execution_id, step_id, result, 'completed')
            
            # 传播结果
            if 'output_mapping' in step:
                self.propagator.propagate_results(execution_id, step_id, result, context)
            
            return {
                'step_id': step_id,
                'status': 'completed',
                'result': result
            }
            
        except Exception as e:
            self.context_manager.update_step_result(execution_id, step_id, str(e), 'failed')
            return {
                'step_id': step_id,
                'status': 'failed',
                'error': str(e)
            }
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """获取执行状态"""
        context = self.context_manager.get_context(execution_id)
        if not context:
            return {'error': '执行不存在'}
        
        return {
            'execution_id': execution_id,
            'start_time': context.start_time.isoformat(),
            'global_parameters': context.global_parameters,
            'step_results': context.step_results,
            'step_status': context.step_status,
            'available_data': context.get_available_data()
        }
    
    def cleanup(self, execution_id: str):
        """清理执行资源"""
        self.context_manager.cleanup_context(execution_id)


# 使用示例
async def example_usage():
    """使用示例"""
    manager = DependencyManager()
    
    # 模拟执行计划
    plan = {
        'steps': [
            {
                'id': 'step1',
                'tool': 'getPOI',
                'parameters': {
                    'x_position': '{{ coordinates.x }}',
                    'y_position': '{{ coordinates.y }}',
                    'afdd': '{{ address }}'
                }
            },
            {
                'id': 'step2',
                'tool': 'showQw',
                'parameters': {
                    'gxdwdm': '{{ unit_code }}'
                },
                'depends_on': ['step1']
            },
            {
                'id': 'step3',
                'tool': 'callPhone',
                'parameters': {
                    'phone': '{{ step2.primary_contact }}'
                },
                'depends_on': ['step2'],
                'condition': '{{ step2.staff_count > 0 }}'
            }
        ]
    }
    
    # 准备执行
    execution_id = await manager.prepare_execution(
        plan,
        {
            'coordinates': {'x': 116.3974, 'y': 39.9093},
            'address': '北京市朝阳区建国门外大街1号',
            'unit_code': '110105'
        }
    )
    
    # 模拟工具执行器
    async def mock_tool_executor(tool_name: str, parameters: Dict[str, Any]) -> Any:
        if tool_name == 'getPOI':
            return {"monitors": ["CAM001", "CAM002"]}
        elif tool_name == 'showQw':
            return {"primary_contact": "13800138000", "staff_count": 2}
        elif tool_name == 'callPhone':
            return {"status": "connected", "duration": 30}
    
    # 执行步骤
    for step in plan['steps']:
        result = await manager.execute_step_with_dependencies(
            execution_id, step, mock_tool_executor
        )
        print(f"步骤 {step['id']}: {result}")
    
    # 清理
    manager.cleanup(execution_id)


if __name__ == "__main__":
    asyncio.run(example_usage())