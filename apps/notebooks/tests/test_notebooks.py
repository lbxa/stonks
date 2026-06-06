from pathlib import Path


def test_studies_directory_exists() -> None:
    assert Path("apps/notebooks/studies").exists()
