# Market Programmer Agent - Autonomous AI System for Continuous Improvement

## 🎯 Repository Responsibility

The **Market Programmer Agent** is the brain of our autonomous trading system. This LangChain-powered FastAPI service monitors the market-predictor, analyzes its performance, detects issues, and autonomously implements improvements through code generation, testing, and deployment via GitHub PRs.

### Core Responsibilities:
- **Intelligent Monitoring**: Continuously monitor market-predictor performance and health
- **Issue Detection**: Analyze metrics and logs to identify problems and optimization opportunities
- **Autonomous Diagnosis**: Use LLM-powered analysis to understand root causes
- **Code Generation**: Create code fixes and improvements using LangChain
- **Local Testing**: Validate fixes in sandbox environments before deployment
- **GitHub Integration**: Create, manage, and merge pull requests autonomously
- **Self-Correction**: Learn from deployment outcomes and adjust strategies

### Event-Driven Architecture (Professional Implementation):
```
Market Predictor → Prometheus → Alert Rules → Alertmanager
     /metrics        ↓              ↓              ↓
                  Monitor      Evaluate      Send Webhooks
                              Conditions          ↓
Agent Webhooks ← HTTP POST ← Alert Manager ← Real Issues
     ↓                                            ↓
AI Analysis → Intelligent Response → Autonomous Actions
     ↓                    ↓                      ↓
Root Cause Analysis → Code Generation → Self-Correction Loop
```

The Agent operates as the **autonomous improvement system** - it's the orchestrator that ensures the market-predictor continuously evolves and improves without human intervention.

---

## 🚀 Quick Start

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd market-programmer-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys (OpenAI, GitHub, etc.)

# Run development server
python -m uvicorn src.agent.main:app --reload --host 0.0.0.0 --port 8001
```

### Docker Setup

```bash
# Build and run with Docker Compose
cd docker
docker-compose up --build

# Or build manually
docker build -f docker/Dockerfile -t market-programmer-agent .
docker run -p 8001:8001 --env-file .env market-programmer-agent
```

### Configuration

Create a `.env` file with the following required settings:

```bash
# LLM Configuration (Required for AI analysis)
OPENAI_API_KEY=your_openai_api_key_here

# Target Service
MARKET_PREDICTOR_URL=http://localhost:8000

# Optional: GitHub Integration
GITHUB_TOKEN=your_github_token_here
GITHUB_REPOSITORY=your_username/market-predictor

# Agent Behavior
SAFETY_MODE=true  # Set to false for autonomous operation
MONITORING_INTERVAL=30
```

### API Endpoints

Once running, the agent provides:

- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **Detailed Status**: http://localhost:8001/status
- **Monitoring Status**: http://localhost:8001/monitoring/status
- **⚡ Alert Webhooks**: http://localhost:8001/webhook/alerts (NEW!)
- **Control Panel**: http://localhost:8001/control/*

---

## 📁 Project Structure

```
market-programmer-agent/
├── src/
│   └── agent/
│       ├── __init__.py
│       ├── main.py                  # FastAPI app entry point
│       ├── core/
│       │   └── monitoring.py        # Monitoring orchestration
│       ├── agents/
│       │   └── analyzer.py          # LangChain analysis agent
│       ├── services/
│       │   └── predictor_client.py  # Market predictor HTTP client
│       ├── models/
│       │   └── health.py           # Health and status models
│       └── config/
│           └── settings.py         # Configuration management
├── tests/                          # Test suite
├── docker/
│   ├── Dockerfile                 # Production container
│   └── docker-compose.yml         # Development environment
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── .env.example                  # Environment template
└── memory-bank/                  # Project documentation
```

---

## 🤖 Agent Capabilities

### Current Features (Phase 1.2 Complete ✅) EVENT-DRIVEN ARCHITECTURE

#### ✅ Professional Event-Driven Monitoring ⚡ NEW!
- **Alertmanager Webhooks**: Receives real alerts from Prometheus/Alertmanager
- **Event-Driven Analysis**: AI triggered by actual infrastructure issues, not polling
- **Alert Processing**: Complete webhook models for Alertmanager payloads
- **Intelligent Response**: AI analyzes rich alert context to determine actions
- **Industry Standard**: How Netflix, Google, etc. actually monitor systems

#### ✅ Basic Monitoring & Communication (Enhanced)
- **Service Health Monitoring**: Professional monitoring via Prometheus metrics
- **HTTP Client**: Robust client for communicating with Market Predictor APIs
- **Connectivity Checks**: Automatic detection via real alerts
- **Response Time Tracking**: Prometheus-based performance monitoring

#### ✅ LangChain AI Analysis (Enhanced)
- **Alert-Driven Analysis**: LLM-powered analysis triggered by real alerts
- **Rich Context Processing**: AI receives alert metadata, severity, descriptions
- **Root Cause Analysis**: AI-driven investigation with alert context
- **Confidence Scoring**: Reliability assessment for autonomous actions
- **Fallback Analysis**: Rule-based analysis when LLM is unavailable

#### ✅ Agent Orchestration (Event-Driven)
- **Alert-Driven Mode**: Agent waits for real alerts instead of continuous polling
- **Action Tracking**: Complete audit trail of agent activities
- **Safety Controls**: Built-in safety mode for human oversight
- **Status Reporting**: Comprehensive status and health reporting

#### ✅ FastAPI Web Interface (Enhanced)
- **RESTful APIs**: Full REST API for agent control and monitoring
- **Webhook Endpoints**: `/webhook/alerts` for Alertmanager integration
- **Status Dashboard**: Real-time agent and target service status
- **Health Endpoints**: Integration-ready health checks

### 🔜 Next Phase Features (Phase 1.3)

- **Action Execution**: Automated service restart and recovery mechanisms
- **Enhanced Metrics Analysis**: Direct Prometheus metrics querying
- **Learning System**: Track action effectiveness and improve responses
- **Escalation Logic**: Smart escalation for complex issues

---

## 🎮 Agent Control

### Manual Operation (Safety Mode)

When `SAFETY_MODE=true`, the agent requires manual triggers:

```bash
# Start monitoring
curl -X POST http://localhost:8001/control/start-monitoring

# Trigger single monitoring cycle
curl -X POST http://localhost:8001/monitoring/cycle

# Stop monitoring
curl -X POST http://localhost:8001/control/stop-monitoring

# Check monitoring status
curl http://localhost:8001/monitoring/status
```

### Event-Driven Operation ⚡ NEW ARCHITECTURE!

The agent now operates using professional event-driven architecture:

- **Alert Reception**: Receives webhooks from Alertmanager when real issues occur
- **Intelligent Analysis**: AI analyzes alert context (severity, description, labels)
- **Action Execution**: Autonomous response to actual infrastructure problems
- **No Polling**: No wasteful continuous checking - responds only to real alerts
- **Professional Standard**: Industry-standard approach used by major tech companies

### Autonomous Operation

When `SAFETY_MODE=false`, the agent operates autonomously:

- **Event-Driven**: Responds to real alerts from monitoring infrastructure
- **Issue Detection**: AI-powered analysis of alert context and metadata
- **Action Execution**: Autonomous response to detected issues
- **Self-Correction**: Learning from outcomes to improve future responses

---

## 🧪 Testing

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src/agent --cov-report=html

# Run linting
flake8 src/ tests/
black src/ tests/
mypy src/
```

---

## 📊 Current Status: Phase 1.1 Complete ✅

### ✅ Completed Features:
- **Agent Infrastructure**: Complete LangChain-powered agent framework
- **Market Predictor Integration**: HTTP client with health monitoring
- **AI Analysis Engine**: GPT-4 powered intelligent issue analysis
- **Monitoring Orchestration**: Configurable monitoring loops with action tracking
- **FastAPI Interface**: Full REST API with manual controls
- **Safety Controls**: Built-in safety mode for controlled operation

### 🔄 Next Steps (Phase 1.2):
- Implement Prometheus client for metrics analysis
- Add Alertmanager webhook integration
- Create basic restart and recovery actions
- Enhance analysis with multi-source data correlation

---

## 🚦 Integration Points

### Market Predictor Integration
- **Health Monitoring**: Continuous monitoring of `/health` and `/status` endpoints
- **Response Time Tracking**: Monitoring API response times and availability
- **Issue Detection**: AI-powered analysis of service problems
- **Recovery Actions**: Automated response to detected issues

### Future Integrations (Later Phases)
- **Prometheus**: Direct metrics querying and alerting
- **Loki**: Log analysis and correlation
- **GitHub**: Automated PR creation and management
- **CI/CD**: Integration with deployment pipelines

---

## ⚙️ Configuration

The agent uses Pydantic Settings for configuration management:

```python
# Core settings
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true

# API configuration  
API_HOST=0.0.0.0
API_PORT=8001

# LLM configuration (required for AI features)
OPENAI_API_KEY=your_key_here
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1

# Target service
MARKET_PREDICTOR_URL=http://localhost:8000

# Agent behavior
MONITORING_INTERVAL=30
SAFETY_MODE=true
LEARNING_ENABLED=true
```

---

## 📈 Development Roadmap

### Milestone 1: Foundation (Current) ✅
- **Phase 1.1**: ✅ Agent Infrastructure & Basic Communication
- **Phase 1.2**: 🔄 Prometheus Integration & Alert Webhooks
- **Phase 1.3**: ⏳ Enhanced Analysis & Basic Actions
- **Phase 1.4**: ⏳ Testing & Validation Framework

### Future Milestones
- **Milestone 2**: Alert System Integration (Prometheus/Loki)
- **Milestone 3**: Intelligence Layer (Advanced LangChain integration)
- **Milestone 4**: Code Generation & GitHub Integration
- **Milestone 5**: Advanced Feedback Loop & Self-Correction
- **Milestone 6**: Production Hardening & Enterprise Features

---

## 🛡️ Safety & Security

### Built-in Safety Controls
- **Safety Mode**: Human approval required for all actions
- **Action Validation**: All actions logged and validated
- **Circuit Breaker**: Protection against repeated failures
- **Audit Trail**: Complete logging of all agent activities

### Security Features
- **API Key Management**: Secure handling of external API keys
- **Input Validation**: Comprehensive validation of all inputs
- **Error Handling**: Graceful handling of failures and exceptions
- **Rate Limiting**: Protection against API abuse

---

## 🤝 Contributing

This agent represents cutting-edge autonomous software development:

1. **Fork** the repository
2. **Create** a feature branch for agent improvements
3. **Implement** changes with comprehensive testing
4. **Document** any new autonomous capabilities
5. **Submit** PR with detailed impact analysis

### Development Guidelines
- Maintain **high test coverage** for all autonomous operations
- Include **safety checks** for all automated actions
- Add **comprehensive logging** for audit trails
- Follow **security best practices** for API integrations
- Document **failure modes** and recovery procedures

---

## 📝 License

MIT License - This project is part of the Autonomous Trading Builder system.

---

*🤖 This agent represents the cutting edge of autonomous software development - a system that can monitor, diagnose, fix, and improve itself with minimal human intervention. It's the beginning of truly self-evolving software systems.*