"""
单元测试：DispatcherAgent测试
"""

import asyncio
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dispatcher_agent import DispatcherAgent
from mcp_bridge import MCPBridge

async def test_dispatcher_initialization():
    """测试代理初始化"""
    session_id = "test-dispatch-001"
    agent = DispatcherAgent(session_id)
    
    success = await agent.initialize()
    
    assert success == True
    assert agent.status == "ready"
    
    print("✅ 测试通过：代理初始化")

async def test_create_plan():
    """测试创建执行计划"""
    session_id = "test-dispatch-002"
    agent = DispatcherAgent(session_id)
    await agent.initialize()
    
    # 创建简单计划
    steps = [
        {
            "description": "打开周边监控",
            "tool_name": "getPOI",
            "parameters": {
                "x_position": 116.3974,
                "y_position": 39.9093,
                "afdd": "北京市朝阳区测试地址"
            }
        },
        {
            "description": "查看值班人员",
            "tool_name": "showQw",
            "parameters": {"gxdwdm": "110105"}
        }
    ]
    
    execution_steps = agent.create_plan(steps)
    
    assert len(execution_steps) == 2
    assert execution_steps[0].tool_name == "getPOI"
    assert execution_steps[1].tool_name == "showQw"
    assert execution_steps[0].status == "pending"
    
    print("✅ 测试通过：创建执行计划")

async def test_execute_single_tool():
    """测试执行单个工具"""
    session_id = "test-dispatch-003"
    agent = DispatcherAgent(session_id)
    
    result = await agent.execute_single_tool(
        "getPOI",
        {
            "x_position": 116.3974,
            "y_position": 39.9093,
            "afdd": "北京市朝阳区测试地址"
        }
    )
    
    assert result.tool_name == "getPOI"
    assert result.execution_time >= 0
    
    print(f"✅ 测试通过：单个工具执行，执行时间：{result.execution_time:.3f}s")

async def test_execute_plan():
    """测试执行完整计划"""
    session_id = "test-dispatch-004"
    agent = DispatcherAgent(session_id)
    await agent.initialize()
    
    # 创建测试计划
    steps = [
        {
            "description": "打开周边监控",
            "tool_name": "getPOI",
            "parameters": {
                "x_position": 116.3974,
                "y_position": 39.9093,
                "afdd": "北京市朝阳区测试地址"
            }
        },
        {
            "description": "查看值班人员",
            "tool_name": "showQw",
            "parameters": {"gxdwdm": "110105"}
        },
        {
            "description": "拨打值班电话",
            "tool_name": "callPhone",
            "parameters": {"phone": "13800138000"}
        }
    ]
    
    agent.create_plan(steps)
    results = await agent.execute_plan()
    
    # 验证执行结果，可能成功或失败（模拟随机）
    assert len(results) >= 1  # 至少执行了一个步骤
    assert agent.status in ["completed", "failed"]
    
    # 验证步骤状态
    for step in agent.execution_steps:
        assert step.status in ["success", "failed", "pending"]
        if step.status != "pending":
            assert step.result is not None
    
    print(f"✅ 测试通过：完整计划执行，状态：{agent.status}，完成步骤：{len(results)}")

async def test_get_plan_status():
    """测试获取计划状态"""
    session_id = "test-dispatch-005"
    agent = DispatcherAgent(session_id)
    await agent.initialize()
    
    # 创建计划
    steps = [
        {
            "description": "测试步骤1",
            "tool_name": "getPOI",
            "parameters": {"x_position": 116.3974, "y_position": 39.9093, "afdd": "测试"}
        }
    ]
    
    agent.create_plan(steps)
    status = agent.get_plan_status()
    
    assert status["session_id"] == session_id
    assert status["total_steps"] == 1
    assert status["completed_steps"] == 0
    assert status["status"] == "ready"
    assert len(status["steps"]) == 1
    
    print("✅ 测试通过：计划状态获取")

async def test_session_isolation():
    """测试会话隔离"""
    session1 = "test-dispatch-006"
    session2 = "test-dispatch-007"
    
    agent1 = DispatcherAgent(session1)
    agent2 = DispatcherAgent(session2)
    
    await agent1.initialize()
    await agent2.initialize()
    
    # 创建不同计划
    steps1 = [{"description": "会话1", "tool_name": "getPOI", "parameters": {"x": 1, "y": 1, "afdd": "a"}}]
    steps2 = [{"description": "会话2", "tool_name": "showQw", "parameters": {"gxdwdm": "110"}}]
    
    agent1.create_plan(steps1)
    agent2.create_plan(steps2)
    
    # 验证隔离
    assert agent1.session_id != agent2.session_id
    assert agent1.execution_steps[0].tool_name == "getPOI"
    assert agent2.execution_steps[0].tool_name == "showQw"
    
    print("✅ 测试通过：会话隔离")

async def main():
    """运行所有测试"""
    print("🧪 开始DispatcherAgent测试...")
    
    try:
        await test_dispatcher_initialization()
        await test_create_plan()
        await test_execute_single_tool()
        await test_execute_plan()
        await test_get_plan_status()
        await test_session_isolation()
        
        print("\n🎉 所有DispatcherAgent测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())