from pathlib import Path

import pytest

from od_platform.cli import reset_project
from od_platform.common.paths import (
    LOGGING_DIR,
    META_DIR,
    META_LOGGING_DIR,
    PRETRAINED_MODELS_DIR,
    RAW_DATA_DIR,
    get_dirs_to_initialize,
    get_paths_to_reset,
    is_protected,
)


def test_reset_targets_include_runtime_data_but_protect_inputs_and_audit_logs() -> None:
    paths = get_paths_to_reset()

    assert LOGGING_DIR in paths
    assert RAW_DATA_DIR not in paths
    assert PRETRAINED_MODELS_DIR not in paths
    assert META_DIR not in paths
    assert META_LOGGING_DIR not in paths
    assert META_LOGGING_DIR in get_dirs_to_initialize()
    assert is_protected(META_DIR)
    assert is_protected(META_LOGGING_DIR)


def test_scan_targets_counts_files_and_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    standalone_file = tmp_path / "model.pt"
    standalone_file.write_bytes(b"weights")
    runtime_dir = tmp_path / "run"
    runtime_dir.mkdir()
    (runtime_dir / "metrics.txt").write_text("loss", encoding="utf-8")

    monkeypatch.setattr(reset_project, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        reset_project,
        "get_paths_to_reset",
        lambda: [standalone_file, runtime_dir],
    )
    monkeypatch.setattr(reset_project, "is_protected", lambda _: False)

    deletable, skipped = reset_project._scan_targets()

    assert skipped == []
    assert deletable == [(standalone_file, 1, 7), (runtime_dir, 1, 4)]


def test_delete_one_handles_files_and_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    standalone_file = tmp_path / "model.pt"
    standalone_file.write_text("weights", encoding="utf-8")
    runtime_dir = tmp_path / "run"
    runtime_dir.mkdir()
    (runtime_dir / "metrics.txt").write_text("loss", encoding="utf-8")

    monkeypatch.setattr(reset_project, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(reset_project, "is_protected", lambda _: False)

    assert reset_project._delete_one(standalone_file, 1, 2, 1, 7) is None
    assert reset_project._delete_one(runtime_dir, 2, 2, 1, 4) is None
    assert not standalone_file.exists()
    assert not runtime_dir.exists()


def test_delete_one_rejects_protected_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protected_dir = tmp_path / "protected"
    protected_dir.mkdir()
    (protected_dir / "keep.txt").write_text("keep", encoding="utf-8")

    monkeypatch.setattr(reset_project, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(reset_project, "is_protected", lambda _: True)

    assert reset_project._delete_one(protected_dir, 1, 1, 1, 4) == "受保护目录"
    assert (protected_dir / "keep.txt").exists()
