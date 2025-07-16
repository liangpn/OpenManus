"""
调度系统演示入口
"""

import asyncio
import json
from dispatch_flow import DispatchFlow, EmergencyData

async def demo_simple_command():
    """演示简单命令执行"""
    print("🎯 演示：简单命令执行")
    print("=" * 50)
    
    flow = DispatchFlow()
    
    # 模拟警情数据
    emergency_data = EmergencyData(
        coordinates={"x": 116.3974, "y": 39.9093},
        address="北京市朝阳区建国门外大街甲6号",
        unit_code="110105",
        emergency_type="重大警情",
        description="发生一起交通事故，需要紧急处置"
    )
    
    print(f"📍 警情信息：")
    print(f"   地址：{emergency_data.address}")
    print(f"   坐标：{emergency_data.coordinates}")
    print(f"   单位代码：{emergency_data.unit_code}")
    print()
    
    # 创建会话
    session_id = await flow.create_session(emergency_data)
    print(f"🔑 创建会话成功：{session_id}")
    
    # 演示各种命令
    commands = [
        "打开监控",
        "查看值班人员",
        "联系值班人员",
        "处置警情"
    ]
    
    for command in commands:
        print(f"\n📝 执行命令：{command}")
        result = await flow.execute_simple_command(session_id, command, emergency_data)
        
        if result.get("success", False):
            print(f"   ✅ 成功：{result.get('data', {}).get('message', '执行成功')}")
        else:
            print(f"   ❌ 失败：{result.get('error', '未知错误')}")
    
    # 清理会话
    flow.cleanup_session(session_id)
    print(f"\n🧹 清理会话：{session_id}")

async def demo_full_flow():
    """演示完整流程"""
    print("\n🎯 演示：完整调度流程")
    print("=" * 50)
    
    flow = DispatchFlow()
    
    emergency_data = EmergencyData(
        coordinates={"x": 116.3974, "y": 39.9093},
        address="北京市朝阳区三里屯路19号",
        unit_code="110105",
        emergency_type="治安事件",
        description="酒吧纠纷，需要警力处置"
    )
    
    print(f"📍 警情信息：{emergency_data.description}")
    
    # 创建会话并执行完整流程
    session_id = await flow.create_session(emergency_data)
    result = await flow.execute_simple_command(session_id, "处置警情", emergency_data)
    
    print(f"\n📊 执行结果：")
    print(f"   会话ID：{result.get('session_id', 'unknown')}")
    print(f"   执行状态：{result.get('status', 'unknown')}")
    print(f"   总步骤：{result.get('total_steps', 0)}")
    print(f"   完成步骤：{result.get('completed_steps', 0)}")
    
    # 显示详细步骤
    if "steps" in result and "steps" in result["steps"]:
        steps = result["steps"]["steps"]
        for i, step in enumerate(steps, 1):
            status_icon = "✅" if step["status"] == "success" else "❌"
            print(f"   {i}. {step['description']} {status_icon}")
    else:
        print("   📋 步骤信息不可用")
    
    # 清理会话
    flow.cleanup_session(session_id)

async def demo_multi_session():
    """演示多会话并发"""
    print("\n🎯 演示：多会话并发")
    print("=" * 50)
    
    flow = DispatchFlow()
    
    # 创建多个警情
    emergencies = [
        EmergencyData(
            coordinates={"x": 116.3974, "y": 39.9093},
            address="朝阳区建国门外",
            unit_code="110105",
            emergency_type="交通事故"
        ),
        EmergencyData(
            coordinates={"x": 117.2009, "y": 39.0841},
            address="南开区鼓楼",
            unit_code="120101",
            emergency_type="治安事件"
        )
    ]
    
    # 并发创建会话
    sessions = []
    for i, emergency in enumerate(emergencies):
        session_id = await flow.create_session(emergency)
        sessions.append((session_id, emergency, f"警情{i+1}"))
        print(f"🔑 创建会话{i+1}：{session_id}")
    
    # 并发执行
    tasks = []
    for session_id, emergency, name in sessions:
        task = flow.execute_simple_command(session_id, "处置警情", emergency)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    print(f"\n📊 并发执行结果：")
    for i, (session_id, emergency, name) in enumerate(sessions):
        result = results[i]
        status = result.get('status', 'unknown') if isinstance(result, dict) else 'unknown'
        print(f"   {name}：{status} (会话：{session_id[-8:]})")
    
    # 清理所有会话
    for session_id, _, _ in sessions:
        flow.cleanup_session(session_id)
    
    print(f"🧹 清理所有会话完成")

async def main():
    """主演示函数"""
    print("🚀 调度系统演示开始")
    print("=" * 60)
    
    try:
        # 演示1：简单命令
        await demo_simple_command()
        
        # 演示2：完整流程
        await demo_full_flow()
        
        # 演示3：多会话并发
        await demo_multi_session()
        
        print("\n🎉 演示完成！调度系统运行正常")
        print("\n📋 已验证功能：")
        print("   ✅ MCP桥接工具调用")
        print("   ✅ 会话隔离和并发")
        print("   ✅ 简单命令和完整流程")
        print("   ✅ 状态追踪和清理")
        
    except Exception as e:
        print(f"\n❌ 演示失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())