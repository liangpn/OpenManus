# CLAUDE.md

这个文件为 Claude Code（claude.ai/code）提供在 OpenManus 代码库中工作的指导。

## 快速开始命令

### 安装与设置
```bash
# 方法1：使用 conda
conda create -n open_manus python=3.12
conda activate open_manus
pip install -r requirements.txt

# 方法2：使用 uv（推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.12
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# 可选：浏览器自动化
playwright install
```

### 配置
```bash
cp config/config.example.toml config/config.toml
# 编辑 config/config.toml 添加API密钥
```

### 运行应用
```bash
# 主 OpenManus 代理
python main.py

# 带提示运行
python main.py --prompt "你的任务描述"

# MCP版本
python run_mcp.py

# 多代理流程版本
python run_flow.py

# 运行特定测试
python -m pytest tests/sandbox/test_sandbox.py -v
```

### 开发命令
```bash
# 代码格式化
black .
isort .

# 代码检查和自动修复
pre-commit run --all-files

# 运行所有测试
python -m pytest tests/

# 开发模式安装
pip install -e .
```

## 架构概览

### 核心组件

**代理系统** (`app/agent/`)
- `BaseAgent`: 所有代理的抽象基类，包含状态管理和执行循环
- `Manus`: 主通用代理，支持MCP和浏览器自动化
- `ToolCallAgent`: 函数调用代理的基类
- 专业代理：`DataAnalysis`（数据分析）、`BrowserAgent`（浏览器）、`SWEAgent`（软件工程）、`ReactAgent`（React）

**工具系统** (`app/tool/`)
- `BaseTool`: 所有工具的抽象基类，提供标准化接口
- 内置工具：`PythonExecute`（Python执行）、`BrowserUseTool`（浏览器操作）、`StrReplaceEditor`（文件编辑）、`WebSearch`（网络搜索）、`AskHuman`（询问用户）
- MCP支持：`MCPClients`、`MCPClientTool` 用于远程工具集成
- 工具集合：`ToolCollection` 管理可用工具

**流程系统** (`app/flow/`)
- `BaseFlow`: 多代理执行流程的抽象基类
- `PlanningFlow`: 任务分解和代理协调
- `FlowFactory`: 创建不同代理组合的流程

**配置系统** (`app/config.py`)
- 单例配置系统，支持TOML配置
- LLM、浏览器、搜索、沙箱和MCP设置
- 环境感知的配置加载

**沙箱系统** (`app/sandbox/`)
- 基于Docker的代码执行环境
- `SandboxManager`、`DockerTerminal`、`SandboxClient` 提供隔离执行

### 关键设计模式

**状态管理**：代理使用 `AgentState` 枚举和上下文管理器进行安全的状态转换
**内存管理**：`Memory` 类使用 `Message` 对象存储对话历史
**工具集成**：工具实现 `execute()` 方法并为LLM提供JSON schema
**MCP支持**：通过SSE/stdio集成Model Context Protocol外部工具
**多代理**：流程系统协调多个专业代理

### 配置结构

```toml
[llm]
model = "claude-3-7-sonnet-20250219"
base_url = "https://api.anthropic.com/v1/"
api_key = "YOUR_API_KEY"
max_tokens = 8192
temperature = 0.0

[browser]
headless = false
disable_security = true

[search]
engine = "Google"
fallback_engines = ["DuckDuckGo", "Baidu", "Bing"]

[mcp]
server_reference = "app.mcp.server"
```

### 开发工作流

1. **代码风格**：使用 Black (23.1.0)、isort (5.12.0)、autoflake (2.0.1) 通过 pre-commit
2. **测试**：pytest 支持 asyncio 的异步测试
3. **CI/CD**：GitHub Actions 进行 pre-commit 检查和包构建
4. **打包**：基于 setuptools 的控制台脚本入口点

### 测试结构

测试组织在 `tests/` 目录：
- `tests/sandbox/`：沙箱功能测试
- `app/tool/chart_visualization/test/`：图表可视化工具测试

使用 `pytest -v` 查看详细测试输出，`pytest tests/sandbox/test_sandbox.py` 运行特定模块。
