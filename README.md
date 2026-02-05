# AI+ Red and Blue Platform

## Three-tier Security Operations Platform

A comprehensive security operations platform with AI-powered capabilities, featuring red team/blue team tools, threat detection, and automated response workflows.

## Architecture

```
ai-red-blue-platform/
├── apps/                      # Application Layer
│   ├── dashboard/            # Web Dashboard (FastAPI)
│   ├── cli/                  # Command Line Interface
│   ├── secbot/              # SecBot-AI Assistant
│   └── range/               # Vulnerability Range
│
├── packages/                 # Service Layer
│   ├── red-team/            # Red Team Services
│   ├── blue-team/           # Blue Team Services
│   ├── orchestration/       # Orchestration Services
│   └── knowledge/            # Knowledge Base Services
│
├── libs/                     # Core Layer
│   ├── core/                # Core Analysis Library
│   ├── ai/                 # AI Core Library
│   ├── security/            # Security Tools Library
│   └── common/             # Common Components
│
└── external-tools/          # External Tools (Monorepo)
```

## Quick Start

```bash
# Clone and enter directory
git clone https://github.com/skydzx/AI-Red-Blue-Platform.git
cd AI-Red-Blue-Platform

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run Dashboard
python apps/dashboard/main.py
# Access at http://localhost:8000/docs for API docs
```

## Features

### Dashboard API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root info |
| `/health` | GET | Health check |
| `/api/v1/alerts` | GET | List alerts (supports `?severity=high&limit=100`) |
| `/api/v1/alerts/{id}` | GET | Get alert details |
| `/api/v1/alerts` | POST | Create alert |
| `/api/v1/alerts/{id}` | PATCH | Update alert |
| `/api/v1/detections` | GET | List detection rules |
| `/api/v1/statistics` | GET | Platform statistics |
| `/api/v1/chat` | POST | AI chat endpoint |
| `/api/v1/utils/hash` | POST | Calculate hash |
| `/api/v1/utils/encode` | POST | Encode data (base64/hex/url) |
| `/api/v1/utils/decode` | POST | Decode data |
| `/api/v1/demo/seed` | POST | Seed demo data |

### CLI Commands

```bash
# Status
python apps/cli/main.py status
python apps/cli/main.py version

# Alerts
python apps/cli/main.py list-alerts
python apps/cli/main.py show-alert <alert_id>
python apps/cli/main.py create-alert "Title" "Description" --severity high
python apps/cli/main.py update-alert <alert_id> --status investigating

# Security Utils
python apps/cli/main.py hash "content" --algorithm sha256
python apps/cli/main.py encode "content" --encoding base64
python apps/cli/main.py decode "encoded_content"

# Demo
python apps/cli/main.py demo

# Chat
python apps/cli/main.py chat "Analyze this threat..." --provider openai
```

## Development

```bash
# Install all libs
cd libs/common && pip install -e .
cd ../security && pip install -e .
cd ../core && pip install -e .
cd ../ai && pip install -e .

# Run tests
pytest

# Lint
black .
ruff check .
mypy .

# Docker
docker-compose up -d
```

## Environment Variables

```env
# Application
ENV=development
LOG_LEVEL=INFO

# AI Providers
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/airbp
REDIS_URL=redis://localhost:6379
```

## License

MIT License
