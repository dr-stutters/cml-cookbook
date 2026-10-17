import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from cml_cookbook.recipes import load_yaml

REPO = Path(__file__).resolve().parents[1]
OSPF = Path("recipes/routing-switching/ospf-multi-area")


@pytest.fixture
def cookbook(tmp_path: Path) -> Path:
    """A copy of this repo's schema, templates and recipes, with a minimal README."""
    for name in ("schema", "templates", "recipes"):
        shutil.copytree(REPO / name, tmp_path / name)
    (tmp_path / "README.md").write_text("# Test\n\n<!-- catalog:start -->\n<!-- catalog:end -->\n")
    return tmp_path


@pytest.fixture
def edit_recipe() -> Callable[[Path, Callable[[dict[str, Any]], None]], None]:
    """Load recipe.yaml under `folder`, let `change` mutate it, and write it back."""

    def edit(folder: Path, change: Callable[[dict[str, Any]], None]) -> None:
        recipe_file = folder / "recipe.yaml"
        data = load_yaml(recipe_file.read_text())
        change(data)
        recipe_file.write_text(yaml.safe_dump(data, sort_keys=False))

    return edit


@pytest.fixture
def git_cookbook(cookbook: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """`cookbook` as a git repo with one commit, tagged `base`, isolated from the user's git config."""
    empty = tmp_path / "gitconfig"
    empty.write_text("")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for key in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{key}_NAME", "Test")
        monkeypatch.setenv(f"GIT_{key}_EMAIL", "test@example.com")
    run_git(cookbook, "init", "-q", "-b", "main")
    commit_all(cookbook, "base")
    run_git(cookbook, "tag", "base")
    return cookbook


def run_git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def commit_all(root: Path, message: str) -> None:
    run_git(root, "add", "-A")
    run_git(root, "commit", "-q", "-m", message)
