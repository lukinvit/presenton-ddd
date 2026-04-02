"""Default agent configurations and pipeline stages."""

from __future__ import annotations

from .value_objects import AgentConfig, PipelineConfig, PipelineStage

DEFAULT_AGENTS: dict[str, AgentConfig] = {
    "Orchestrator": AgentConfig(
        model="claude-opus-4-6",
        provider="anthropic",
        system_prompt=(
            "You are the Orchestrator agent. You coordinate the full presentation "
            "pipeline, delegating tasks to specialized sub-agents and ensuring "
            "each stage completes successfully before moving to the next."
        ),
        temperature=0.3,
        max_tokens=8192,
        tools=(
            "agent.run_pipeline",
            "agent.ralph_loop.start",
            "content.generate_plan",
            "style.extract",
            "rendering.render_slide",
        ),
    ),
    "ContentWriter": AgentConfig(
        model="claude-sonnet-4-6",
        provider="anthropic",
        system_prompt=(
            "You are the ContentWriter agent. You generate compelling, concise slide "
            "content including titles, bullet points, speaker notes, and narrative flow."
        ),
        temperature=0.7,
        max_tokens=4096,
        tools=("content.generate_plan", "content.write_slide"),
    ),
    "OutlineArchitect": AgentConfig(
        model="claude-sonnet-4-6",
        provider="anthropic",
        system_prompt=(
            "You are the OutlineArchitect agent. You create the high-level structure "
            "of presentations — deciding slide count, ordering, and logical flow."
        ),
        temperature=0.5,
        max_tokens=4096,
        tools=("content.generate_plan",),
    ),
    "StyleParser": AgentConfig(
        model="claude-sonnet-4-6",
        provider="anthropic",
        system_prompt=(
            "You are the StyleParser agent. You analyze reference materials (PDFs, "
            "images, brand guidelines) to extract visual style rules."
        ),
        temperature=0.3,
        max_tokens=4096,
        tools=("style.extract", "style.analyze_reference"),
    ),
    "PaletteDesigner": AgentConfig(
        model="claude-sonnet-4-6",
        provider="anthropic",
        system_prompt=(
            "You are the PaletteDesigner agent. You create harmonious color palettes "
            "that match brand identity and ensure accessibility."
        ),
        temperature=0.6,
        max_tokens=2048,
        tools=("style.create_palette", "style.check_contrast"),
    ),
    "FontSelector": AgentConfig(
        model="claude-sonnet-4-6",
        provider="anthropic",
        system_prompt=(
            "You are the FontSelector agent. You choose font pairings that establish "
            "clear hierarchy and match the presentation's tone."
        ),
        temperature=0.5,
        max_tokens=2048,
        tools=("style.select_fonts",),
    ),
    "LayoutComposer": AgentConfig(
        model="claude-sonnet-4-6",
        provider="anthropic",
        system_prompt=(
            "You are the LayoutComposer agent. You design slide layouts ensuring "
            "proper alignment, whitespace, and visual balance."
        ),
        temperature=0.5,
        max_tokens=4096,
        tools=("rendering.compose_layout", "style.get_grid"),
    ),
    "InfographicBuilder": AgentConfig(
        model="claude-sonnet-4-6",
        provider="anthropic",
        system_prompt=(
            "You are the InfographicBuilder agent. You create data visualizations, "
            "charts, and infographic elements for slides."
        ),
        temperature=0.5,
        max_tokens=4096,
        tools=("rendering.create_infographic",),
    ),
    "ImageCurator": AgentConfig(
        model="claude-haiku-4-5",
        provider="anthropic",
        system_prompt=(
            "You are the ImageCurator agent. You search for and select appropriate "
            "images that complement slide content."
        ),
        temperature=0.3,
        max_tokens=2048,
        tools=("media.search_images", "media.download_image"),
    ),
    "SlideRenderer": AgentConfig(
        model="",
        provider="none",
        system_prompt="",
        temperature=0.0,
        max_tokens=0,
        tools=("rendering.render_slide", "rendering.render_batch"),
    ),
    "QualityReviewer": AgentConfig(
        model="claude-opus-4-6",
        provider="anthropic",
        system_prompt=(
            "You are the QualityReviewer agent. You evaluate presentations against a "
            "comprehensive quality checklist covering design, content, and accessibility."
        ),
        temperature=0.2,
        max_tokens=8192,
        tools=("agent.ralph_loop.start",),
    ),
    "StyleEnforcer": AgentConfig(
        model="claude-sonnet-4-6",
        provider="anthropic",
        system_prompt=(
            "You are the StyleEnforcer agent. You verify that every slide conforms "
            "to the established style guide — colors, fonts, spacing, and branding."
        ),
        temperature=0.2,
        max_tokens=4096,
        tools=("style.validate",),
    ),
    "WebResearcher": AgentConfig(
        model="claude-sonnet-4-6",
        provider="anthropic",
        system_prompt=(
            "You are the WebResearcher agent. You gather facts, statistics, and "
            "references from the web to enrich presentation content."
        ),
        temperature=0.5,
        max_tokens=4096,
        tools=("web.search", "web.fetch"),
    ),
}

DEFAULT_PIPELINE_STAGES: list[PipelineStage] = [
    PipelineStage(name="RESEARCH", agents=("WebResearcher",), parallel=False),
    PipelineStage(
        name="PLANNING",
        agents=("OutlineArchitect", "StyleParser"),
        parallel=True,
    ),
    PipelineStage(
        name="CONTENT",
        agents=("ContentWriter", "PaletteDesigner", "FontSelector"),
        parallel=True,
    ),
    PipelineStage(
        name="ASSEMBLY",
        agents=("LayoutComposer", "InfographicBuilder", "ImageCurator"),
        parallel=True,
    ),
    PipelineStage(name="RENDERING", agents=("SlideRenderer",), parallel=False),
    PipelineStage(
        name="RALPH_LOOP",
        agents=("QualityReviewer", "StyleEnforcer"),
        parallel=False,
    ),
    PipelineStage(name="EXPORT", agents=("SlideRenderer",), parallel=False),
]

DEFAULT_PIPELINE_CONFIG = PipelineConfig(parallel_subagents=True, max_concurrent=8)

FIXER_MAP: dict[str, str] = {
    "color_consistency": "PaletteDesigner",
    "font_hierarchy": "FontSelector",
    "text_readability": "ContentWriter",
    "contrast_ratio": "PaletteDesigner",
    "layout_alignment": "LayoutComposer",
    "image_quality": "ImageCurator",
    "infographic_accuracy": "InfographicBuilder",
    "content_grammar": "ContentWriter",
    "content_tone": "ContentWriter",
    "slide_overflow": "LayoutComposer",
}
