"""Finding and loading recipes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CATEGORIES: dict[str, str] = {
    "routing-switching": "Routing & switching",
    "enterprise": "Enterprise designs",
    "security": "Security",
}

# CML node definitions that don't count toward the node license.
UNLICENSED_NODE_DEFINITIONS = frozenset({"external_connector", "unmanaged_switch"})

# (tier, maximum licensed nodes); None means no upper bound.
LICENSE_TIERS: list[tuple[str, int | None]] = [
    ("free", 5),
    ("personal", 20),
    ("personal-plus", 40),
    ("enterprise", None),
]


class RecipeError(Exception):
    """A recipe file that can't be read at all."""


@dataclass(frozen=True)
class Issue:
    level: str  # "error" or "warning"
    where: str  # recipe id, or a path when there is no id
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper()} {self.where}: {self.message}"


class _Loader(yaml.SafeLoader):
    """SafeLoader that keeps dates as strings, so they validate as JSON strings."""


_Loader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_yaml(text: str) -> Any:
    return yaml.load(text, Loader=_Loader)


@dataclass(frozen=True)
class Recipe:
    category: str
    path: Path
    data: dict[str, Any]

    @property
    def id(self) -> str:
        return self.path.name

    @property
    def version(self) -> str:
        return str(self.data.get("version", ""))

    @property
    def nodes(self) -> list[dict[str, Any]]:
        return self.data.get("topology", {}).get("nodes", [])

    def licensed_node_count(self) -> int:
        return sum(
            1 for node in self.nodes if node.get("node_definition") not in UNLICENSED_NODE_DEFINITIONS
        )

    def license_tier(self) -> str:
        count = self.licensed_node_count()
        for tier, limit in LICENSE_TIERS:
            if limit is None or count <= limit:
                return tier
        raise AssertionError("unreachable")


def find_root(start: Path | None = None) -> Path:
    """Walk up from `start` to the folder holding `recipes/` and `schema/`."""
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "recipes").is_dir() and (candidate / "schema").is_dir():
            return candidate
    raise RecipeError(f"no cookbook found at or above {here} (looking for recipes/ and schema/)")


def recipe_dirs(root: Path) -> list[Path]:
    """Every folder at recipes/<category>/<id>/, sorted, whether or not it is valid."""
    found = []
    for category_dir in sorted(p for p in (root / "recipes").iterdir() if p.is_dir()):
        found.extend(sorted(p for p in category_dir.iterdir() if p.is_dir()))
    return found


def load_recipe(path: Path) -> Recipe:
    recipe_file = path / "recipe.yaml"
    if not recipe_file.is_file():
        raise RecipeError(f"{path}: missing recipe.yaml")
    try:
        data = load_yaml(recipe_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RecipeError(f"{recipe_file}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise RecipeError(f"{recipe_file}: expected a mapping at the top level")
    return Recipe(category=path.parent.name, path=path, data=data)


def load_all(root: Path) -> list[Recipe]:
    """Load every recipe that can be parsed; use validate.validate_repo to report the rest."""
    recipes = []
    for path in recipe_dirs(root):
        try:
            recipes.append(load_recipe(path))
        except RecipeError:
            continue
    return recipes


def find_recipe(root: Path, recipe_id: str) -> Recipe:
    for path in recipe_dirs(root):
        if path.name == recipe_id:
            return load_recipe(path)
    raise RecipeError(f"no recipe with id {recipe_id!r}")
