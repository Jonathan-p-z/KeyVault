from __future__ import annotations

from pathlib import Path

import backup_app.core as core


def test_mirror_delete_removes_extraneous_files(tmp_path: Path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()

    (src / "a.txt").write_text("A", encoding="utf-8")
    (src / "b.txt").write_text("B", encoding="utf-8")
    (dst / "old.txt").write_text("OLD", encoding="utf-8")

    result = core.run_backup(src, dst, mirror_delete=True, log_path=tmp_path / "backup.log")

    assert result.errors == []
    assert result.copied_files == 2
    assert result.deleted_files == 1
    assert not (dst / "old.txt").exists()


def test_mirror_delete_does_not_delete_when_copy_errors(tmp_path: Path, monkeypatch):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()

    (src / "a.txt").write_text("A", encoding="utf-8")
    (dst / "old.txt").write_text("OLD", encoding="utf-8")

    def boom(_src: Path, _dst: Path, *, retries: int = 3, delay_s: float = 0.25) -> None:
        raise OSError("simulated copy failure")

    monkeypatch.setattr(core, "_copy_with_retries", boom)

    result = core.run_backup(src, dst, mirror_delete=True, log_path=tmp_path / "backup.log")

    assert result.errors, "expected copy errors"
    # Safety: no deletion when errors present.
    assert (dst / "old.txt").exists()
