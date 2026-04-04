"""Unit tests for the Workspace manager."""
import pytest
import tempfile
from pathlib import Path

from domains.agent.infrastructure.workspace import Workspace, PipelineState


@pytest.fixture
def tmp_workspace(tmp_path):
    ws = Workspace("test-presentation-id", base_dir=str(tmp_path))
    ws.initialize()
    return ws


def test_initialize_creates_directories(tmp_path):
    ws = Workspace("test-id", base_dir=str(tmp_path))
    ws.initialize()

    expected_dirs = [
        "source", "source/references",
        "assets/images", "assets/fonts", "assets/icons", "assets/infographics",
        "preview", "slides", "output", "output/preview",
    ]
    for d in expected_dirs:
        assert (ws.base / d).is_dir(), f"Missing directory: {d}"


def test_initialize_creates_pipeline_state(tmp_workspace):
    state = tmp_workspace.load_state()
    assert state is not None
    assert state.presentation_id == "test-presentation-id"
    assert state.current_stage == "INTAKE"
    assert state.mode == "from_scratch"
    assert len(state.stages) == 10
    assert all(s["status"] == "pending" for s in state.stages.values())


def test_write_json_read_json_roundtrip(tmp_workspace):
    data = {"key": "value", "nested": {"list": [1, 2, 3]}}
    tmp_workspace.write_json("test_artifact.json", data)
    result = tmp_workspace.read_json("test_artifact.json")
    assert result == data


def test_read_json_returns_none_for_missing_file(tmp_workspace):
    result = tmp_workspace.read_json("nonexistent.json")
    assert result is None


def test_write_text_read_text_roundtrip(tmp_workspace):
    content = "Hello, world!\nLine two."
    tmp_workspace.write_text("notes.txt", content)
    result = tmp_workspace.read_text("notes.txt")
    assert result == content


def test_read_text_returns_none_for_missing_file(tmp_workspace):
    result = tmp_workspace.read_text("nonexistent.txt")
    assert result is None


def test_file_exists(tmp_workspace):
    assert not tmp_workspace.file_exists("new_file.txt")
    tmp_workspace.write_text("new_file.txt", "data")
    assert tmp_workspace.file_exists("new_file.txt")


def test_list_files(tmp_workspace):
    tmp_workspace.write_text("slides/slide1.html", "<html/>")
    tmp_workspace.write_text("slides/slide2.html", "<html/>")
    files = tmp_workspace.list_files("slides")
    assert set(files) == {"slide1.html", "slide2.html"}


def test_update_stage_changes_status(tmp_workspace):
    state = tmp_workspace.update_stage("INTAKE", "running")
    assert state.stages["INTAKE"]["status"] == "running"
    assert state.stages["INTAKE"]["started_at"] is not None
    assert state.current_stage == "INTAKE"


def test_update_stage_completed_sets_timestamps(tmp_workspace):
    tmp_workspace.update_stage("PARSE", "running")
    state = tmp_workspace.update_stage("PARSE", "completed", artifact="source/manifest.json")
    assert state.stages["PARSE"]["status"] == "completed"
    assert state.stages["PARSE"]["completed_at"] is not None
    assert state.stages["PARSE"]["artifact"] == "source/manifest.json"


def test_update_stage_persists_to_disk(tmp_workspace):
    tmp_workspace.update_stage("STRATEGY", "completed")
    # Re-load from disk
    reloaded = tmp_workspace.load_state()
    assert reloaded.stages["STRATEGY"]["status"] == "completed"


def test_update_stage_raises_if_not_initialized(tmp_path):
    ws = Workspace("uninitialized-id", base_dir=str(tmp_path))
    with pytest.raises(ValueError, match="Workspace not initialized"):
        ws.update_stage("INTAKE", "running")


def test_set_gate_and_check_hard_gates_pass(tmp_workspace):
    tmp_workspace.set_gate("brief_complete", True)
    failed = tmp_workspace.check_hard_gates("INTAKE")
    assert failed == []


def test_set_gate_and_check_hard_gates_fail(tmp_workspace):
    tmp_workspace.set_gate("brief_complete", False)
    failed = tmp_workspace.check_hard_gates("INTAKE")
    assert "brief_complete" in failed


def test_check_hard_gates_none_not_failed(tmp_workspace):
    # Gates that are None (not yet evaluated) should NOT count as failed
    failed = tmp_workspace.check_hard_gates("RENDER_QA")
    assert failed == []


def test_check_hard_gates_multiple_failures(tmp_workspace):
    tmp_workspace.set_gate("no_overflow", False)
    tmp_workspace.set_gate("score_threshold", False)
    tmp_workspace.set_gate("human_approved", True)
    failed = tmp_workspace.check_hard_gates("RENDER_QA")
    assert "no_overflow" in failed
    assert "score_threshold" in failed
    assert "human_approved" not in failed


def test_check_hard_gates_unknown_stage(tmp_workspace):
    failed = tmp_workspace.check_hard_gates("UNKNOWN_STAGE")
    assert failed == []


def test_set_decision_persists(tmp_workspace):
    tmp_workspace.set_decision("output_format", "pptx")
    state = tmp_workspace.load_state()
    assert state.decisions["output_format"] == "pptx"
