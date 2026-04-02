"""Style domain services."""

from __future__ import annotations

from dataclasses import dataclass

from .entities import StyleProfile

# ---------------------------------------------------------------------------
# StyleToCSS
# ---------------------------------------------------------------------------


@dataclass
class StyleToCSS:
    """Convert a StyleProfile to CSS custom properties or Tailwind theme config."""

    def to_css_variables(self, profile: StyleProfile) -> str:
        """Return a CSS :root { ... } block with all custom properties."""
        lines: list[str] = [":root {"]

        if profile.colors:
            c = profile.colors
            lines.append(f"  --color-primary: {c.primary};")
            lines.append(f"  --color-secondary: {c.secondary};")
            lines.append(f"  --color-background: {c.background};")
            lines.append(f"  --color-text: {c.text};")
            for i, acc in enumerate(c.accent):
                lines.append(f"  --color-accent-{i + 1}: {acc};")

        if profile.typography:
            t = profile.typography
            lines.append(f"  --font-heading: '{t.heading_font}', sans-serif;")
            lines.append(f"  --font-body: '{t.body_font}', sans-serif;")
            for key, val in sorted(t.sizes_dict.items()):
                lines.append(f"  --font-size-{key}: {val};")

        if profile.layout:
            lo = profile.layout
            lines.append(f"  --layout-margin: {lo.margin};")
            lines.append(f"  --layout-padding: {lo.padding};")
            lines.append(f"  --layout-columns: {lo.alignment_grid};")
            lines.append(f"  --layout-max-width: {lo.max_content_width};")

        if profile.spacing:
            sp = profile.spacing
            lines.append(f"  --spacing-line-height: {sp.line_height};")
            lines.append(f"  --spacing-paragraph-gap: {sp.paragraph_gap};")
            lines.append(f"  --spacing-element-gap: {sp.element_gap};")

        lines.append("}")
        return "\n".join(lines)

    def to_tailwind_theme(self, profile: StyleProfile) -> dict:
        """Return a Tailwind CSS theme extension dict."""
        theme: dict = {"extend": {}}

        if profile.colors:
            c = profile.colors
            theme["extend"]["colors"] = {
                "primary": c.primary,
                "secondary": c.secondary,
                "background": c.background,
                "text-color": c.text,
                **{f"accent-{i + 1}": acc for i, acc in enumerate(c.accent)},
            }

        if profile.typography:
            t = profile.typography
            theme["extend"]["fontFamily"] = {
                "heading": [t.heading_font, "sans-serif"],
                "body": [t.body_font, "sans-serif"],
            }
            theme["extend"]["fontSize"] = {k: v for k, v in t.sizes_dict.items()}

        if profile.layout:
            lo = profile.layout
            theme["extend"]["maxWidth"] = {"content": lo.max_content_width}
            theme["extend"]["spacing"] = {
                "layout-margin": lo.margin,
                "layout-padding": lo.padding,
            }

        if profile.spacing:
            sp = profile.spacing
            theme["extend"]["lineHeight"] = {"content": sp.line_height}
            existing_spacing = theme["extend"].get("spacing", {})
            existing_spacing["paragraph-gap"] = sp.paragraph_gap
            existing_spacing["element-gap"] = sp.element_gap
            theme["extend"]["spacing"] = existing_spacing

        return theme


# ---------------------------------------------------------------------------
# StyleValidationService
# ---------------------------------------------------------------------------


@dataclass
class StyleValidationService:
    """Validate rendered presentation data against a StyleProfile.

    Returns a checklist suitable for the Ralph Loop review step.
    """

    def validate(self, style_profile: StyleProfile, rendered_data: dict) -> list[dict]:
        """Compare rendered_data against style_profile, returning checklist items.

        Args:
            style_profile: The reference style profile.
            rendered_data: Dict with optional keys:
                - colors (list[str]): hex colors found in rendered output
                - fonts (list[str]): font names found in rendered output
                - bg_color (str): detected background color

        Returns:
            list of {"criterion": str, "passed": bool, "details": str}
        """
        results: list[dict] = []

        # --- Color checks ---
        if style_profile.colors:
            palette = style_profile.colors
            allowed_colors = {
                palette.primary,
                palette.secondary,
                palette.background,
                palette.text,
                *palette.accent,
            }
            rendered_colors: list[str] = [c.upper() for c in rendered_data.get("colors", [])]
            unknown_colors = [c for c in rendered_colors if c not in allowed_colors]
            results.append(
                {
                    "criterion": "color_consistency",
                    "passed": len(unknown_colors) == 0,
                    "details": (
                        "All colors are within the style palette."
                        if not unknown_colors
                        else f"Unknown colors detected: {', '.join(unknown_colors)}"
                    ),
                }
            )

            bg = rendered_data.get("bg_color", "").upper()
            results.append(
                {
                    "criterion": "background_color",
                    "passed": not bg or bg == palette.background,
                    "details": (
                        "Background color matches the style profile."
                        if not bg or bg == palette.background
                        else f"Background {bg!r} does not match expected {palette.background!r}"
                    ),
                }
            )

        # --- Font checks ---
        if style_profile.typography:
            typo = style_profile.typography
            allowed_fonts = {typo.heading_font.lower(), typo.body_font.lower()}
            rendered_fonts: list[str] = [f.lower() for f in rendered_data.get("fonts", [])]
            unknown_fonts = [f for f in rendered_fonts if f not in allowed_fonts]
            results.append(
                {
                    "criterion": "font_consistency",
                    "passed": len(unknown_fonts) == 0,
                    "details": (
                        "All fonts are within the style typography."
                        if not unknown_fonts
                        else f"Unknown fonts detected: {', '.join(unknown_fonts)}"
                    ),
                }
            )

        # --- Profile completeness ---
        results.append(
            {
                "criterion": "profile_complete",
                "passed": style_profile.is_complete(),
                "details": (
                    "Style profile is fully defined."
                    if style_profile.is_complete()
                    else "Style profile is missing one or more sections (colors/typography/layout/spacing)."
                ),
            }
        )

        return results


# ---------------------------------------------------------------------------
# StyleExtractionService — stub for PPTX/PDF parsing
# ---------------------------------------------------------------------------


@dataclass
class StyleExtractionService:
    """Extract a StyleProfile from a file (PPTX or PDF).

    NOTE: Real parser implementations (python-pptx / pdfplumber) will be
    added in a follow-up integration pass.  This service currently returns
    a placeholder profile so the command/application layer can be fully
    exercised in tests.
    """

    def extract_from_file(self, file_path: str, name: str) -> dict:
        """Return a raw style dict extracted from the given file path.

        Raises:
            FileNotFoundError: if the file does not exist.
            ValueError: if the file type is unsupported.
        """
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[-1].lower()
        if ext not in {".pptx", ".pdf"}:
            raise ValueError(f"Unsupported file type: {ext!r}. Expected .pptx or .pdf.")

        # Stub — real parsing delegated to future integration
        return {
            "source": "file",
            "colors": {
                "primary": "#1A1A1A",
                "secondary": "#555555",
                "accent": ["#0066CC"],
                "background": "#FFFFFF",
                "text": "#1A1A1A",
            },
            "typography": {
                "heading_font": "Arial",
                "body_font": "Arial",
                "sizes": {"h1": "36px", "h2": "28px", "h3": "22px", "body": "16px"},
            },
            "layout": {
                "margin": "40px",
                "padding": "24px",
                "alignment_grid": 12,
                "max_content_width": "1200px",
            },
            "spacing": {
                "line_height": "1.5",
                "paragraph_gap": "20px",
                "element_gap": "16px",
            },
        }

    def extract_from_url(self, url: str, name: str) -> dict:
        """Return a raw style dict extracted via vision from a URL.

        NOTE: Vision-based extraction will be implemented in a future pass.
        """
        return {
            "source": "url",
            "colors": {
                "primary": "#1A1A1A",
                "secondary": "#555555",
                "accent": [],
                "background": "#FFFFFF",
                "text": "#1A1A1A",
            },
            "typography": {
                "heading_font": "sans-serif",
                "body_font": "sans-serif",
                "sizes": {"h1": "36px", "h2": "28px", "h3": "22px", "body": "16px"},
            },
            "layout": {
                "margin": "40px",
                "padding": "24px",
                "alignment_grid": 12,
                "max_content_width": "1200px",
            },
            "spacing": {
                "line_height": "1.5",
                "paragraph_gap": "20px",
                "element_gap": "16px",
            },
        }
