"""`cookbook new`: start a recipe from templates/recipe/."""

from __future__ import annotations

import json
import re
import shutil
from datetime import date
from pathlib import Path

from cml_cookbook.recipes import CATEGORIES, RecipeError, recipe_dirs

SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
HANDLE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")


def new_recipe(root: Path, category: str, recipe_id: str, title: str, maintainer: str, today: date | None = None) -> Path:
    if category not in CATEGORIES:
        raise RecipeError(f"unknown category {category!r} (expected one of: {', '.join(CATEGORIES)})")
    if not SLUG.match(recipe_id) or len(recipe_id) > 50:
        raise RecipeError(f"{recipe_id!r} isn't a valid id: use lowercase kebab-case, at most 50 characters")
    if not HANDLE.match(maintainer):
        raise RecipeError(f"{maintainer!r} isn't a GitHub handle")
    for existing in recipe_dirs(root):
        if existing.name == recipe_id:
            raise RecipeError(f"id {recipe_id!r} is already used by {existing.relative_to(root).as_posix()}")

    template = root / "templates" / "recipe"
    if not template.is_dir():
        raise RecipeError("templates/recipe/ is missing")
    target = root / "recipes" / category / recipe_id
    shutil.copytree(template, target)

    tokens = {
        # JSON strings are valid double-quoted YAML scalars, so any title is safe in recipe.yaml.
        "__RECIPE_TITLE_YAML__": json.dumps(title),
        "__RECIPE_TITLE__": title,
        "__RECIPE_ID__": recipe_id,
        "__MAINTAINER__": maintainer,
        "__TODAY__": (today or date.today()).isoformat(),
    }
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for token, value in tokens.items():
            text = text.replace(token, value)
        path.write_text(text, encoding="utf-8")
    return target
