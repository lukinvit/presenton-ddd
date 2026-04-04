# Presenton Agent Pipeline — 4-Stage Architecture

## Overview

The presentation generation pipeline consists of 4 sequential stages, each with specialized agents. The pipeline adapts based on whether the user starts from scratch or provides an existing presentation.

---

## Stage 1: DISCOVERY (Interview + Analysis)

**Goal:** Understand what the user needs. Two modes:

### Mode A: New Presentation (from scratch)
- InterviewAgent conducts an adaptive interview with the user
- Asks about: topic, audience, goals, key messages, tone, data/facts to include
- Questions adapt based on previous answers (not a fixed questionnaire)
- ResearchAgent gathers supporting data from the web
- Output: `DiscoveryBrief` — structured understanding of what to build

### Mode B: Existing Presentation (improve/redesign)
- AnalyzerAgent parses the uploaded file (PPTX/PDF)
- Extracts: content structure, data, key messages, visual style
- StyleReaderAgent reads the current visual style (colors, fonts, layouts)
- InterviewAgent asks what to improve, change, add
- Output: `DiscoveryBrief` + `ExistingStyleProfile` + `ContentAnalysis`

**Key principle:** Never start creating without fully understanding intent.

---

## Stage 2: SPECIFICATION (Brief + References)

**Goal:** Create a detailed specification that agents can execute.

- BriefArchitect compiles the DiscoveryBrief into a detailed creative brief
- Includes: slide-by-slide outline, content requirements, visual direction
- ReferenceAnalyzer processes user-provided references (URLs, images, PDFs)
- Extracts design patterns, color schemes, typography, layout patterns
- StyleDirector synthesizes references into a StyleGuide
- User reviews and approves the brief before Stage 3

**Output:** `CreativeBrief.md` + `StyleGuide.md` — the "contract" for Stage 3.

---

## Stage 3: PRODUCTION (Create + Ralph Loop)

**Goal:** Build the presentation with continuous quality checks.

### Sub-stages:
1. **Content Generation** — ContentWriter creates slide text based on brief
2. **Visual Design** — PaletteDesigner, FontSelector, LayoutComposer design each slide
3. **Media** — ImageCurator finds images, InfographicBuilder creates data visuals
4. **Assembly** — SlideAssembler combines content + design + media into HTML slides
5. **Rendering** — SlideRenderer produces HTML output
6. **Ralph Loop** — QualityReviewer + StyleEnforcer check against brief
   - Auto-fix cycle until threshold met
   - Live preview updates visible to user

**Key principle:** The Ralph Loop runs continuously, not once at the end.

---

## Stage 4: REVIEW (User Feedback + Export)

**Goal:** Get user approval and export.

- Present final result to user with side-by-side comparison to brief
- ReviewInterviewer asks structured questions about each aspect
- User can request changes (triggers targeted fixes in Stage 3)
- Once approved: export to PDF/PPTX
- PostMortem agent logs lessons for future presentations

**Output:** Approved presentation + export files.
