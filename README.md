# AI+ Red and Blue Platform

## Three-tier Security Operations Platform

This project implements a three-tier architecture for a comprehensive security operations platform with AI-powered capabilities.

## Architecture Overview

```
ai-red-blue-platform/
├── apps/                      # 应用层 - 独立应用
│   ├── dashboard/            # Web仪表盘 (FastAPI)
│   ├── cli/                   # 命令行工具
│   ├── secbot/               # SecBot-AI应用
│   └── range/                 # 漏洞靶场
│
├── packages/                  # 服务层 - 业务逻辑包
│   ├── red-team/             # 红队服务
│   ├── blue-team/            # 蓝队服务
│   ├── orchestration/         # 编排服务
│   └── knowledge/            # 知识库服务
│
├── libs/                      # 核心层 - 共享库
│   ├── core/                 # 核心分析库
│   ├── ai/                   # AI核心库
│   ├── security/             # 安全工具库
│   └── common/               # 公共组件
│
└── external-tools/           # 外部工具 (Monorepo)
```

## Directory Structure

### Core Layer (libs/)
- **common/** - 公共组件 (配置、日志、异常、工具函数)
- **core/** - 核心分析库 (告警、攻击、检测)
- **ai/** - AI核心库 (LLM提供商适配、模型管理)
- **security/** - 安全工具库 (扫描器、分析器)

### Service Layer (packages/)
- **red-team/** - 红队服务 (渗透测试、侦察、武器化)
- **blue-team/** - 蓝队服务 (检测、响应、威胁情报)
- **orchestration/** - 编排服务 (工作流、调度、预案)
- **knowledge/** - 知识库服务 (文档、搜索、CVE)

### Application Layer (apps/)
- **dashboard/** - Web仪表盘
- **cli/** - 命令行工具
- **secbot/** - SecBot-AI安全助手
- **range/** - 漏洞靶场

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-red-blue-platform

# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run the application
poetry run python apps/dashboard/main.py
```

## Usage

### Dashboard
```bash
poetry run python apps/dashboard/main.py
# Access at http://localhost:8000
```

### CLI
```bash
poetry run ai-rb-cli --help
poetry run ai-rb-cli status
poetry run ai-rb-cli scan --type vulnerability target.com
```

### SecBot
```bash
poetry run secbot
```

## Development

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run ruff check .
```

## License

MIT License
