from datetime import date

import pytest

from cml_cookbook.recipes import RecipeError, load_recipe
from cml_cookbook.scaffold import new_recipe
from cml_cookbook.validate import validate_repo


def test_new_recipe_is_valid(cookbook):
    path = new_recipe(cookbook, "security", "dot1x-access-ise", "802.1X: access with ISE", "dr-stutters", date(2026, 10, 16))
    recipe = load_recipe(path)
    assert recipe.data["title"] == "802.1X: access with ISE"
    assert recipe.data["maintainers"] == ["dr-stutters"]
    assert "## [0.1.0] - 2026-10-16" in (path / "CHANGELOG.md").read_text()
    assert (path / "README.md").read_text().startswith("# 802.1X: access with ISE\n")

    _, issues = validate_repo(cookbook, ["dot1x-access-ise"])
    assert [i for i in issues if i.level == "error"] == []
    assert any("TODO" in i.message for i in issues if i.level == "warning")


@pytest.mark.parametrize(
    ("category", "recipe_id", "maintainer", "problem"),
    [
        ("misc", "x-lab", "me", "unknown category"),
        ("enterprise", "Bad_Id", "me", "isn't a valid id"),
        ("enterprise", "ospf-multi-area", "me", "already used"),
        ("enterprise", "x-lab", "not a handle", "isn't a GitHub handle"),
    ],
)
def test_new_recipe_rejects(cookbook, category, recipe_id, maintainer, problem):
    with pytest.raises(RecipeError, match=problem):
        new_recipe(cookbook, category, recipe_id, "Title", maintainer)
