# Presenton DDD + MCP Redesign — Full Specification

**Date**: 2026-04-02
**Status**: Approved
**Approach**: DDD Monorepo + MCP Bus (Approach A)

---

## 1. Overview

Presenton is an open-source AI presentation generator. This spec covers a full architectural redesign from the current monolithic codebase to a clean DDD architecture with MCP-based inter-domain communication, plus significant new functionality.

### Goals

1. **Security fixes**: CORS, encrypted secrets, auth on static files, rate limiting
2. **DDD architecture**: 10 bounded contexts, hexagonal architecture per domain
3. **MCP dual-layer**: Internal MCP between domains + external MCP gateway
4. **Agent pipeline**: 13+ specialized agents with parallel subagent execution
5. **Ralph Loop**: Iterative quality improvement with auto-checks + human approval
6. **Style copying**: From PPTX/PDF, URL (vision), and preset library
7. **OAuth 2.0**: Authorization Code + PKCE for Anthropic and OpenAI (not API keys)
8. **Infographics**: SVG templates + D3.js + AI-generated visuals (hybrid)
9. **Web access**: Internet search, scraping, data extraction for content
10. **Export**: PDF + PPTX export as separate domain
11. **Docker deployment**: docker-compose with 10+ services
12. **Electron**: Standalone desktop with embedded domains
13. **SpecKit**: Spec-driven development workflow throughout

### Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLModel, Alembic, structlog
- **Frontend**: TypeScript, Next.js 14, Redux Toolkit, Tailwind CSS
- **Desktop**: Electron 36+
- **Infrastructure**: Docker, PostgreSQL 16, Redis 7 (Streams), nginx
- **AI**: Anthropic Claude, OpenAI, Google Gemini, Ollama (via OAuth or local)
- **MCP**: FastMCP for Python MCP servers
- **Tooling**: ruff, mypy, pre-commit, Vitest, Cypress, Prometheus, Sentry

---

## 2. Monorepo Structure

```
presenton/
├── domains/
│   ├── presentation/          # Bounded Context: Presentation
│   │   ├── domain/            # Entities, Value Objects, Aggregates
│   │   ├── application/       # Use Cases, Commands, Queries
│   │   ├── infrastructure/    # DB repos, external adapters
│   │   ├── api/               # FastAPI routes
│   │   ├── mcp/               # MCP server (tools, resources)
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   ├── style/
│   ├── content/
│   ├── rendering/
│   ├── media/
│   ├── agent/
│   ├── auth/
│   ├── identity/
│   ├── web_access/
│   └── export/
├── shared/                    # Shared Kernel
│   ├── domain/                # Base Entity, ValueObject, AggregateRoot
│   ├── events/                # Domain Events + Event Bus interface
│   ├── mcp/                   # MCP client/server base classes
│   └── infrastructure/        # Redis Streams adapter, logging, tracing
├── gateway/
│   ├── api_gateway/           # nginx + FastAPI reverse proxy
│   ├── mcp_gateway/           # External MCP server (aggregates all domains)
│   └── Dockerfile
├── frontend/                  # Next.js
│   └── Dockerfile
├── electron/                  # Standalone desktop app
│   ├── app/                   # Electron main process
│   └── embedded/              # Embedded Python runtime + all domains
├── docs/
│   └── superpowers/specs/
├── docker-compose.yml
├── docker-compose.dev.yml
└── speckit.config
```

### Per-Domain Internal Structure (Hexagonal / Ports & Adapters)

```
domain_name/
├── domain/
│   ├── entities.py            # Aggregate roots, entities
│   ├── value_objects.py       # Immutable value types
│   ├── events.py              # Domain events
│   ├── repositories.py        # Repository interfaces (ports)
│   └── services.py            # Domain services
├── application/
│   ├── commands.py            # Command handlers (write)
│   ├── queries.py             # Query handlers (read)
│   ├── dto.py                 # Data transfer objects
│   └── interfaces.py          # Application service interfaces
├── infrastructure/
│   ├── db/
│   │   ├── models.py          # SQLAlchemy/SQLModel models
│   │   ├── repositories.py    # Repository implementations
│   │   └── migrations/        # Alembic per-domain
│   ├── adapters/              # External service adapters
│   └── config.py              # Environment, settings
├── api/
│   ├── router.py              # FastAPI endpoints
│   ├── schemas.py             # Pydantic request/response
│   └── dependencies.py        # FastAPI DI
├── mcp/
│   ├── server.py              # MCP tool definitions
│   └── client.py              # MCP client for calling other domains
└── tests/
    ├── unit/
    ├── integration/
    └── conftest.py
```

---

## 3. Bounded Contexts

### 3.1 Presentation Domain (core)

**Responsibility**: Lifecycle of presentations — CRUD, slides, versioning, metadata.

**Aggregates**:
- `Presentation` (root) → `Slide[]` → `SlideElement[]`
- `Template`

**Domain Events**:
- `PresentationCreated`, `PresentationUpdated`, `SlideAdded`, `SlideReordered`, `PresentationFinalized`

**MCP Tools**:
- `presentation.create`, `presentation.get`, `presentation.update`, `presentation.list`
- `slide.add`, `slide.update`, `slide.remove`, `slide.reorder`
- `template.apply`, `template.list`

---

### 3.2 Style Domain

**Responsibility**: Parsing, storing, and applying visual styles. Three sources: PPTX/PDF file, URL (vision), presets.

**Aggregates**:
- `StyleProfile` → `ColorPalette`, `Typography`, `LayoutRules`, `Spacing`
- `StylePreset` (library of built-in and user-created presets)

**Domain Events**:
- `StyleExtracted`, `StyleApplied`, `PresetCreated`

**MCP Tools**:
- `style.extract_from_file` (PPTX/PDF → StyleProfile)
- `style.extract_from_url` (screenshot → vision model → StyleProfile)
- `style.apply` (StyleProfile → Presentation)
- `style.presets.list`, `style.presets.create`
- `style.validate` (check style conformance — used by Ralph Loop)

**Dependencies**: calls Rendering for visual conformance checks, Auth for vision model access.

#### Style Extraction Pipeline

**Source A — PPTX/PDF file**:
- python-pptx: extract slide masters, layouts, theme colors, accent colors, fonts, sizes, margins, backgrounds
- pdfplumber: extract fonts, colors from text runs, layout geometry
- Output: `StyleProfile`

**Source B — URL (Vision)**:
- WebAccess.screenshot(url) → multiple screenshots at different viewport sizes
- StyleParser Agent + Vision Model analyzes screenshots
- Extracts: dominant colors (hex), font families/sizes, spacing patterns, layout grid, design language
- Output: `StyleProfile`

**Source C — Presets**:
- Built-in presets: minimal-light, corporate-blue, creative-bold, dark-elegant, startup-gradient
- User can save any StyleProfile as a custom preset

#### StyleProfile → CSS/Tailwind

StyleProfile converts to:
- CSS custom properties (--color-primary, --font-heading, etc.)
- Tailwind theme config (colors, fontFamily, fontSize, spacing)
- Used by Rendering domain for HTML slide generation

---

### 3.3 Content Domain

**Responsibility**: Text content generation — outline, slide texts, speaker notes. System prompt management.

**Aggregates**:
- `ContentPlan` → `SlideContent[]`
- `SystemPrompt` (configurable prompts for different tasks)
- `PromptTemplate` (templates with variables)

**Domain Events**:
- `OutlineGenerated`, `SlideContentGenerated`, `ContentRevised`

**MCP Tools**:
- `content.generate_outline` (topic → presentation structure)
- `content.generate_slide` (outline item → slide text)
- `content.revise` (text + feedback → improved text)
- `content.prompts.list`, `content.prompts.update`, `content.prompts.create`

**Dependencies**: Auth for LLM access, WebAccess for web grounding.

---

### 3.4 Rendering Domain

**Responsibility**: HTML rendering of slides, previews, visual diff for Ralph Loop.

**Aggregates**:
- `RenderJob` → `RenderedSlide[]`
- `RenderConfig` (resolution, format, CSS)

**Domain Events**:
- `SlideRendered`, `PresentationRendered`

**MCP Tools**:
- `rendering.render_slide` (slide data + style → HTML)
- `rendering.render_preview` (thumbnail generation)
- `rendering.visual_diff` (two renders → difference percentage, for Ralph Loop)
- `rendering.batch_render` (all slides in parallel)

**Dependencies**: Style for CSS, Puppeteer/Chromium for HTML→image.

---

### 3.5 Media Domain

**Responsibility**: Image search, AI image generation, infographics.

**Aggregates**:
- `MediaAsset` → `ImageAsset | InfographicAsset | IconAsset`
- `InfographicTemplate` (SVG templates for charts, timelines, flowcharts)

**Infographic sub-modules**:
- `svg_generator` — D3.js/SVG for charts, diagrams
- `template_engine` — fill templates with data
- `ai_generator` — DALL-E/Gemini for custom visualizations

**Domain Events**:
- `ImageFound`, `ImageGenerated`, `InfographicCreated`

**MCP Tools**:
- `media.search_images` (query → results from Pexels/Pixabay/web)
- `media.generate_image` (prompt → AI image)
- `media.create_infographic` (data + type → SVG/HTML infographic)
- `media.infographic_templates.list`
- `media.icons.search`

**Dependencies**: WebAccess for search, Auth for AI providers.

---

### 3.6 Agent Domain (orchestrator)

**Responsibility**: Agent pipeline management, subagents, parallel execution, Ralph Loop.

**Aggregates**:
- `AgentPipeline` → `AgentStep[]`
- `Agent` → `AgentConfig` (model, system_prompt, tools[], temperature, max_tokens)
- `AgentRun` → `SubAgentRun[]` (execution tracking)
- `RalphLoop` → `Iteration[]` → `CheckResult[]`

**Specialized Agents (13)**:

| Agent | Task |
|---|---|
| `Orchestrator` | Routing, task decomposition, subagent launch |
| `ContentWriter` | Slide text generation |
| `OutlineArchitect` | Presentation structure creation |
| `StyleParser` | Style extraction from files/URLs |
| `PaletteDesigner` | Color palette generation |
| `FontSelector` | Font selection |
| `LayoutComposer` | Element composition on slides |
| `InfographicBuilder` | Infographic creation |
| `ImageCurator` | Image search and selection |
| `SlideRenderer` | HTML rendering of each slide |
| `QualityReviewer` | Quality checklist verification |
| `StyleEnforcer` | Style conformance verification |
| `WebResearcher` | Internet information search |

**Domain Events**:
- `PipelineStarted`, `PipelineCompleted`, `PipelineFailed`
- `AgentTaskAssigned`, `AgentTaskCompleted`
- `RalphLoopIterationCompleted`
- `HumanApprovalRequested`, `HumanApprovalReceived`

**MCP Tools**:
- `agent.run_pipeline` (topic + config → full presentation)
- `agent.configure` (agent config, prompts, parameters)
- `agent.ralph_loop.start`, `agent.ralph_loop.status`, `agent.ralph_loop.approve`
- `agent.list_agents`, `agent.update_agent`

#### Full Pipeline (7 Stages)

```
Stage 1: RESEARCH (parallel)
  WebResearcher → web.search(topic)
  StyleParser → style.extract_from_url(reference) or style.extract_from_file(upload)

Stage 2: PLANNING
  OutlineArchitect → content.generate_outline()
  PaletteDesigner → style.generate_palette()
  FontSelector → style.select_fonts()

Stage 3: CONTENT (parallel per slide)
  ContentWriter[0..N] → content.generate_slide(i)
  ImageCurator → media.search_images(queries)
  InfographicBuilder → media.create_infographic(data)

Stage 4: ASSEMBLY
  LayoutComposer → place text, images, infographics per slide, apply StyleProfile

Stage 5: RENDERING (parallel)
  SlideRenderer[0..N] → rendering.render_slide(i)

Stage 6: RALPH LOOP
  (see Ralph Loop section below)

Stage 7: EXPORT
  export.to_pdf() + export.to_pptx()
```

#### Ralph Loop — Detailed Algorithm

Hybrid cycle: automatic checks + final human confirmation.

**Checklist criteria (weighted)**:

| Criterion | Weight |
|---|---|
| color_consistency | 0.15 |
| font_hierarchy | 0.10 |
| text_readability | 0.15 |
| contrast_ratio | 0.10 |
| layout_alignment | 0.10 |
| image_quality | 0.10 |
| infographic_accuracy | 0.10 |
| content_grammar | 0.10 |
| content_tone | 0.05 |
| slide_overflow | 0.05 |

**Algorithm**:
1. Parallel launch: QualityReviewer + StyleEnforcer evaluate all slides
2. Aggregate checklist, compute weighted score
3. If score >= threshold (default 0.95) → request human approval via WebSocket
4. If human approves → exit loop, proceed to export
5. If human gives feedback → parse into targeted fix items
6. If score < threshold → automatically identify failed items
7. Parallel launch fixer agents (mapped by failed criterion):
   - color_consistency → PaletteDesigner
   - font_hierarchy → FontSelector
   - text_readability → ContentWriter
   - contrast_ratio → PaletteDesigner
   - layout_alignment → LayoutComposer
   - image_quality → ImageCurator
   - infographic_accuracy → InfographicBuilder
   - content_grammar → ContentWriter
   - content_tone → ContentWriter
   - slide_overflow → LayoutComposer
8. Re-render changed slides
9. Repeat (max iterations configurable, default 5)
10. If max iterations reached → force human review

#### Subagent Parallel Execution

- `SubAgentExecutor` with configurable `max_concurrent` (default 8)
- Uses `asyncio.Semaphore` for concurrency control
- Each subagent gets: own system prompt, access to specified MCP tools, presentation context

#### WebSocket Real-Time Progress

```
WS /api/v1/agents/pipeline/{run_id}/stream

Events:
  stage_started       — { stage, agents[] }
  agent_progress      — { agent, status }
  stage_completed     — { stage, duration_ms }
  ralph_loop_iteration — { iteration, score, failed[] }
  human_approval_needed — { score, checklist }
  pipeline_completed  — { presentation_id }
```

#### Agent Configuration (via UI/config)

Each agent is configurable:
- model (claude-sonnet-4-6, gpt-4o, gemini-2.0-flash, etc.)
- provider (anthropic, openai, google, ollama, custom)
- system_prompt (editable text)
- temperature, max_tokens
- tools[] (which MCP tools the agent can call)
- enabled (toggle on/off)

Ralph Loop configuration:
- max_iterations (default 5)
- threshold (default 0.95)
- auto_fix_enabled (default true)
- human_approval_required (default true)

Pipeline configuration:
- parallel_subagents (default true)
- max_concurrent (default 8)

---

### 3.7 Auth Domain

**Responsibility**: OAuth 2.0 authorization to Anthropic and OpenAI. Token management.

**Aggregates**:
- `OAuthConnection` → `AccessToken`, `RefreshToken`, `TokenExpiry`
- `ProviderConfig` (OAuth client_id, redirect_uri, scopes)

**Supported providers**:

| Provider | Auth Method | Details |
|---|---|---|
| Anthropic | OAuth 2.0 (Authorization Code + PKCE) | console.anthropic.com/oauth, scopes: messages:write, models:read |
| OpenAI (Codex) | OAuth 2.0 (Authorization Code + PKCE) | auth.openai.com/authorize, scopes: model.request, api.all |
| Google Gemini | API Key (no OAuth available) | Stored encrypted, managed by Auth domain |
| Ollama | No auth (local) | Only URL configuration needed |
| Custom OpenAI-compatible | API Key | Stored encrypted, managed by Auth domain |

Note: Google Gemini and Ollama do not support OAuth. Auth domain manages their API keys with the same AES-256 encryption. The OAuth flow applies only to Anthropic and OpenAI.

**OAuth Flow**: Authorization Code + PKCE
1. Frontend: user clicks "Connect to Anthropic"
2. Auth domain: generate state (CSRF), code_verifier, code_challenge
3. Return authorize URL to frontend
4. Browser redirect to provider
5. User logs in & consents
6. Callback with auth code
7. Auth domain exchanges code + code_verifier for tokens
8. Encrypt tokens (AES-256) and store in DB
9. Auto-refresh before expiry (5-minute buffer)

**Token management**: Any domain calls `auth.get_token("anthropic")` and receives a valid access_token. Auto-refresh is transparent.

**Encryption**: AES-256 for token storage, key from env `ENCRYPTION_KEY`.

**Electron OAuth**: Uses `BrowserWindow` for OAuth redirect, intercepts callback via custom protocol `presenton://oauth/callback`.

**MCP Tools**:
- `auth.connect` (provider → OAuth URL)
- `auth.callback` (code → tokens)
- `auth.get_token` (provider → valid access_token, auto-refresh)
- `auth.disconnect` (provider → revoke)
- `auth.status` (list connected providers)

---

### 3.8 Identity Domain

**Responsibility**: Users, sessions, roles, permissions.

**Aggregates**:
- `User` → `Session[]`, `Role[]`
- `Role` → `Permission[]`

**Authentication details**:
- Password hashing: bcrypt with salt
- JWT: RS256 signed, access_token TTL 15min, refresh_token TTL 7 days
- Session: stored in DB, invalidated on logout/password change
- RBAC roles: `admin`, `editor`, `viewer`

**MCP Tools**:
- `identity.register` (email, password → user_id + JWT)
- `identity.login` (email, password → JWT pair)
- `identity.logout` (invalidate session)
- `identity.refresh` (refresh_token → new JWT pair)
- `identity.users.list`, `identity.users.get`
- `identity.roles.assign`, `identity.roles.list`
- `identity.verify_session` (JWT → user context, used as middleware by all domains)

---

### 3.9 WebAccess Domain

**Responsibility**: All internet interactions — search, scraping, fetch.

**Aggregates**:
- `WebQuery` → `WebResult[]`
- `ScrapedPage` → `ExtractedContent`

**MCP Tools**:
- `web.search` (query → results from Google/Bing/DuckDuckGo)
- `web.fetch` (URL → markdown content)
- `web.screenshot` (URL → image, for style extraction)
- `web.extract_data` (URL → structured data)

---

### 3.10 Export Domain

**Responsibility**: Export to PDF, PPTX, other formats.

**Aggregates**:
- `ExportJob` → `ExportConfig`, `ExportResult`

**MCP Tools**:
- `export.to_pdf` (presentation_id → PDF file path)
- `export.to_pptx` (presentation_id → PPTX file path)
- `export.status` (job tracking for long exports)
- `export.download` (file path → file)

**Dependencies**: Rendering for HTML, Puppeteer for PDF, python-pptx for PPTX.

---

## 4. Inter-Domain Communication

### Synchronous: MCP Tool Calls

Domain A calls Domain B's MCP tool and waits for response. Used for commands and queries.

### Asynchronous: Redis Streams

Domain events published to Redis Streams. Each domain is a separate consumer group. At-least-once delivery guarantee.

### Communication Rules

- **Commands** (sync): MCP tool calls. Agent calls `content.generate_slide` and waits.
- **Events** (async): Redis Streams. `PresentationCreated` → Style domain subscribes, reacts.
- **Queries** (read): MCP tool calls. `presentation.get` → returns data.

---

## 5. Infrastructure

### Docker Compose — Production

Services: gateway, redis, postgres, presentation, style, content, rendering, media, agent, auth, identity, web_access, export, frontend.

**Database strategy**: Shared PostgreSQL, separate schema per domain. Each domain manages its own tables via Alembic. No cross-schema access.

**Connection pool**: `pool_size=10, max_overflow=20, pool_recycle=3600` on all domains.

### Gateway

- **API Gateway**: nginx reverse proxy → frontend + domain APIs
- **MCP Gateway**: External MCP server aggregating all domain MCP tools
- **Auth middleware**: JWT validation, session check on all routes
- **Rate limiting**: `limit_req_zone` in nginx + FastAPI middleware

**Port allocation and routing**:

| Domain | HTTP Port | MCP Port |
|---|---|---|
| presentation | 8010 | 9010 |
| style | 8020 | 9020 |
| content | 8030 | 9030 |
| rendering | 8040 | 9040 |
| media | 8050 | 9050 |
| agent | 8060 | 9060 |
| auth | 8070 | 9070 |
| identity | 8080 | 9080 |
| web_access | 8090 | 9090 |
| export | 8100 | 9100 |
| frontend | 3000 | — |
| mcp_gateway | — | 8001 |

```
HTTP routing (nginx):
  /api/v1/presentations/*  → presentation :8010
  /api/v1/styles/*         → style :8020
  /api/v1/content/*        → content :8030
  /api/v1/rendering/*      → rendering :8040
  /api/v1/media/*          → media :8050
  /api/v1/agents/*         → agent :8060
  /api/v1/auth/*           → auth :8070
  /api/v1/identity/*       → identity :8080
  /api/v1/web/*            → web_access :8090
  /api/v1/export/*         → export :8100
  /*                       → frontend :3000

MCP routing:
  /mcp → mcp_gateway :8001
  mcp_gateway routes each tool prefix to the corresponding domain MCP port
```

### Electron — Standalone

All domains run embedded in a single process:
- `launcher.py` starts all domains in-process
- `embedded_bus.py` — in-memory event bus (replaces Redis)
- `embedded_db.py` — SQLite with table prefix per domain (replaces PostgreSQL)
- MCP via stdio/in-process (replaces TCP)

**Infrastructure abstraction in shared kernel**:
- `EventBus(Protocol)` → `RedisEventBus` (Docker) / `InMemoryEventBus` (Electron)
- `DatabaseConfig` → PostgreSQL schema (Docker) / SQLite prefix (Electron)
- `MCPTransport` → TCP (Docker) / Stdio (Electron)

### Security Fixes

| Issue | Solution |
|---|---|
| CORS `*` | Gateway: whitelist from env `ALLOWED_ORIGINS` |
| API keys plaintext | Auth domain: AES-256 encrypted storage |
| `/app_data/` no auth | Gateway: JWT middleware on all static routes |
| No rate limiting | Gateway: nginx `limit_req_zone` + FastAPI middleware |
| No auth | Identity domain: JWT + RBAC |
| DB no pool config | Shared: pool_size=10, max_overflow=20, pool_recycle=3600 |
| No health checks | Each domain: `GET /health`, Gateway: aggregated `/health` |
| No structured logging | Shared: structlog (Python), pino (Next.js) |
| Inline DB migration | Alembic per-domain, remove hardcoded ALTER TABLE |
| Dockerfile no lockfile | `uv sync --frozen` per domain |

### Monitoring & Observability

- **Prometheus**: each domain exports metrics on `/metrics`
- **Distributed tracing**: OpenTelemetry, trace ID propagated through MCP calls
- **Centralized logging**: structlog → stdout → Docker log driver
- **Health**: `/health` per domain + Gateway aggregated health
- **Sentry**: error tracking on each domain

---

## 6. Frontend Architecture

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/
│   │   ├── page.tsx                    # Presentation list
│   │   └── settings/
│   │       ├── agents/page.tsx         # Agent configuration
│   │       ├── connections/page.tsx    # OAuth connections
│   │       ├── styles/page.tsx         # Preset library
│   │       └── profile/page.tsx
│   ├── (presentation)/
│   │   ├── [id]/
│   │   │   ├── page.tsx               # Presentation editor
│   │   │   ├── preview/page.tsx       # Fullscreen preview
│   │   │   └── export/page.tsx
│   │   └── new/
│   │       ├── page.tsx               # Creation wizard
│   │       └── components/
│   │           ├── TopicInput.tsx
│   │           ├── StylePicker.tsx     # Upload/URL/Preset
│   │           ├── AgentConfig.tsx
│   │           └── PipelineProgress.tsx
│   └── api/
├── components/
│   ├── agents/
│   │   ├── AgentCard.tsx
│   │   ├── AgentConfigEditor.tsx
│   │   ├── PipelineVisualizer.tsx     # DAG visualization
│   │   └── RalphLoopPanel.tsx
│   ├── presentation/
│   │   ├── SlideEditor.tsx
│   │   ├── SlidePreview.tsx
│   │   ├── SlideSorter.tsx
│   │   └── InfographicEditor.tsx
│   ├── style/
│   │   ├── StyleUploader.tsx
│   │   ├── URLStyleExtractor.tsx
│   │   ├── PresetGallery.tsx
│   │   ├── ColorPaletteEditor.tsx
│   │   └── TypographyPicker.tsx
│   └── shared/
│       ├── WebSocketProvider.tsx
│       └── AuthGuard.tsx
├── store/
│   ├── slices/
│   │   ├── presentationSlice.ts
│   │   ├── agentSlice.ts
│   │   ├── styleSlice.ts
│   │   ├── ralphLoopSlice.ts
│   │   └── authSlice.ts
│   └── store.ts
└── hooks/
    ├── useWebSocket.ts
    ├── useAgentPipeline.ts
    └── useRalphLoop.ts
```

**Key UI flows**:

1. **Create presentation**: Topic → Style (upload/URL/preset) → Agent config → Start Pipeline → Real-time progress → Ralph Loop → Approve → Export

2. **Ralph Loop UI**: Checklist with pass/fail, weighted score, slide previews, "Approve" / "Request changes" buttons with feedback text field

3. **Agent Config UI**: Agent table, inline system prompt editing, model/provider selection, enabled toggle

---

## 7. Testing Strategy

| Layer | Tool | Scope |
|---|---|---|
| Domain unit tests | pytest | Entities, value objects, domain services |
| Application tests | pytest | Use cases, command/query handlers |
| API integration tests | pytest + httpx | FastAPI endpoints |
| MCP integration tests | pytest | MCP tool calls between domains |
| Frontend unit tests | Vitest + RTL | Components, hooks, Redux slices |
| Frontend E2E | Cypress | Full user flows |
| CI | GitHub Actions | All tests run, blocking (no continue-on-error) |

**CI workflow**: test every domain independently + integration tests for cross-domain MCP calls.

---

## 8. Migration Strategy

The redesign is a complete rewrite organized by domain. Existing code from the current Presenton repo serves as reference for:
- PPTX generation logic → Export domain
- LLM client patterns → Content/Agent domains
- Next.js components → Frontend (adapted)
- Database models → Presentation domain (migrated to new schema)

No data migration needed — fresh deployment with new schema.
