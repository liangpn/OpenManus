"""
单元测试：DispatchFlow完整流程测试
"""

import asyncio
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dispatch_flow import DispatchFlow, EmergencyData

async def test_create_session():
    """测试创建会话"""
    flow = DispatchFlow()
    
    emergency_data = EmergencyData(
        coordinates={"x": 116.3974, "y": 39.9093},
        address="北京市朝阳区测试地址",
        unit_code="110105",
        emergency_type="测试警情"
    )
    
    session_id = await flow.create_session(emergency_data)
    
    assert session_id is not None
    assert len(session_id) > 0
    assert session_id in flow.list_sessions()
    
    print(f"✅ 测试通过：创建会话 - {session_id}")
    return session_id

async def test_simple_command_get_poi():
    """测试简单命令：打开监控"""
    flow = DispatchFlow()
    
    emergency_data = EmergencyData(
        coordinates={"x": 116.3974, "y": 39.9093},
        address="北京市朝阳区测试地址",
        unit_code="110105",
        emergency_type="测试警情"
    )
    
    session_id = await flow.create_session(emergency_data)
    
    # 测试"打开监控"命令
    result = await flow.execute_simple_command(session_id, "打开监控", emergency_data)
    
    assert result["tool_name"] == "getPOI"
    assert result["session_id"] == session_id
    
    print(f"✅ 测试通过：打开监控命令 - 成功：{result['success']}")
    if result["success"]:
        print(f"   结果：{result['data'].get('message', '成功')}")
    else:
        print(f"   错误：{result['error']}")

async def test_simple_command_show_qw():
    """测试简单命令：查看值班人员"""
    flow = DispatchFlow()
    
    emergency_data = EmergencyData(
        coordinates={"x": 116.3974, "y": 39.9093},
        address="北京市朝阳区测试地址",
        unit_code="110105",
        emergency_type="测试警情"
    )
    
    session_id = await flow.create_session(emergency_data)
    
    # 测试"查看值班人员"命令
    result = await flow.execute_simple_command(session_id, "查看值班人员", emergency_data)
    
    assert result["tool_name"] == "showQw"
    assert result["session_id"] == session_id
    
    print(f"✅ 测试通过：查看值班人员命令 - 成功：{result['success']}")

async def test_full_flow():
    """测试完整流程"""
    flow = DispatchFlow()
    
    emergency_data = EmergencyData(
        coordinates={"x": 116.3974, "y": 39.9093},
        address="北京市朝阳区测试地址",
        unit_code="110105",
        emergency_type="测试警情"
    )
    
    session_id = await flow.create_session(emergency_data)
    
    # 测试完整流程
    result = await flow.execute_simple_command(session_id, "处置警情", emergency_data)
    
    assert result["flow_type"] == "full"
    assert result["total_steps"] == 3
    assert result["session_id"] == session_id
    assert result["status"] in ["completed", "failed"]
    
    print(f"✅ 测试通过：完整流程 - 状态：{result['status']}")
    print(f"   总步骤：{result['total_steps']}, 完成：{result['completed_steps']}")

async def test_session_status():
    """测试会话状态"""
    flow = DispatchFlow()
    
    emergency_data = EmergencyData(
        coordinates={"x": 116.3974, "y": 39.9093},
        address="北京市朝阳区测试地址",
        unit_code="110105",
        emergency_type="测试警情"
    )
    
    session_id = await flow.create_session(emergency_data)
    
    # 执行一些操作
    await flow.execute_simple_command(session_id, "打开监控", emergency_data)
    
    # 获取状态
    status = flow.get_session_status(session_id)
    
    assert status["session_id"] == session_id
    assert "total_steps" in status
    
    print("✅ 测试通过：会话状态获取")

async def test_multiple_sessions():
    """测试多会话并发"""
    flow = DispatchFlow()
    
    emergency_data1 = EmergencyData(
        coordinates={"x": 116.3974, "y": 39.9093},
        address="地址1",
        unit_code="110105",
        emergency_type="警情1"
    )
    
    emergency_data2 = EmergencyData(
        coordinates={"x": 117.2009, "y": 39.0841},
        address="地址2", 
        unit_code="120101",
        emergency_type="警情2"
    )
    
    # 并发创建会话
    session1 = await flow.create_session(emergency_data1)
    session2 = await flow.create_session(emergency_data2)
    
    assert session1 != session2
    assert len(flow.list_sessions()) == 2
    
    # 并发执行
    tasks = [
        flow.execute_simple_command(session1, "打开监控", emergency_data1),
        flow.execute_simple_command(session2, "查看值班人员", emergency_data2)
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 2
    assert results[0]["session_id"] == session1
    assert results[1]["session_id"] == session2
    
    print("✅ 测试通过：多会话并发")

async def test_session_cleanup():
    """测试会话清理"""
    flow = DispatchFlow()
    
    emergency_data = EmergencyData(
        coordinates={"x": 116.3974, "y": 39.9093},
        address="北京市朝阳区测试地址",
        unit_code="110105",
        emergency_type="测试警情"
    )
    
    session_id = await flow.create_session(emergency_data)
    
    # 清理会话
    flow.cleanup_session(session_id)
    
    assert session_id not in flow.list_sessions()
    
    # 验证状态获取会报错
    status = flow.get_session_status(session_id)
    assert "error" in status
    
    print("✅ 测试通过：会话清理")

async def main():
    """运行所有测试"""
    print("🧪 开始DispatchFlow完整流程测试...")
    
    try:
        session_id = await test_create_session()
        await test_simple_command_get_poi()
        await test_simple_command_show_qw()
        await test_full_flow()
        await test_session_status()
        await test_multiple_sessions()
        await test_session_cleanup()
        
        print("\n🎉 所有DispatchFlow测试通过！调度系统已就绪")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(main())