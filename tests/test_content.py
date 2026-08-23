"""Tests for YAML content loading."""

from pathlib import Path


def test_bio_meta_yaml_loads():
    """bio_meta.yaml must have an emails key with at least one entry."""
    import yaml

    path = Path(__file__).resolve().parent.parent / "coltrane" / "content" / "bio_meta.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "emails" in data
    assert len(data["emails"]) >= 1


def test_bio_skills_yaml_loads():
    """bio_skills.yaml must have a skills key with at least one entry."""
    import yaml

    path = Path(__file__).resolve().parent.parent / "coltrane" / "content" / "bio_skills.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "skills" in data
    assert len(data["skills"]) >= 1


def test_bio_md_exists_and_non_empty():
    """bio.md must exist and contain content."""
    path = Path(__file__).resolve().parent.parent / "coltrane" / "content" / "bio.md"
    content = path.read_text(encoding="utf-8")
    assert len(content) > 100
