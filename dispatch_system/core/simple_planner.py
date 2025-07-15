"""
轻量级Planner - 业务指导文件驱动
读取.md业务指导文件，生成符合业务场景的调度步骤
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class PlanningStep:
    """规划步骤"""
    step_id: str
    tool_name: str
    parameters: Dict[str, Any]
    description: str = ""
    priority: int = 1
    depends_on: List[str] = None
    condition: Optional[str] = None


@dataclass
class BusinessGuidance:
    """业务指导信息"""
    severity: str
    recommended_tools: List[str]
    parameter_templates: Dict[str, Any]
    business_rules: List[str]
    timing_guidelines: Dict[str, int]


class SimplePlanner:
    """轻量级业务指导驱动规划器"""
    
    def __init__(self, guidance_dir: str = "dispatch_system/business_guidance"):
        self.guidance_dir = Path(guidance_dir)
        self.business_rules = {}
        self._load_business_rules()
    
    def _load_business_rules(self):
        """加载业务指导文件"""
        # 加载警情类型指导
        emergency_dir = self.guidance_dir / "emergency_types"
        if emergency_dir.exists():
            for file in emergency_dir.glob("*.md"):
                self.business_rules[file.stem] = self._parse_guidance_file(file)
        
        # 加载模板指导
        template_dir = self.guidance_dir / "templates"
        if template_dir.exists():
            for file in template_dir.glob("*.md"):
                self.business_rules[file.stem] = self._parse_guidance_file(file)
    
    def _parse_guidance_file(self, file_path: Path) -> Dict[str, Any]:
        """解析业务指导文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        guidance = {
            'type': file_path.stem,
            'recommended_tools': [],
            'parameter_templates': {},
            'business_rules': [],
            'timing_guidelines': {}
        }
        
        # 提取工具推荐
        tool_matches = re.findall(r'- (.+?)工具[:：]?', content)
        guidance['recommended_tools'] = [self._extract_tool_name(tool) for tool in tool_matches]
        
        # 提取业务规则
        rule_matches = re.findall(r'### (.+?)\n(.+?)(?=\n###|\Z)', content, re.DOTALL)
        for title, content in rule_matches:
            guidance['business_rules'].append({
                'title': title.strip(),
                'content': content.strip()
            })
        
        # 提取参数模板
        param_matches = re.findall(r'`(\w+?)`[:：]\s*(.+?)\n', content)
        for param, template in param_matches:
            guidance['parameter_templates'][param] = template.strip()
        
        # 提取时间指导
        time_matches = re.findall(r'- (.+?)[:：]\s*(\d+)分钟?', content)
        for action, minutes in time_matches:
            guidance['timing_guidelines'][action.strip()] = int(minutes)
        
        return guidance
    
    def _extract_tool_name(self, tool_text: str) -> str:
        """提取工具名称"""
        tool_map = {
            '打开周边监控': 'getPOI',
            '查看值班人员': 'showQw',
            '拨打电话': 'callPhone',
            '威胁等级评估': 'assessThreatLevel',
            '派遣特警': 'dispatchSWAT',
            '协调急救': 'coordinateEMS',
            '封锁区域': 'lockdownArea',
            '实施交通管制': 'controlTraffic'
        }
        
        for chinese, english in tool_map.items():
            if chinese in tool_text:
                return english
        
        # 回退到基础工具
        if '监控' in tool_text:
            return 'getPOI'
        elif '值班' in tool_text or '人员' in tool_text:
            return 'showQw'
        elif '电话' in tool_text:
            return 'callPhone'
        
        return 'getPOI'  # 默认工具
    
    def plan_dispatch(self, emergency_data: Dict[str, Any]) -> List[PlanningStep]:
        """根据警情数据生成调度计划"""
        steps = []
        
        # 根据警情类型选择指导文件
        emergency_type = emergency_data.get('emergency_type', '一般警情')
        guidance_key = self._map_to_guidance_key(emergency_type)
        
        guidance = self.business_rules.get(guidance_key, self.business_rules.get('一般警情', {}))
        
        # 生成基础步骤
        base_steps = self._generate_base_steps(emergency_data, guidance)
        steps.extend(base_steps)
        
        # 根据严重程度调整
        severity_steps = self._adjust_by_severity(emergency_data, steps)
        
        return severity_steps
    
    def _map_to_guidance_key(self, emergency_type: str) -> str:
        """映射警情类型到指导文件"""
        type_mapping = {
            '轻微事故': '一般警情',
            '纠纷': '一般警情',
            '治安事件': '一般警情',
            '刑事案件': '重大警情',
            '交通事故': '重大警情',
            '暴力事件': '重大警情',
            '群体性事件': '重大警情'
        }
        
        return type_mapping.get(emergency_type, '一般警情')
    
    def _generate_base_steps(self, data: Dict[str, Any], 
                           guidance: Dict[str, Any]) -> List[PlanningStep]:
        """生成基础步骤"""
        steps = []
        
        # 步骤1：打开监控
        if 'getPOI' in guidance.get('recommended_tools', []):
            steps.append(PlanningStep(
                step_id="open_monitor",
                tool_name="getPOI",
                parameters={
                    "x_position": data.get('coordinates', {}).get('x', 0),
                    "y_position": data.get('coordinates', {}).get('y', 0),
                    "afdd": data.get('address', '')
                },
                description="打开现场周边监控，了解实时情况"
            ))
        
        # 步骤2：查看值班人员
        if 'showQw' in guidance.get('recommended_tools', []):
            steps.append(PlanningStep(
                step_id="check_staff",
                tool_name="showQw",
                parameters={
                    "gxdwdm": data.get('unit_code', '')
                },
                description="查看管辖单位值班人员情况",
                depends_on=["open_monitor"]
            ))
        
        # 步骤3：联系人员
        if 'callPhone' in guidance.get('recommended_tools', []):
            steps.append(PlanningStep(
                step_id="contact_staff",
                tool_name="callPhone",
                parameters={
                    "phone": "{{ check_staff.primary_contact }}"
                },
                description="联系值班人员到现场处置",
                depends_on=["check_staff"]
            ))
        
        return steps
    
    def _adjust_by_severity(self, data: Dict[str, Any], 
                          base_steps: List[PlanningStep]) -> List[PlanningStep]:
        """根据严重程度调整步骤"""
        adjusted_steps = base_steps.copy()
        
        # 根据威胁等级调整
        threat_level = data.get('threat_level', 'low')
        
        if threat_level == 'high':
            # 增加额外步骤
            adjusted_steps.append(PlanningStep(
                step_id="assess_threat",
                tool_name="assessThreatLevel",  # 未来扩展工具
                parameters={
                    "incident_type": data.get('emergency_type'),
                    "location": data.get('coordinates'),
                    "intensity": 8
                },
                description="评估威胁等级",
                priority=1
            ))
        
        return adjusted_steps
    
    def get_business_context(self, emergency_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取业务上下文"""
        emergency_type = emergency_data.get('emergency_type', '一般警情')
        guidance_key = self._map_to_guidance_key(emergency_type)
        
        guidance = self.business_rules.get(guidance_key, {})
        
        return {
            'emergency_type': emergency_type,
            'guidance_file': guidance_key,
            'recommended_tools': guidance.get('recommended_tools', []),
            'timing_guidelines': guidance.get('timing_guidelines', {}),
            'business_rules': guidance.get('business_rules', [])
        }
    
    def explain_planning(self, steps: List[PlanningStep], 
                        context: Dict[str, Any]) -> str:
        """解释规划依据"""
        explanation = f"""
基于{context['emergency_type']}的业务指导文件：{context['guidance_file']}

规划依据：
1. 推荐工具：{', '.join(context['recommended_tools'])}
2. 业务规则：{len(context['business_rules'])}条
3. 时间指导：{context['timing_guidelines']}

生成的步骤：
"""
        
        for i, step in enumerate(steps, 1):
            explanation += f"{i}. {step.description} (工具：{step.tool_name})\n"
        
        return explanation


# 使用示例
if __name__ == "__main__":
    planner = SimplePlanner()
    
    # 测试一般警情
    emergency_data = {
        'coordinates': {'x': 116.3974, 'y': 39.9093},
        'address': '北京市朝阳区建国门外大街1号',
        'unit_code': '110105',
        'emergency_type': '一般交通事故'
    }
    
    steps = planner.plan_dispatch(emergency_data)
    context = planner.get_business_context(emergency_data)
    
    print("=== 规划结果 ===")
    for step in steps:
        print(f"{step.step_id}: {step.tool_name} - {step.description}")
    
    print("\n=== 业务上下文 ===")
    print(json.dumps(context, ensure_ascii=False, indent=2))
    
    print("\n=== 规划解释 ===")
    print(planner.explain_planning(steps, context))