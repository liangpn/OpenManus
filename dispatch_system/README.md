# 公安大厅警情调度系统

## 🎯 系统概述

这是一个基于OpenManus架构的简化警情调度系统，专注于**实时步骤反馈**和**业务指导文件驱动**的调度流程。

## 🚀 核心特性

### ✅ 已实现功能
- **简单命令**: 1:1命令到工具映射 (`open_monitor`, `show_staff`, `call_staff`)
- **复杂命令**: 多步骤按业务逻辑执行 (`handle_all` → [getPOI → showQw → callPhone])
- **业务指导**: 通过.md文件定义业务规则
- **实时状态**: 每个步骤的实时执行状态
- **参数传递**: 步骤间的参数动态传递
- **扩展设计**: 支持未来30+工具的无缝集成

### 📋 当前工具集
```yaml
当前可用工具 (3个):
- getPOI: 打开周边监控
- showQw: 查看值班人员  
- callPhone: 联系值班人员

未来扩展工具 (27个规划):
- assessThreatLevel: 威胁等级评估
- dispatchSWAT: 派遣特警
- coordinateEMS: 协调急救
- lockdownArea: 封锁区域
- controlTraffic: 实施交通管制
```

## 🏗️ 架构设计

### 核心组件
```
dispatch_system/
├── core/                    # 核心业务层
│   ├── dispatcher.py        # 主调度器
│   ├── simple_planner.py    # 轻量级规划器
│   ├── tool_registry.py     # 工具注册与管理
│   ├── dependency_manager.py # 参数依赖管理
│   └── state_manager.py     # 状态管理器（可选扩展）
├── flow_specs/              # 命令规范
│   ├── simple_commands.yml  # 简单命令映射
│   └── complex_commands.md  # 复杂命令拆解
├── ARCHITECTURE.md          # 架构文档
└── README.md                # 使用文档
```

## 🎯 使用示例

### 1. 简单命令执行
```python
# 调度员输入: "打开监控"
result = await dispatcher.dispatch_command("open_monitor", {
    "coordinates": {"x": 116.3974, "y": 39.9093},
    "address": "北京市朝阳区建国门外大街1号"
})
```

### 2. 复杂命令执行
```python
# 调度员输入: "一键处置"
result = await dispatcher.dispatch_command("handle_all", {
    "emergency_type": "一般交通事故",
    "coordinates": {"x": 116.3974, "y": 39.9093},
    "address": "北京市朝阳区建国门外大街1号",
    "unit_code": "110105"
})
# 自动执行: [getPOI → showQw → callPhone]
```

### 3. 实时状态查询
```python
# 查看调度进度
status = dispatcher.get_dispatch_status(dispatch_id)
# 返回: {"current_step": 2, "total_steps": 3, "status": "running"}
```

## 📊 业务规则引擎

### 警情类型自动识别
- **一般警情**: 轻微事故、纠纷、治安事件
- **重大警情**: 刑事案件、交通事故、暴力事件、群体性事件

### 自动调度逻辑
```yaml
一般警情:
  步骤: [open_monitor → show_staff → call_staff]
  监控范围: 500米
  警力需求: 1-2人

重大警情:
  步骤: [open_monitor → show_staff → call_staff → assess_threat]
  监控范围: 1000米
  警力需求: 3-5人
```

## 🛠️ 快速开始

### 1. 安装依赖
```bash
cd dispatch_system
pip install -r requirements.txt
```

### 2. 运行演示
```bash
python core/dispatcher.py
```

### 3. 业务逻辑
业务逻辑已硬编码为固定三步流程，如需调整请直接修改 `core/simple_planner.py`

## 🔄 扩展指南

### 添加新工具
1. 在MCP server中添加新工具定义
2. 在 `core/tool_registry.py` 中注册工具映射
3. 在 `core/simple_planner.py` 中添加使用规则

## 📈 性能指标

### 响应时间目标
- **监控打开**: ≤1分钟
- **人员联系**: ≤2分钟  
- **一键处置**: ≤5分钟

### 成功率目标
- **工具执行成功率**: ≥99%
- **业务逻辑准确率**: ≥95%
- **用户满意度**: ≥90%

## 🎯 成功标准

### 调度员视角
- ✅ 输入简单命令立即执行
- ✅ 复杂命令按业务逻辑自动拆解
- ✅ 实时看到每一步的执行状态
- ✅ 无需了解技术细节，专注业务判断

### 系统视角
- ✅ 支持MCP工具无缝扩展
- ✅ 固定业务逻辑确保一致性
- ✅ 参数传递自动化
- ✅ 错误处理和降级机制

## 🔮 未来规划

### 即将实现
- [ ] Web界面实时展示调度状态
- [ ] 语音命令识别
- [ ] 移动端调度应用
- [ ] AI辅助警情分析

### 长期规划
- [ ] 多部门协调系统
- [ ] 实时视频分析
- [ ] 预测性调度
- [ ] 跨地区联动调度

---

**这就是调度员期望的业务流程！** 🚔👮‍♂️