# Presenton DDD+MCP — Implementation Plan Overview

> **Execution order is strict. Each plan depends on previous plans being completed.**

## Plan 1: Shared Kernel + Infrastructure [DETAILED]
**File:** `2026-04-02-plan-01-shared-kernel.md`
**Tasks:** 14 tasks — project scaffolding, Entity/AggregateRoot, ValueObject, DomainEvent/EventBus, Repository protocol, InMemoryEventBus, RedisEventBus, DatabaseConfig, Logging, Settings, MCP ServerBase, MCP Client, full test suite, public API exports.

## Plan 2: Identity + Auth Domains [DETAILED]
**File:** `2026-04-02-plan-02-identity-auth.md`
**Tasks:** 9 tasks — Identity entities, Token/Password services, Register/Login commands, FastAPI router, Auth EncryptionService, OAuth entities/flow, Auth FastAPI router, MCP servers, full test suite.

## Plan 3: Presentation Domain
**Depends on:** Plans 1, 2
**Key tasks:**
- [ ] Presentation, Slide, SlideElement, Template entities
- [ ] CRUD commands (CreatePresentation, AddSlide, UpdateSlide, ReorderSlides)
- [ ] Queries (GetPresentation, ListPresentations)
- [ ] SQLModel DB models + Alembic migrations (schema: `presentation`)
- [ ] FastAPI router with JWT middleware
- [ ] MCP server (presentation.create, .get, .update, slide.add, .update, .remove, .reorder, template.apply)
- [ ] Unit + integration tests

## Plan 4: Style Domain
**Depends on:** Plans 1, 2, 3
**Key tasks:**
- [ ] StyleProfile, ColorPalette, Typography, LayoutRules, Spacing value objects
- [ ] StylePreset entity + built-in presets (minimal-light, corporate-blue, creative-bold, dark-elegant, startup-gradient)
- [ ] Style extraction from PPTX (python-pptx) — extract theme colors, fonts, layouts
- [ ] Style extraction from PDF (pdfplumber) — extract fonts, colors, geometry
- [ ] Style extraction from URL — WebAccess.screenshot → Vision model → StyleProfile
- [ ] StyleProfile → CSS variables converter
- [ ] StyleProfile → Tailwind theme converter
- [ ] style.validate tool (for Ralph Loop)
- [ ] MCP server + FastAPI router
- [ ] Unit + integration tests

## Plan 5: Content Domain
**Depends on:** Plans 1, 2, 7 (Auth for LLM access)
**Key tasks:**
- [ ] ContentPlan, SlideContent, SystemPrompt, PromptTemplate entities
- [ ] LLM client abstraction (uses Auth domain for tokens)
- [ ] GenerateOutline command — topic → structured outline
- [ ] GenerateSlideContent command — outline item → slide text
- [ ] ReviseContent command — text + feedback → improved text
- [ ] SystemPrompt CRUD (configurable per agent)
- [ ] Web grounding integration (via WebAccess domain)
- [ ] MCP server + FastAPI router
- [ ] Unit + integration tests

## Plan 6: Rendering Domain
**Depends on:** Plans 1, 4 (Style for CSS)
**Key tasks:**
- [ ] RenderJob, RenderedSlide, RenderConfig entities
- [ ] HTML slide renderer — Tailwind CSS + style variables
- [ ] Puppeteer/Chromium integration — HTML → PNG/screenshot
- [ ] Thumbnail generation
- [ ] Visual diff — compare two renders, compute difference percentage
- [ ] Batch render — parallel rendering of all slides
- [ ] MCP server (rendering.render_slide, .render_preview, .visual_diff, .batch_render)
- [ ] Unit + integration tests

## Plan 7: Media Domain
**Depends on:** Plans 1, 2, 9 (WebAccess for image search)
**Key tasks:**
- [ ] MediaAsset, ImageAsset, InfographicAsset, IconAsset entities
- [ ] InfographicTemplate entity + built-in SVG templates (pie chart, bar chart, timeline, flowchart, comparison)
- [ ] Image search — Pexels, Pixabay APIs + web search fallback
- [ ] AI image generation — DALL-E 3, Gemini Flash (via Auth domain)
- [ ] SVG generator — D3.js/SVG for data-driven charts
- [ ] Template engine — fill SVG templates with data
- [ ] MCP server + FastAPI router
- [ ] Unit + integration tests

## Plan 8: WebAccess Domain
**Depends on:** Plan 1
**Key tasks:**
- [ ] WebQuery, WebResult, ScrapedPage, ExtractedContent entities
- [ ] Web search — DuckDuckGo/Google search integration
- [ ] Web fetch — URL → markdown content (HTML parser)
- [ ] Screenshot — Puppeteer-based URL screenshot at multiple viewports
- [ ] Data extraction — structured data from web pages
- [ ] Rate limiting + caching for web requests
- [ ] MCP server + FastAPI router
- [ ] Unit + integration tests

## Plan 9: Export Domain
**Depends on:** Plans 1, 3, 6 (Rendering for HTML)
**Key tasks:**
- [ ] ExportJob, ExportConfig, ExportResult entities
- [ ] PDF export — Puppeteer HTML → PDF
- [ ] PPTX export — python-pptx with slide data + style
- [ ] Job tracking — async export with status polling
- [ ] File storage + cleanup
- [ ] MCP server (export.to_pdf, .to_pptx, .status, .download)
- [ ] Unit + integration tests

## Plan 10: Agent Domain (LARGEST)
**Depends on:** ALL previous plans
**Key tasks:**
- [ ] Agent, AgentConfig, AgentPipeline, AgentStep entities
- [ ] AgentRun, SubAgentRun execution tracking
- [ ] 13 specialized agent definitions with default system prompts
- [ ] SubAgentExecutor — parallel execution with asyncio.Semaphore
- [ ] Pipeline stages (RESEARCH → PLANNING → CONTENT → ASSEMBLY → RENDERING → RALPH LOOP → EXPORT)
- [ ] RalphLoop entity + runner (auto-checks + human approval)
- [ ] Checklist criteria with weighted scoring
- [ ] Fixer agent mapping (failed criterion → fixer agent)
- [ ] WebSocket real-time progress events
- [ ] Agent configuration CRUD (system prompts, models, tools, parameters)
- [ ] MCP server + FastAPI router
- [ ] Unit + integration tests

## Plan 11: Gateway + MCP Gateway
**Depends on:** ALL domain plans
**Key tasks:**
- [ ] nginx.conf — reverse proxy to all domains by path prefix
- [ ] Rate limiting — nginx limit_req_zone + FastAPI middleware
- [ ] CORS — whitelist from ALLOWED_ORIGINS env
- [ ] JWT middleware — validate token on all API routes
- [ ] Static file auth — JWT check on /app_data/* routes
- [ ] MCP Gateway — aggregates all domain MCP tools, routes by prefix
- [ ] Health endpoint — aggregated /health checking all domains
- [ ] Dockerfile
- [ ] Integration tests

## Plan 12: Frontend
**Depends on:** Plans 1-11 (API endpoints must exist)
**Key tasks:**
- [ ] Project setup — Next.js 14 with TypeScript, Tailwind, Redux Toolkit
- [ ] Auth pages — login, register
- [ ] Dashboard — presentation list, settings
- [ ] Presentation creation wizard — TopicInput, StylePicker, AgentConfig, PipelineProgress
- [ ] Slide editor — SlideEditor, SlidePreview, SlideSorter, InfographicEditor
- [ ] Style components — StyleUploader, URLStyleExtractor, PresetGallery, ColorPaletteEditor, TypographyPicker
- [ ] Agent components — AgentCard, AgentConfigEditor, PipelineVisualizer (DAG), RalphLoopPanel
- [ ] WebSocket integration — useWebSocket, useAgentPipeline, useRalphLoop hooks
- [ ] Redux slices — presentation, agent, style, ralphLoop, auth
- [ ] AuthGuard route protection
- [ ] Vitest + RTL unit tests
- [ ] Cypress E2E tests

## Plan 13: Electron
**Depends on:** Plans 1-12
**Key tasks:**
- [ ] Electron main process — window management, IPC
- [ ] Process manager — launch embedded Python + Next.js
- [ ] Embedded launcher.py — starts all domains in-process
- [ ] InMemoryEventBus wiring (replaces Redis)
- [ ] SQLite wiring with table prefix per domain (replaces PostgreSQL)
- [ ] OAuth via BrowserWindow + custom protocol presenton://
- [ ] Build scripts — electron-builder for Windows, macOS, Linux
- [ ] Sync export runtime

## Plan 14: Docker Compose + CI
**Depends on:** ALL plans
**Key tasks:**
- [ ] docker-compose.yml — all services with proper depends_on, volumes, env
- [ ] docker-compose.dev.yml — development overrides with volume mounts
- [ ] Per-domain Dockerfiles — multi-stage build, uv sync --frozen
- [ ] GitHub Actions CI — test every domain, lint, type check, build Docker images
- [ ] GitHub Actions CD — push images to ghcr.io on release
- [ ] Health check integration tests in CI
- [ ] SpecKit configuration

---

## Execution Summary

| Plan | Est. Tasks | Domain(s) |
|------|-----------|-----------|
| 1 | 14 | shared |
| 2 | 9 | identity, auth |
| 3 | ~8 | presentation |
| 4 | ~10 | style |
| 5 | ~8 | content |
| 6 | ~8 | rendering |
| 7 | ~8 | media |
| 8 | ~7 | web_access |
| 9 | ~7 | export |
| 10 | ~12 | agent |
| 11 | ~7 | gateway |
| 12 | ~10 | frontend |
| 13 | ~8 | electron |
| 14 | ~6 | infra/CI |
| **Total** | **~120** | |
