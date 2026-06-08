import importlib.util
import sys
from pathlib import Path

import nbformat


def load_builder_module():
    path = Path("apps/notebooks/studies/tesla_valuation/build_notebooks.py")
    spec = importlib.util.spec_from_file_location("tesla_valuation_build_notebooks", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tesla_notebook_specs_cover_required_outputs() -> None:
    builder = load_builder_module()
    titles = [spec.title for spec in builder.NOTEBOOK_SPECS]

    assert "05 DCF SOTP Sensitivities and Memo" in titles
    assert len(builder.NOTEBOOK_SPECS) == 6


def test_checked_in_tesla_notebooks_are_valid() -> None:
    notebook_dir = Path("apps/notebooks/studies/tesla_valuation")
    paths = sorted(notebook_dir.glob("*.ipynb"))

    assert len(paths) == 6
    for path in paths:
        notebook = nbformat.read(path, as_version=4)
        assert notebook.cells
        assert notebook.cells[0].cell_type == "markdown"
