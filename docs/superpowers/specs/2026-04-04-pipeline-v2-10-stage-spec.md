# Presenton Pipeline v2 — 10-Stage Conveyor with Artifacts & Quality Gates

**Date:** 2026-04-04
**Status:** Draft
**Supersedes:** 4-stage pipeline from 2026-04-02 spec

---

## 1. Overview

The presentation pipeline is a 10-stage conveyor with explicit decision points, quality gates, and persistent artifacts. Every stage reads inputs from previous artifacts and writes outputs as structured files. The pipeline can stop, branch, or loop at any gate.

### Design Principles

1. **Artifact-driven** — agents communicate via files, not ephemeral API calls. Every stage produces a named artifact that the next stage consumes.
2. **Decision points** — explicit branching logic at key moments (strategy, enrichment, packaging).
3. **Quality gates** — automated checks that halt the pipeline if criteria aren't met.
4. **Dual mode** — pipeline adapts whether input is "from scratch" or "existing presentation".
5. **Reproducible** — the final package includes everything needed to rebuild the result.

### Artifact Storage

All artifacts stored in a per-presentation workspace:

```
workspaces/{presentation_id}/
├── brief.json                    # Stage 1 output
├── source/                       # Stage 2 output
│   ├── original.pptx             # uploaded file (if any)
│   ├── original.pdf              # PDF version
│   └── reference_urls.json       # reference links
├── assets/                       # Stage 2+7 output
│   ├── images/                   # extracted/found images
│   ├── fonts/                    # font files
│   ├── icons/                    # icon assets
│   └── infographics/             # generated SVGs
├── preview/                      # Stage 2 output
│   ├── slide_001.png             # thumbnail per slide
│   └── ...
├── slides_manifest.json          # Stage 3 output
├── render_strategy.json          # Stage 4 output
├── design_tokens.json            # Stage 5 output
├── style_guide.md                # Stage 5 output
├── content_plan.md               # Stage 6 output
├── slides/                       # Stage 5-8 output
│   ├── slide_001.html
│   ├── slide_002.html
│   └── ...
├── sources.json                  # Stage 8 output
├── qa_report.md                  # Stage 9 output
├── output/                       # Stage 10 output
│   ├── index.html                # final presentation
│   ├── presentation.pdf          # PDF export
│   ├── slides.pptx               # PPTX export (if requested)
│   ├── speaker_notes.md          # speaker notes document
│   ├── storytelling.md           # narrative script
│   ├── sources.md                # bibliography
│   └── README.md                 # package documentation
└── pipeline_state.json           # pipeline execution state
```

---

## 2. Pipeline State Machine

```
                    ┌──────────────────────────────────────────────┐
                    │                                              │
INTAKE ──► INGEST ──► PARSE ──► STRATEGY ──► BASE ──► CONTENT ──► │
                                   │                              │
                                   ├── raster ──────────────────► │
                                   ├── structured ──────────────► │
                                   └── hybrid ──────────────────► │
                                                                  │
    ┌─────────────────────────────────────────────────────────────┘
    │
    ▼
 ASSETS ──► ENRICHMENT ──► RENDER & QA ──► PACKAGE
                │               │
                │               └──── FAIL? ──► fix ──► re-render
                │
                └──── external facts? ──► verify ──► continue
```

### `pipeline_state.json`

```json
{
  "presentation_id": "uuid",
  "created_at": "2026-04-04T12:00:00Z",
  "current_stage": "PARSE",
  "mode": "from_scratch | from_existing",
  "stages": {
    "INTAKE": {"status": "completed", "started_at": "...", "completed_at": "...", "artifact": "brief.json"},
    "INGEST": {"status": "completed", "artifact": "source/"},
    "PARSE": {"status": "running", "artifact": "slides_manifest.json"},
    "STRATEGY": {"status": "pending"},
    "BASE": {"status": "pending"},
    "CONTENT": {"status": "pending"},
    "ASSETS": {"status": "pending"},
    "ENRICHMENT": {"status": "pending"},
    "RENDER_QA": {"status": "pending", "iterations": 0, "max_iterations": 5},
    "PACKAGE": {"status": "pending"}
  },
  "quality_gates": {
    "slide_count_match": null,
    "no_overflow": null,
    "no_unverified_facts": null,
    "assets_complete": null,
    "strategy_matches_requirement": null,
    "pdf_no_crop": null
  },
  "decisions": {
    "render_strategy": null,
    "needs_editability": null,
    "needs_pixel_perfect": null,
    "has_external_facts": null,
    "needs_speaker_notes": null,
    "output_format": null
  }
}
```

---

## 3. Stages

### Stage 1: INTAKE

**Goal:** Determine presentation purpose, audience, format, and constraints.

**Input:**
- User conversation (InterviewAgent chat)
- Uploaded files (PPTX/PDF/images) — optional
- Reference URLs — optional

**Agent:** `InterviewAgent` (claude-opus-4-6, temp 0.8)

**Interview parameters to capture:**

| Parameter | Type | Values | Required |
|---|---|---|---|
| `goal` | string | pitch, report, education, conference, meeting, sales | yes |
| `audience` | string | executives, investors, students, developers, general | yes |
| `duration_minutes` | int | 5, 10, 15, 30, 60 | yes |
| `slide_count` | int | user-specified or auto-calculated from duration | yes |
| `tone` | string | formal, casual, inspirational, technical, playful | yes |
| `core_message` | string | the ONE takeaway | yes |
| `output_format` | enum | html, pdf, html+pdf, pptx, all | yes |
| `editability` | enum | pixel_perfect, editable, hybrid | yes |
| `key_points` | string[] | topics to cover | yes |
| `data_sources` | string[] | statistics, charts, facts to include | no |
| `brand_guidelines` | object | colors, fonts, logo — or null | no |
| `reference_urls` | string[] | URLs of admired presentations/sites | no |
| `constraints` | object | mandatory slides, topics to avoid, terminology | no |
| `speaker_notes` | bool | include speaker notes | no |
| `language` | string | en, ru, etc. | yes |

**Output artifact:** `brief.json`

```json
{
  "version": "1.0",
  "mode": "from_scratch",
  "goal": "conference talk",
  "audience": "developers",
  "duration_minutes": 15,
  "slide_count": 12,
  "tone": "technical but engaging",
  "core_message": "AI agents can automate 80% of presentation work",
  "output_format": "html+pdf",
  "editability": "editable",
  "key_points": ["problem statement", "architecture", "demo", "results"],
  "data_sources": [{"type": "statistic", "description": "market size of presentation tools"}],
  "brand_guidelines": null,
  "reference_urls": ["https://example.com/admired-deck"],
  "constraints": {
    "mandatory_slides": ["title", "agenda", "thank_you"],
    "avoid_topics": [],
    "terminology": {"LLM": "assume known"}
  },
  "speaker_notes": true,
  "language": "en",
  "conversation_summary": "User wants a 15-minute conference talk about AI-powered presentation generation..."
}
```

**Quality gate:** brief.json must have all required fields populated. InterviewAgent must confirm understanding with user before finalizing.

---

### Stage 2: INGEST

**Goal:** Collect all source materials into a structured workspace.

**Input:** `brief.json`, uploaded files, reference URLs

**Agents:**
- `IngestAgent` (no LLM — pure file operations)
- `StyleReaderAgent` (sonnet, temp 0.3) — only if mode=from_existing

**Actions:**

| Input type | Action |
|---|---|
| PPTX file | Copy to `source/original.pptx`, export to PDF → `source/original.pdf`, render each slide to PNG → `preview/` |
| PDF file | Copy to `source/original.pdf`, render pages to PNG → `preview/` |
| Images/screenshots | Copy to `source/references/` |
| Reference URLs | Save to `source/reference_urls.json`, take screenshots → `source/references/` |
| Brand assets (logo, fonts) | Copy to `assets/` |

**Output artifacts:**
- `source/` directory with all originals
- `preview/` directory with slide thumbnails
- `assets/` directory (partial — brand assets only at this stage)

**Quality gate:** All files listed in brief.json must exist in workspace. No corrupted files.

---

### Stage 3: PARSE & INVENTORY

**Goal:** Decompose the source presentation (if exists) into structured data.

**Input:** `source/original.pptx` or `source/original.pdf`

**Agents:**
- `ParserAgent` (sonnet, temp 0.2) — structured extraction
- `AnalyzerAgent` (sonnet, temp 0.3) — semantic analysis

**For PPTX parsing (python-pptx):**

```json
// slides_manifest.json
{
  "source_file": "source/original.pptx",
  "total_slides": 15,
  "dimensions": {"width": 13333333, "height": 7500000, "units": "emu"},
  "fonts_used": ["Arial", "Calibri", "Helvetica Neue"],
  "color_theme": {
    "accent1": "#0078D4",
    "accent2": "#00BCF2",
    "dk1": "#000000",
    "lt1": "#FFFFFF"
  },
  "slides": [
    {
      "index": 0,
      "layout_name": "Title Slide",
      "background": {"type": "solid", "color": "#FFFFFF"},
      "elements": [
        {
          "id": "title_1",
          "type": "text_box",
          "position": {"left": 838200, "top": 2286000, "width": 10515600, "height": 1325563},
          "text": "AI-Powered Presentations",
          "font": {"family": "Calibri", "size": 4400, "bold": true, "color": "#000000"},
          "paragraph_alignment": "center"
        },
        {
          "id": "subtitle_1",
          "type": "text_box",
          "position": {"left": 1524000, "top": 3886200, "width": 9144000, "height": 762000},
          "text": "How agents build better decks",
          "font": {"family": "Calibri", "size": 2000, "bold": false, "color": "#666666"}
        },
        {
          "id": "logo_1",
          "type": "image",
          "position": {"left": 5943600, "top": 5486400, "width": 1447800, "height": 762000},
          "image_ref": "assets/images/logo.png",
          "alt_text": "Company Logo"
        }
      ],
      "notes": "Welcome everyone. Today I'll show you..."
    }
  ],
  "tables": [],
  "charts": [
    {
      "slide_index": 5,
      "chart_type": "bar",
      "title": "Market Growth",
      "data": {"categories": ["2023", "2024", "2025"], "series": [{"name": "Revenue", "values": [10, 25, 45]}]}
    }
  ],
  "groups": [],
  "master_layouts": ["Title Slide", "Title and Content", "Two Content", "Blank"]
}
```

**For "from scratch" mode:** Generate a minimal manifest from brief.json with planned slide types:

```json
{
  "source_file": null,
  "total_slides": 12,
  "slides": [
    {"index": 0, "planned_type": "title_slide", "planned_title": "AI-Powered Presentations"},
    {"index": 1, "planned_type": "content", "planned_title": "Agenda"},
    {"index": 2, "planned_type": "section_divider", "planned_title": "The Problem"}
  ]
}
```

**Output artifact:** `slides_manifest.json`

**Quality gate:** Slide count must match brief.json. All referenced assets must be extractable.

---

### Stage 4: TARGET STRATEGY DECISION

**Goal:** Choose the rendering approach based on requirements.

**Input:** `brief.json` + `slides_manifest.json`

**Agent:** `StrategyAgent` (sonnet, temp 0.2) — deterministic decision

**Decision matrix:**

| Condition | Strategy |
|---|---|
| `editability=pixel_perfect` AND content unchanged | `raster` |
| `editability=editable` | `structured` |
| `editability=hybrid` | `hybrid` |
| `mode=from_scratch` | `structured` (always) |
| `mode=from_existing` AND complex layouts (>20 elements/slide avg) | `hybrid` |
| `mode=from_existing` AND simple layouts | `structured` |

**Strategy definitions:**

| Strategy | Description |
|---|---|
| `raster` | Slides rendered as images. Viewer HTML wraps pre-rendered PNGs. No text editing possible. Fastest, most faithful. |
| `structured` | Full HTML reconstruction. Text, images, layout all in HTML/CSS. Fully editable. May differ from original. |
| `hybrid` | Complex backgrounds/decorations as raster images. Text, key data, charts as editable HTML overlaid on top. |

**Output artifact:** `render_strategy.json`

```json
{
  "strategy": "structured",
  "reasoning": "User requires editable output, creating from scratch",
  "slide_strategies": [
    {"index": 0, "strategy": "structured", "complexity": "low"},
    {"index": 5, "strategy": "hybrid", "complexity": "high", "raster_layers": ["background_gradient", "decorative_shapes"]}
  ],
  "estimated_fidelity": 0.85,
  "estimated_editability": 0.95
}
```

**Quality gate:** Strategy must satisfy `editability` requirement from brief.json. If conflict detected, halt and ask user.

---

### Stage 5: BASE RECONSTRUCTION

**Goal:** Build the HTML skeleton, design system, and component library.

**Input:** `brief.json` + `slides_manifest.json` + `render_strategy.json` + reference analysis

**Agents:**
- `StyleDirector` (sonnet, temp 0.4) — design tokens + style guide
- `LayoutComposer` (sonnet, temp 0.5) — HTML skeleton

**Sub-steps:**

1. **Design Tokens** — extract or create from brief/references:

```json
// design_tokens.json
{
  "colors": {
    "primary": "#0066CC",
    "secondary": "#334155",
    "accent": "#F97316",
    "background": "#FFFFFF",
    "surface": "#F8FAFC",
    "text": "#1E293B",
    "text_muted": "#64748B",
    "border": "#E2E8F0",
    "success": "#22C55E",
    "warning": "#EAB308",
    "error": "#EF4444"
  },
  "typography": {
    "heading_font": "Inter",
    "body_font": "Inter",
    "scale": {
      "h1": {"size": "48px", "weight": 700, "line_height": 1.2, "letter_spacing": "-0.02em"},
      "h2": {"size": "36px", "weight": 600, "line_height": 1.3},
      "h3": {"size": "28px", "weight": 600, "line_height": 1.3},
      "body": {"size": "24px", "weight": 400, "line_height": 1.5},
      "caption": {"size": "18px", "weight": 400, "line_height": 1.4},
      "label": {"size": "14px", "weight": 500, "line_height": 1.0, "text_transform": "uppercase"}
    }
  },
  "spacing": {
    "base": "8px",
    "xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px", "2xl": "48px", "3xl": "64px"
  },
  "layout": {
    "slide_width": 1920,
    "slide_height": 1080,
    "safe_area": {"top": 80, "right": 80, "bottom": 80, "left": 80},
    "grid_columns": 12,
    "grid_gap": "24px"
  },
  "components": {
    "card": {"border_radius": "12px", "shadow": "0 2px 8px rgba(0,0,0,0.08)", "padding": "24px"},
    "bullet": {"style": "disc", "color": "accent", "indent": "24px"},
    "divider": {"height": "2px", "color": "border"},
    "image": {"border_radius": "8px", "object_fit": "cover"}
  }
}
```

2. **Style Guide** — human-readable document for QA reference → `style_guide.md`

3. **HTML Base** — skeleton with CSS variables, grid system, component classes:

```html
<!-- base_template.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1920">
  <style>
    :root { /* design tokens as CSS custom properties */ }
    .slide { width: 1920px; height: 1080px; position: relative; overflow: hidden; }
    .slide-header { /* ... */ }
    .slide-body { /* ... */ }
    /* component classes */
  </style>
</head>
<body>
  <!-- slides injected here -->
</body>
</html>
```

**Output artifacts:** `design_tokens.json`, `style_guide.md`, `slides/base_template.html`

**Quality gate:** All colors must have WCAG AA contrast ratios. Font sizes must be ≥24px for body text at 1080p.

---

### Stage 6: CONTENT ADAPTATION

**Goal:** Generate or adapt content for every slide.

**Input:** `brief.json` + `slides_manifest.json` + `content_plan.md` (if from_existing, also original content)

**Agents:**
- `ContentWriter` (sonnet, temp 0.7) — write/rewrite content
- `BriefArchitect` (opus, temp 0.5) — content plan

**Two modes:**

#### Mode A: From Scratch
1. `BriefArchitect` creates `content_plan.md`:
   - Slide-by-slide outline with title, purpose, content requirements
   - Narrative arc: intro → problem → solution → evidence → conclusion
   - Data visualization needs per slide
   - Image/media needs per slide

2. `ContentWriter` generates content per slide:

```json
// content output per slide
{
  "index": 0,
  "title": "AI-Powered Presentations",
  "subtitle": "How agents build better decks",
  "body": null,
  "bullets": null,
  "data_viz": null,
  "image_needs": ["hero background: abstract AI network visualization"],
  "speaker_notes": "Welcome everyone. Today I'll walk you through how we use AI agents to automate 80% of presentation creation work.",
  "layout_type": "title_slide"
}
```

#### Mode B: From Existing (Adaptation)
1. Read original content from `slides_manifest.json`
2. Apply requested changes from `brief.json`:
   - Update facts/data
   - Adjust tone
   - Add/remove/merge slides
   - Rewrite for new audience
3. **Preserve narrative logic** — don't break the story arc
4. Track what changed vs what's preserved

**Output artifact:** `content_plan.md` + updated `slides_manifest.json` with content

**Quality gate:**
- Slide count matches brief.json
- Every slide has a clear purpose (no filler slides)
- Word count per slide ≤ limits from style guide
- Core message appears in at least 2 slides

---

### Stage 7: ASSET NORMALIZATION

**Goal:** Prepare all media assets for consistent rendering.

**Input:** `assets/` directory + `slides_manifest.json`

**Agent:** `AssetAgent` (no LLM — pure tooling) + `ImageCurator` (haiku, temp 0.3) + `InfographicBuilder` (sonnet, temp 0.5)

**Actions:**

| Asset type | Action |
|---|---|
| Images from PPTX | Extract, convert to PNG/WebP, normalize to standard sizes |
| PDF embeds | Convert to SVG (vector) or PNG (raster) |
| Charts from PPTX | Extract data, regenerate as SVG |
| Icons | Find matching icon set, download SVG |
| Fonts | Locate web font files or Google Fonts links |
| Backgrounds | Export as full-slide images if hybrid strategy |
| Logos | Extract, ensure transparent background |
| New images needed | `ImageCurator` searches Pexels/Pixabay/web |
| New infographics | `InfographicBuilder` generates SVG from data |

**Normalization rules:**
- All images: max 1920x1080, WebP format preferred, <500KB per image
- All SVGs: viewBox normalized, colors use CSS variables
- All fonts: WOFF2 format, subset to used characters if >100KB
- File naming: `{slide_index}_{element_id}.{ext}`

**Output artifact:** Cleaned `assets/` directory with manifest

```json
// assets_manifest.json
{
  "images": [
    {"id": "slide_0_bg", "path": "assets/images/slide_0_bg.webp", "width": 1920, "height": 1080, "size_kb": 245}
  ],
  "fonts": [
    {"family": "Inter", "weights": [400, 500, 600, 700], "format": "woff2", "path": "assets/fonts/inter.woff2"}
  ],
  "icons": [],
  "infographics": [
    {"id": "slide_5_chart", "path": "assets/infographics/slide_5_chart.svg", "type": "bar_chart"}
  ]
}
```

**Quality gate:** No missing assets. No images >1MB. No broken font references. All referenced files exist.

---

### Stage 8: EXTERNAL ENRICHMENT

**Goal:** Verify facts, add sources, enrich with external data.

**Input:** `slides_manifest.json` (content) + `brief.json`

**Agents:**
- `ResearchAgent` (sonnet, temp 0.5) — fact finding
- `FactCheckerAgent` (sonnet, temp 0.2) — verification

**Actions:**

1. **Scan content** for claims that need verification:
   - Statistics ("market grew 40%")
   - Quotes ("As Elon Musk said...")
   - Dates ("founded in 2023")
   - Rankings ("#1 in the market")
   - Trends ("fastest growing segment")

2. **Research** each claim:
   - Find primary source
   - Verify accuracy
   - Get latest data if outdated

3. **Mark each fact:**

```json
// sources.json
{
  "facts": [
    {
      "claim": "Presentation software market is $15B",
      "slide_index": 3,
      "status": "verified",
      "source": "Grand View Research, 2025",
      "source_url": "https://...",
      "published_date": "2025-06-15",
      "confidence": 0.95,
      "note": "Updated from user's original $12B figure"
    },
    {
      "claim": "80% of professionals use PowerPoint",
      "slide_index": 4,
      "status": "unverified",
      "source": null,
      "confidence": 0.3,
      "note": "Cannot find primary source for this statistic"
    }
  ],
  "enrichments": [
    {
      "slide_index": 6,
      "type": "added_statistic",
      "content": "AI presentation tools market CAGR: 24.3% (2024-2030)",
      "source": "MarketsandMarkets, 2025"
    }
  ]
}
```

**Decision point:** If `has_external_facts` and any fact has `status=unverified` and `confidence < 0.5`:
- HALT pipeline
- Flag to user: "These facts couldn't be verified: [list]. Remove, replace, or mark as unverified?"

**Output artifact:** `sources.json`

**Quality gate:** No unverified facts with confidence < 0.5 on critical slides (title, key message, data slides).

---

### Stage 9: RENDER & QA LOOP

**Goal:** Assemble final slides, render, and iterate until quality passes.

**Input:** All previous artifacts

**Agents:**
- `SlideAssembler` (sonnet, temp 0.3) — HTML assembly
- `QualityReviewer` (opus, temp 0.2) — content + design review
- `StyleEnforcer` (sonnet, temp 0.2) — pixel-perfect style check
- Fixer agents as needed (routed by `FIXER_MAP`)

**Sub-steps per iteration:**

1. **Assemble** — SlideAssembler produces `slides/slide_{index}.html` for each slide
2. **Render** — Puppeteer renders each slide to PNG → `preview/`
3. **PDF export** — Generate PDF from all slides
4. **Automated checks:**

| Check | Method | Gate |
|---|---|---|
| Slide count | Count vs brief.json | HARD — must match |
| Text overflow | Puppeteer: check for scrollbars, clipping | HARD — no overflow |
| PDF cropping | Compare PDF page dimensions to slide dimensions | HARD — no cropping |
| Color compliance | Parse CSS, compare to design_tokens.json | SOFT — 95% match |
| Font compliance | Parse CSS, compare to design_tokens.json | SOFT — 100% match |
| Contrast ratios | Calculate for all text-on-background pairs | HARD — WCAG AA |
| Image loading | Check all `<img>` src resolve | HARD — no broken images |
| Consistent spacing | Compare spacing across slides | SOFT — 90% consistent |
| Layout alignment | Check grid alignment of elements | SOFT — 80% aligned |
| Content grammar | LLM check for spelling/grammar | SOFT — 0 errors |

5. **Score** — weighted score as in Ralph Loop (threshold: 0.95)
6. **Fix** — route failures to fixer agents via FIXER_MAP
7. **Re-render** — repeat from step 1

**Max iterations:** 5 (configurable)

**Human approval:** Required after automated checks pass. Show:
- Side-by-side: brief requirements vs what was built
- Slide-by-slide preview
- QA report summary
- Any unresolved issues

**Output artifact:** `qa_report.md`

```markdown
# QA Report — Iteration 3 (Final)

## Score: 4.8/5

## Checks
| Check | Status | Details |
|---|---|---|
| Slide count | PASS | 12/12 |
| Text overflow | PASS | 0 overflows |
| PDF cropping | PASS | All pages full-bleed |
| Color compliance | PASS | 100% match |
| Font compliance | PASS | 100% match |
| Contrast ratios | PASS | Min ratio: 5.2:1 |
| Image loading | PASS | 8/8 images loaded |
| Spacing consistency | PASS | 96% consistent |
| Layout alignment | PASS | 92% aligned |
| Content grammar | PASS | 0 errors |

## Iterations
- Iteration 1: Score 3.8 — fixed: font_hierarchy (slide 3), color_consistency (slides 5,7), layout_alignment (slide 9)
- Iteration 2: Score 4.5 — fixed: text_overflow (slide 11), image_quality (slide 6)
- Iteration 3: Score 4.8 — all checks pass

## Human Review: APPROVED
```

---

### Stage 10: PACKAGING

**Goal:** Produce self-contained deliverables.

**Input:** All artifacts

**Agent:** `PackagingAgent` (no LLM — pure file operations) + `ExportManager`

**Deliverables:**

| File | Content |
|---|---|
| `output/index.html` | Self-contained HTML presentation with all CSS/images inline or embedded |
| `output/presentation.pdf` | PDF export, all slides |
| `output/slides.pptx` | PPTX export (if `output_format` includes pptx) |
| `output/speaker_notes.md` | Speaker notes per slide, formatted for reading |
| `output/storytelling.md` | Narrative script — what to say, when, transitions |
| `output/sources.md` | Bibliography with all verified sources |
| `output/README.md` | Package docs: how to edit, rebuild, present |
| `output/preview/` | PNG thumbnails of all slides |

**README.md template:**

```markdown
# {presentation_title}

Generated: {date}
Slides: {count}
Duration: {minutes} min
Format: {output_format}

## Files
- `index.html` — open in browser, use arrow keys to navigate
- `presentation.pdf` — print-ready PDF
- `speaker_notes.md` — notes for the presenter
- `sources.md` — all referenced data sources

## Editing
The HTML version is fully editable. Open `index.html` in any code editor.
Design tokens: see `design_tokens.json`.
Style guide: see `style_guide.md`.

## Rebuilding
To regenerate from modified content, re-run the pipeline with the artifacts in this directory.
```

**Quality gate:** All requested output formats exist. PDF page count matches slide count. HTML renders without errors in Chromium.

---

## 4. Agent Roster (Updated)

### New agents (vs previous 19)

| Agent | Stage | Model | Temp | New? |
|---|---|---|---|---|
| `InterviewAgent` | 1 | opus | 0.8 | existing |
| `IngestAgent` | 2 | none (tooling) | — | **NEW** |
| `StyleReaderAgent` | 2 | sonnet | 0.3 | existing |
| `ParserAgent` | 3 | sonnet | 0.2 | **NEW** |
| `AnalyzerAgent` | 3 | sonnet | 0.3 | existing |
| `StrategyAgent` | 4 | sonnet | 0.2 | **NEW** |
| `StyleDirector` | 5 | sonnet | 0.4 | existing |
| `LayoutComposer` | 5 | sonnet | 0.5 | existing |
| `BriefArchitect` | 6 | opus | 0.5 | existing |
| `ContentWriter` | 6 | sonnet | 0.7 | existing |
| `ImageCurator` | 7 | haiku | 0.3 | existing |
| `InfographicBuilder` | 7 | sonnet | 0.5 | existing |
| `AssetAgent` | 7 | none (tooling) | — | **NEW** |
| `ResearchAgent` | 8 | sonnet | 0.5 | existing |
| `FactCheckerAgent` | 8 | sonnet | 0.2 | **NEW** |
| `SlideAssembler` | 9 | sonnet | 0.3 | existing |
| `QualityReviewer` | 9 | opus | 0.2 | existing |
| `StyleEnforcer` | 9 | sonnet | 0.2 | existing |
| `PaletteDesigner` | 9 (fixer) | sonnet | 0.4 | existing |
| `FontSelector` | 9 (fixer) | sonnet | 0.4 | existing |
| `ReviewInterviewer` | post-9 | opus | 0.8 | existing |
| `PackagingAgent` | 10 | none (tooling) | — | **NEW** |
| `ExportManager` | 10 | none (tooling) | — | existing |
| `PostMortem` | 10 | sonnet | 0.5 | existing |

**Total: 24 agents** (19 existing + 5 new)

---

## 5. Quality Gates Summary

| Gate | Stage | Type | Condition |
|---|---|---|---|
| Brief complete | 1 | HARD | All required fields in brief.json populated |
| Files ingested | 2 | HARD | All referenced files exist in workspace |
| Manifest valid | 3 | HARD | Slide count matches, all elements typed |
| Strategy consistent | 4 | HARD | Strategy satisfies editability requirement |
| Contrast accessible | 5 | HARD | WCAG AA on all text-background pairs |
| Content complete | 6 | HARD | Every slide has title + content |
| Assets resolved | 7 | HARD | No missing images, fonts, or icons |
| Facts verified | 8 | SOFT | Unverified facts flagged, user notified |
| No overflow | 9 | HARD | Zero text overflow or clipping |
| No PDF crop | 9 | HARD | PDF pages match slide dimensions |
| Score ≥ 0.95 | 9 | HARD | Weighted quality score passes threshold |
| Human approved | 9 | HARD | User confirms final result |
| Package complete | 10 | HARD | All requested output formats generated |

**HARD gates** halt the pipeline until resolved.
**SOFT gates** generate warnings but allow continuation with user acknowledgment.

---

## 6. Decision Points

| Decision | Stage | Options | Default |
|---|---|---|---|
| Mode | 1 | from_scratch, from_existing | auto-detected from input |
| Output format | 1 | html, pdf, html+pdf, pptx, all | html+pdf |
| Editability | 1 | pixel_perfect, editable, hybrid | editable |
| Render strategy | 4 | raster, structured, hybrid | structured |
| Has external facts | 8 | yes, no | auto-detected |
| Needs verification | 8 | yes, no, skip | yes if external facts found |
| Speaker notes | 1 | yes, no | yes |
| Language | 1 | en, ru, ... | en |

---

## 7. Migration from Current Pipeline

### What changes:
- 4 stages → 10 stages
- 19 agents → 24 agents (5 new tooling agents)
- Ephemeral API calls → persistent artifact files
- No decision points → 8 explicit decision points
- 1 quality check (Ralph Loop) → 13 quality gates across all stages
- Conversation history lost → `brief.json` preserves full interview

### What stays:
- DDD architecture (10 bounded contexts)
- MCP communication layer
- Ralph Loop algorithm (now part of Stage 9)
- Agent configuration UI
- Style preset system
- Docker deployment

### New infrastructure needed:
- Workspace directory per presentation (filesystem or object storage)
- python-pptx integration in ParserAgent (extract elements with positions)
- Puppeteer integration in Render stage (HTML → PNG, HTML → PDF)
- File upload handling in Ingest stage
