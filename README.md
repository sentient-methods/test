# MakeItHappen

**The CEO's engineering org in a box.**

> Motto: *Just Do It* | Slogan: *Make It Happen* | Tagline: *As You Wish*

MakeItHappen is a Jarvis-like AI assistant for vibe coders. You speak in outcomes and vision. The system translates your intent into executed software through a multi-agent organization — Product, Design, Engineering, QA, DevOps — all spun up on demand.

You are the CEO. The system is the rest of the company.

## How It Works

```
You (CEO)
  "I need a landing page for my SaaS"
        |
  Chief of Staff (Intent Translator)
    - Classifies intent (build/fix/deploy/explain/plan/change)
    - Translates to actionable specs
    - Asks clarifying questions if needed
        |
  Orchestrator
    - Routes work to the right teams
    - Manages dependencies between agents
    - Streams progress back to you in real time
        |
  +-----------+-----------+---------+--------+--------+
  | Product   | Designer  |Engineer |  QA    | DevOps |
  | Owner     |           |         |        |        |
  +-----------+-----------+---------+--------+--------+
  | Specs &   | UI/UX     | Code    | Tests  | Build  |
  | stories   | layout    | (SDK)   | verify | deploy |
  +-----------+-----------+---------+--------+--------+
        |
  CEO Filter (Progressive Disclosure)
    - Executive summary by default
    - "Tell me more" for details
    - "Show me the code" for full technical output
        |
  Preview Pane
    - Live preview of what was built
    - Auto-detects project type (Node, Python, static)
```

## Architecture

- **Backend**: Python / FastAPI / WebSocket / SQLite
- **Frontend**: React / TypeScript / Vite
- **AI Engine**: Claude Agent SDK for tool-capable agents (file editing, bash, search)
- **AI API**: Anthropic Claude API for planning agents (classification, translation, filtering)
- **Models**: Haiku (fast classification) / Sonnet (translation + filtering) / Opus (engineering)
- **Persistence**: SQLite for session history

## Project Structure

```
backend/
  main.py                    # FastAPI entrypoint with lifespan management
  config.py                  # Settings, model assignments, env loading
  chat/
    models.py                # CEO/System message protocol (Pydantic)
    session.py               # Session management with SQLite persistence
    router.py                # WebSocket endpoint + REST session APIs
  intent/
    prompts.py               # System prompts for the Chief of Staff
    translator.py            # CEO-speak -> ActionableIntent pipeline
  agents/
    registry.py              # Org chart: 5 agent definitions with personas
    orchestrator.py           # Pipeline execution, SDK + API agent runners
  middleware/
    ceo_filter.py            # Translates technical output -> executive language
    progressive_disclosure.py # Detects detail level from CEO language
  tools/
    project_state.py         # Project structure scanner and stack detector
    preview.py               # Dev server management (Node, Python, static)
    feedback.py              # Agent -> CEO feedback queue

frontend/
  src/
    App.tsx                  # Root component
    main.tsx                 # React entry point
    components/
      Chat.tsx               # Main chat interface with preview pane
      MessageBubble.tsx      # Message rendering with type-specific styling
      AgentStatus.tsx        # Agent status badges
      AgentPipeline.tsx      # Visual org chart of active agents
    hooks/
      useWebSocket.ts        # WebSocket connection management
    types/
      messages.ts            # TypeScript message types

tests/                       # Unit tests for all backend modules
Makefile                     # Dev scripts (install, dev, test, clean)
```

## Quick Start

```bash
# 1. Install everything
make setup

# 2. Configure your API key
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY=sk-ant-...

# 3. Start the backend (terminal 1)
make backend

# 4. Start the frontend (terminal 2)
make frontend

# 5. Open http://localhost:3000 and start talking
```

### Manual Setup

```bash
# Backend
pip install -e ".[dev]"
python -m backend.main

# Frontend
cd frontend && npm install && npm run dev
```

## Agent Architecture

### The Org Chart

| Agent | Role | Model | Tools | Purpose |
|-------|------|-------|-------|---------|
| **Chief of Staff** | Intent Translation | Haiku + Sonnet | None (API only) | Classifies & translates CEO directives |
| **Product Owner** | Specs & Stories | Sonnet | Read, Glob, Grep | Breaks down intent into user stories |
| **Designer** | UI/UX | Sonnet | Read, Glob, Grep | Component specs, layouts, design tokens |
| **Engineer** | Code | Opus | Read, Write, Edit, Bash, Glob, Grep | Writes actual code via Agent SDK |
| **QA** | Validation | Sonnet | Read, Write, Edit, Bash, Glob, Grep | Tests, validates, reports issues |
| **DevOps** | Infrastructure | Sonnet | Read, Write, Edit, Bash, Glob, Grep | Build systems, deployment config |

### Execution Pipelines

Different intents trigger different agent sequences:

| Intent | Pipeline |
|--------|----------|
| `build` | Product Owner -> Designer -> Engineer -> QA |
| `fix` | Engineer -> QA |
| `change` | Engineer -> QA |
| `deploy` | DevOps |
| `explain` | Product Owner |
| `plan` | Product Owner -> Designer |

### SDK vs API Agents

- **SDK Agents** (Engineer, QA, DevOps): Use the Claude Agent SDK with `query()`. These agents can actually edit files, run commands, and modify your project.
- **API Agents** (Product Owner, Designer): Use the Anthropic API directly. Faster and cheaper — they only produce specs, not code.

## Progressive Disclosure

MakeItHappen speaks to you at the level you want:

| Level | Triggered by | Example output |
|-------|-------------|----------------|
| **Executive** (default) | — | "Your landing page is ready. Three sections with a signup form." |
| **Manager** | "tell me more", "elaborate" | "Built with React + Tailwind. Hero, features grid, CTA. Mobile responsive." |
| **Technical** | "show me the code", "debug" | Full agent output with code changes and technical decisions |

Say "keep it simple" or "just the highlights" to go back to executive level.

## Preview System

MakeItHappen auto-detects your project type and launches a dev server:

- **Node.js** (package.json with `dev` script): `npm run dev`
- **Python** (app.py / main.py): uvicorn
- **Django** (manage.py): `runserver`
- **Static HTML** (index.html): Python HTTP server

Preview appears in a split pane next to the chat.

## Session Persistence

Sessions are stored in SQLite at `~/.makeitahppen/sessions.db`. You can:

- Resume previous conversations
- List all sessions: `GET /api/sessions`
- Get a specific session: `GET /api/sessions/{id}`

## API Endpoints

| Endpoint | Type | Description |
|----------|------|-------------|
| `/api/chat` | WebSocket | Main chat connection |
| `/api/sessions` | GET | List all sessions |
| `/api/sessions/{id}` | GET | Get session details |
| `/api/preview/{session_id}` | GET | Start/get preview server |
| `/health` | GET | Health check |

## Testing

```bash
make test
# or
python -m pytest tests/ -v
```

## Configuration

All settings can be overridden via environment variables or `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `MODEL_ORCHESTRATOR` | `claude-opus-4-6` | Model for orchestration |
| `MODEL_ENGINEER` | `claude-opus-4-6` | Model for code generation |
| `MODEL_CLASSIFIER` | `claude-haiku-4-5` | Model for intent classification |
| `MODEL_TRANSLATOR` | `claude-sonnet-4-6` | Model for spec translation |
| `MODEL_CEO_FILTER` | `claude-sonnet-4-6` | Model for output filtering |
| `PORT` | `8000` | Backend server port |

## Roadmap

- [x] Multi-agent orchestration with specialized system prompts
- [x] Claude Agent SDK integration for real file editing and bash execution
- [x] Intent classification and translation pipeline
- [x] Progressive disclosure (executive/manager/technical)
- [x] Session persistence (SQLite)
- [x] Live preview system with auto-detection
- [x] Agent feedback queue for CEO input
- [x] Real-time agent pipeline visualization
- [ ] Voice input ("Hey Jarvis...")
- [ ] Custom agent creation (bring your own team members)
- [ ] Project templates (SaaS, landing page, API, mobile)
- [ ] Deploy pipeline integration (Vercel, Netlify, Railway)
- [ ] Multi-project workspace management
- [ ] Undo/rollback ("go back to how it was")
