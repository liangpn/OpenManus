# 复杂命令拆解规范

## 调度员复杂命令拆解规则

### 🎯 核心原则
- **一个复杂命令 = 多个简单步骤**
- **步骤顺序 = 业务逻辑顺序**
- **参数传递 = 前一步结果给下一步**

---

## 📋 一键处置命令拆解

### 命令: `handle_all`
**调度员意图**: 一键完成所有必要处置

#### 拆解步骤:
1. **open_monitor** → **show_staff** → **call_staff**

#### 业务逻辑:
1. 先打开监控了解现场情况
2. 再查看值班人员情况
3. 最后联系值班人员

#### 参数传递:
```
step1: getPOI → 获取监控信息
step2: showQw → 使用unit_code获取人员信息  
step3: callPhone → 使用step2返回的phone号码
```

---

## 📊 标准拆解模板

### 模板: 基础处置流程
```
复杂命令: 基础处置
步骤顺序:
1. 信息收集 (getPOI)
2. 资源查看 (showQw)  
3. 人员联系 (callPhone)
```

### 模板: 紧急响应流程  
```
复杂命令: 紧急响应
步骤顺序:
1. 监控覆盖 (getPOI)
2. 人员调度 (showQw)
3. 直接联系 (callPhone)
```

---

## ⚡ 拆解规则

### 1. 顺序规则
- **信息优先**: 先收集信息，再采取行动
- **就近原则**: 先查看就近资源，再联系具体人员
- **最小依赖**: 每个步骤只依赖前一步结果

### 2. 参数传递规则  
- **监控结果**: 用于了解现场情况（不直接传递参数）
- **人员结果**: 提供phone参数给下一步
- **联系结果**: 用于确认联系成功

### 3. 错误处理规则
- **任何步骤失败**: 立即停止后续步骤
- **参数缺失**: 使用默认值或跳过该步骤
- **业务异常**: 上报给调度员人工处理

---

## 🎯 实际使用示例

### 调度员输入: `handle_all`
**业务场景**: 朝阳区重大警情
**拆解结果**:
```yaml
steps:
  - id: step1_open_monitor
    tool: getPOI
    parameters: {x: 116.3974, y: 39.9093, afdd: "朝阳区建国门外大街"}
    
  - id: step2_check_staff  
    tool: showQw
    parameters: {gxdwdm: "110105"}
    depends_on: [step1_open_monitor]
    
  - id: step3_contact_staff
    tool: callPhone  
    parameters: {phone: "{{step2_check_staff.phone}}"}
    depends_on: [step2_check_staff]
```

### 调度员输入: `open_monitor`
**业务场景**: 简单监控需求
**拆解结果**:
```yaml
steps:
  - id: step1_open_monitor
    tool: getPOI
    parameters: {x: 116.3974, y: 39.9093, afdd: "朝阳区建国门外大街"}
```

---

## 🔄 动态调整规则

### 情况1: 简单命令直接执行
- 调度员: `open_monitor`
- 执行: [getPOI]

### 情况2: 复杂命令按顺序执行  
- 调度员: `handle_all`
- 执行: [getPOI → showQw → callPhone]

### 情况3: 失败处理
- 如果`showQw`返回无人员 → 跳过`callPhone`
- 如果`getPOI`失败 → 继续执行后续步骤（业务决策）

---

## 📊 业务验证检查

### 拆解后的步骤是否符合调度员预期？
- [x] 监控 → 了解现场 ✓
- [x] 人员 → 查看可用警力 ✓  
- [x] 联系 → 联系具体人员 ✓
- [x] 顺序 → 逻辑合理 ✓

这就是调度员期望的业务流程！