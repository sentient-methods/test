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
    - Classifies intent (build/fix/deploy/explain/plan)
    - Translates to actionable specs
    - Asks clarifying questions if needed
        |
  Orchestrator
    - Routes work to the right teams
    - Manages dependencies between agents
    - Streams progress back to you
        |
  +-----------+-----------+---------+--------+
  | Product   | Designer  |Engineer |  QA    |
  | Owner     |           |         |        |
  +-----------+-----------+---------+--------+
        |
  CEO Filter (Progressive Disclosure)
    - Executive summary by default
    - "Tell me more" for details
    - "Show me the code" for full technical output
```

## Architecture

- **Backend**: Python / FastAPI / WebSocket
- **Frontend**: React / TypeScript / Vite
- **AI**: Anthropic Claude API (Haiku for classification, Sonnet for translation, Opus for engineering)
- **Agent Orchestration**: Multi-agent pipeline with specialized system prompts per role

## Project Structure

```
backend/
  main.py              # FastAPI entrypoint
  config.py            # Settings and model assignments
  chat/                # WebSocket chat layer, session management
  intent/              # CEO-speak -> actionable specs translation
  agents/              # Agent registry, orchestrator, org chart
  middleware/           # CEO filter, progressive disclosure
  tools/               # Project state tracking
frontend/
  src/
    components/        # Chat UI, message bubbles, agent status
    hooks/             # WebSocket connection management
    types/             # Shared TypeScript types
tests/                 # Unit tests
```

## Setup

### Backend

```bash
# Install dependencies
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your Anthropic API key

# Run
python -m backend.main
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies API requests to the backend at `localhost:8000`.

## Progressive Disclosure

By default, MakeItHappen speaks to you like a CEO:

- **Executive** (default): "Your landing page is ready. Three sections with a signup form. Ready for review."
- **Manager** ("tell me more"): "Built with React + Tailwind. Hero section, features grid, and CTA. Mobile responsive. Used your existing color tokens."
- **Technical** ("show me the code"): Full agent output with code diffs and technical details.

## Next Steps

- [ ] Claude Agent SDK integration for real file editing and bash execution
- [ ] Live preview pane (iframe-based for web projects)
- [ ] Session persistence (SQLite)
- [ ] Voice input ("Hey Jarvis...")
- [ ] Deploy pipeline integration
- [ ] Custom agent creation (bring your own team members)
