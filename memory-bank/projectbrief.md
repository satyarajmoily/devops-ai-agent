# Project Brief - Market Programmer Agent

## Project Overview

**Market Programmer Agent** is the autonomous brain of our trading system. This LangChain-powered FastAPI service monitors the market-predictor, analyzes its performance, detects issues, and autonomously implements improvements through code generation, testing, and deployment via GitHub PRs.

## Core Purpose

- **Primary Function**: Autonomous monitoring and improvement of the market-predictor service
- **System Role**: The orchestrator that ensures continuous evolution and optimization
- **Business Value**: Enable self-improving trading infrastructure without human intervention

## Key Responsibilities

1. **Intelligent Monitoring**: Continuously monitor market-predictor performance and health
2. **Issue Detection**: Analyze metrics and logs to identify problems and optimization opportunities
3. **Autonomous Diagnosis**: Use LLM-powered analysis to understand root causes
4. **Code Generation**: Create code fixes and improvements using LangChain
5. **Local Testing**: Validate fixes in sandbox environments before deployment
6. **GitHub Integration**: Create, manage, and merge pull requests autonomously
7. **Self-Correction**: Learn from deployment outcomes and adjust strategies

## System Architecture Context

```
[Market Predictor] → [Prometheus] → [Agent Monitoring]
        ↓              ↓                    ↓
   [Loki Logs] → [Agent Analysis] → [Issue Classification]
                       ↓                    ↓
              [LangChain LLM] → [Code Generation] → [Local Testing]
                       ↓                    ↓
              [GitHub PR] → [CI/CD] → [Deployment] → [Monitoring]
                                           ↓
                                  [Self-Correction Loop]
```

The Agent operates as the **autonomous improvement system** - it's the orchestrator that ensures the market-predictor continuously evolves and improves without human intervention.

## Milestone 1 Objectives

**Goal**: Establish the autonomous agent foundation with FastAPI service, basic monitoring, and communication with market-predictor

### Success Criteria:
- [ ] Working FastAPI application with agent infrastructure
- [ ] Basic monitoring and communication with market-predictor
- [ ] Health monitoring and status reporting capabilities
- [ ] Simple feedback loop for basic issue detection and response
- [ ] Docker containerization support
- [ ] Comprehensive testing suite

### Milestone 1 Phases:
1. **Phase 1.1**: Project Structure & Agent Framework Setup (2-3 days)
2. **Phase 1.2**: Basic Monitoring & Communication Setup (2-3 days)
3. **Phase 1.3**: Basic Feedback Loop Implementation (3-4 days)
4. **Phase 1.4**: Agent Infrastructure Testing (1-2 days)

## Technical Constraints

- **Language**: Python 3.9+
- **Framework**: FastAPI for agent service, LangChain for AI capabilities
- **Deployment**: Docker containers
- **Monitoring**: Must integrate with Prometheus and Loki
- **AI Integration**: LangChain for LLM interactions
- **GitHub Integration**: GitHub API for PR management
- **Testing**: Comprehensive testing including AI component mocking

## Success Metrics

- Successfully monitor market-predictor health status
- Detect basic issues (service down, high latency)
- Implement simple restart mechanisms
- Expose comprehensive agent health and status endpoints
- Full containerized deployment capability
- Test coverage >90% for non-AI components

## Integration Requirements

### With Market Predictor:
- HTTP communication for health checks and status monitoring
- Metrics scraping from Prometheus endpoints
- Log analysis from structured JSON logs
- Performance monitoring and trend analysis

### With External Systems:
- **Prometheus**: Metrics collection and alerting
- **Loki**: Log aggregation and analysis
- **GitHub**: PR creation and management
- **LangChain**: LLM integration for analysis and code generation

## Autonomous Capabilities (Future Milestones)

While Milestone 1 focuses on foundation and basic monitoring, the agent is designed to evolve into a fully autonomous system with:

- **Intelligent Analysis**: Deep understanding of system performance patterns
- **Predictive Issues**: Detecting problems before they impact users
- **Advanced Code Generation**: Creating complex fixes and optimizations
- **Learning & Adaptation**: Improving strategies based on past outcomes
- **Self-Optimization**: Optimizing its own performance and capabilities 