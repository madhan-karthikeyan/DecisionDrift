from __future__ import annotations

from pathlib import Path

from decisiondrift.bootstrap.bootstrapper import bootstrap


class TestBootstrapperV2:
    def test_bootstrap_empty_repo(self, tmp_path: Path):
        """Empty repo should produce no findings."""
        result = bootstrap(tmp_path, adr_dir=tmp_path / "docs/adr", dry_run=True)
        assert len(result) == 0

    def test_bootstrap_with_fastapi(self, tmp_path: Path):
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
        (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
        (tmp_path / "Dockerfile").write_text("FROM python")
        result = bootstrap(tmp_path, adr_dir=tmp_path / "docs/adr", dry_run=True)
        assert len(result) > 0
        adr_names = [s.adr.title for s in result]
        assert any("FastAPI" in n for n in adr_names)
        assert not any("Docker" in n for n in adr_names)

    def test_bootstrap_apply_writes_files(self, tmp_path: Path):
        adr_dir = tmp_path / "docs" / "adr"
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
        (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
        bootstrap(tmp_path, adr_dir=adr_dir, dry_run=False)
        written = list(adr_dir.glob("*.md"))
        assert len(written) > 0
        content = written[0].read_text()
        assert "---" in content  # frontmatter

    def test_bootstrap_dedup_existing_adrs(self, tmp_path: Path):
        """If an ADR already exists for a technology, don't suggest it again."""
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "ADR-0001.md").write_text(
            "---\nid: ADR-0001\ntitle: Use FastAPI for Async HTTP Services\nstatus: accepted\nseverity: high\n---\n"
        )
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
        (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
        result = bootstrap(tmp_path, adr_dir=adr_dir, dry_run=True)
        # Should not suggest FastAPI again
        assert not any("FastAPI" in s.adr.title for s in result)
