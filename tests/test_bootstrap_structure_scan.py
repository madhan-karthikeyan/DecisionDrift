from __future__ import annotations

import tempfile
from pathlib import Path

from decisiondrift.bootstrap.structure_scan import EXCLUDED_DIRS, scan_repo

HMS_V2 = Path(__file__).parent.parent / "repos" / "hospital-management-system-V2"


class TestStructureScan:
    def test_scans_top_level_dirs(self):
        structure = scan_repo(HMS_V2)
        assert "backend" in structure.top_level_dirs
        assert "frontend" in structure.top_level_dirs
        assert "docs" in structure.top_level_dirs
        assert "migrations" in structure.top_level_dirs

    def test_detects_indicator_files(self):
        structure = scan_repo(HMS_V2)
        indicators = {f.split("/")[-1] for f in structure.indicator_files}
        assert "requirements.txt" in indicators
        assert "manage.py" in indicators
        assert "alembic.ini" in indicators or "migrations/alembic.ini" in structure.indicator_files
        assert "celery_worker.py" in indicators or "backend/celery_worker.py" in structure.indicator_files

    def test_excludes_noise_dirs(self):
        for d in EXCLUDED_DIRS:
            assert d not in HMS_V2.name, f"test assumes {d} is not the repo root"
        structure = scan_repo(HMS_V2)
        for d in structure.dirs:
            parts = Path(d).parts
            for part in parts:
                assert part not in EXCLUDED_DIRS, f"{d} contains excluded dir {part}"

    def test_excludes_migrations_versions(self):
        structure = scan_repo(HMS_V2)
        for d in structure.dirs:
            assert "migrations/versions" not in d

    def test_includes_migrations_root(self):
        structure = scan_repo(HMS_V2)
        dir_names = set(structure.dirs)
        assert "migrations" in dir_names or any("migrations" in d for d in dir_names)

    def test_max_depth_respected(self):
        structure = scan_repo(HMS_V2, max_depth=2)
        for d in structure.dirs:
            assert len(Path(d).parts) <= 2

    def test_max_depth_configurable(self):
        deep = scan_repo(HMS_V2, max_depth=4)
        shallow = scan_repo(HMS_V2, max_depth=1)
        assert len(deep.dirs) >= len(shallow.dirs)

    def test_has_file_method(self):
        structure = scan_repo(HMS_V2)
        assert structure.has_file("requirements.txt")
        assert structure.has_file("manage.py")

    def test_has_subdir_method(self):
        structure = scan_repo(HMS_V2)
        assert structure.has_subdir("backend", "api")
        assert structure.has_subdir("frontend")

    def test_empty_dir_returns_no_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            structure = scan_repo(tmp)
            assert structure.dirs == []
            assert structure.files == []

    def test_non_existent_dir_raises_error(self):
        import pytest

        with pytest.raises(NotADirectoryError):
            scan_repo("/nonexistent/path")

    def test_skips_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            real_dir = Path(tmp) / "real"
            real_dir.mkdir()
            (real_dir / "real_file.py").touch()
            link = Path(tmp) / "link_to_real"
            link.symlink_to(real_dir, target_is_directory=True)
            structure = scan_repo(tmp)
            assert "link_to_real" not in structure.dirs
