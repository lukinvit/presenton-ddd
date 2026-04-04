"""Workspace manager — creates and manages per-presentation artifact directories."""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any

APP_DATA = os.getenv("PRESENTON_APP_DATA_DIR", "./app_data")


@dataclass
class PipelineState:
    presentation_id: str
    created_at: str
    current_stage: str = "INTAKE"
    mode: str = "from_scratch"  # from_scratch | from_existing
    stages: dict[str, dict] = field(default_factory=dict)
    quality_gates: dict[str, bool | None] = field(default_factory=dict)
    decisions: dict[str, str | None] = field(default_factory=dict)


class Workspace:
    """Manages a per-presentation workspace directory."""

    def __init__(self, presentation_id: str, base_dir: str | None = None):
        self.presentation_id = presentation_id
        self.base = Path(base_dir or APP_DATA) / "workspaces" / presentation_id

    def initialize(self) -> "Workspace":
        """Create workspace directory structure."""
        dirs = [
            "source", "source/references",
            "assets/images", "assets/fonts", "assets/icons", "assets/infographics",
            "preview",
            "slides",
            "output", "output/preview",
        ]
        for d in dirs:
            (self.base / d).mkdir(parents=True, exist_ok=True)

        # Initialize pipeline state
        state = PipelineState(
            presentation_id=self.presentation_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            stages={
                stage: {"status": "pending", "started_at": None, "completed_at": None, "artifact": None}
                for stage in ["INTAKE", "INGEST", "PARSE", "STRATEGY", "BASE", "CONTENT", "ASSETS", "ENRICHMENT", "RENDER_QA", "PACKAGE"]
            },
            quality_gates={
                "brief_complete": None, "files_ingested": None, "manifest_valid": None,
                "strategy_consistent": None, "contrast_accessible": None, "content_complete": None,
                "assets_resolved": None, "facts_verified": None, "no_overflow": None,
                "no_pdf_crop": None, "score_threshold": None, "human_approved": None, "package_complete": None,
            },
            decisions={
                "render_strategy": None, "needs_editability": None, "needs_pixel_perfect": None,
                "has_external_facts": None, "needs_speaker_notes": None, "output_format": None,
            },
        )
        self.save_state(state)
        return self

    # --- Artifact I/O ---

    def write_json(self, filename: str, data: Any) -> Path:
        path = self.base / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        return path

    def read_json(self, filename: str) -> Any:
        path = self.base / filename
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def write_text(self, filename: str, content: str) -> Path:
        path = self.base / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def read_text(self, filename: str) -> str | None:
        path = self.base / filename
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def write_bytes(self, filename: str, data: bytes) -> Path:
        path = self.base / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def file_exists(self, filename: str) -> bool:
        return (self.base / filename).exists()

    def list_files(self, directory: str) -> list[str]:
        d = self.base / directory
        if not d.exists():
            return []
        return [f.name for f in d.iterdir() if f.is_file()]

    # --- Pipeline State ---

    def save_state(self, state: PipelineState) -> None:
        self.write_json("pipeline_state.json", asdict(state))

    def load_state(self) -> PipelineState | None:
        data = self.read_json("pipeline_state.json")
        if data is None:
            return None
        return PipelineState(**data)

    def update_stage(self, stage: str, status: str, artifact: str | None = None) -> PipelineState:
        state = self.load_state()
        if state is None:
            raise ValueError("Workspace not initialized")
        now = datetime.now(timezone.utc).isoformat()
        stage_data = state.stages.get(stage, {})
        stage_data["status"] = status
        if status == "running" and not stage_data.get("started_at"):
            stage_data["started_at"] = now
        if status == "completed":
            stage_data["completed_at"] = now
        if artifact:
            stage_data["artifact"] = artifact
        state.stages[stage] = stage_data
        state.current_stage = stage
        self.save_state(state)
        return state

    def set_gate(self, gate: str, passed: bool) -> None:
        state = self.load_state()
        if state:
            state.quality_gates[gate] = passed
            self.save_state(state)

    def set_decision(self, key: str, value: str) -> None:
        state = self.load_state()
        if state:
            state.decisions[key] = value
            self.save_state(state)

    def check_hard_gates(self, stage: str) -> list[str]:
        """Return list of failed HARD gates for a stage."""
        state = self.load_state()
        if not state:
            return ["workspace_not_initialized"]

        gate_map = {
            "INTAKE": ["brief_complete"],
            "INGEST": ["files_ingested"],
            "PARSE": ["manifest_valid"],
            "STRATEGY": ["strategy_consistent"],
            "BASE": ["contrast_accessible"],
            "CONTENT": ["content_complete"],
            "ASSETS": ["assets_resolved"],
            "RENDER_QA": ["no_overflow", "no_pdf_crop", "score_threshold", "human_approved"],
            "PACKAGE": ["package_complete"],
        }

        gates = gate_map.get(stage, [])
        return [g for g in gates if state.quality_gates.get(g) is False]
