from pathlib import Path

import pytest
from conftest import OSPF

from cml_cookbook.catalog import CatalogError, recipe_entry, write_catalog
from cml_cookbook.recipes import Recipe, load_all, load_recipe, load_yaml


def test_write_then_check_is_clean(cookbook):
    recipes = load_all(cookbook)
    written = write_catalog(recipes, cookbook)
    assert cookbook / "index.yaml" in written
    assert write_catalog(recipes, cookbook, check=True) == []


def test_check_finds_drift(cookbook, edit_recipe):
    write_catalog(load_all(cookbook), cookbook)
    edit_recipe(cookbook / OSPF, lambda d: d.update(title="OSPF in three areas"))
    stale = write_catalog(load_all(cookbook), cookbook, check=True)
    assert cookbook / "index.yaml" in stale
    assert cookbook / "README.md" in stale
    assert cookbook / "recipes" / "routing-switching" / "README.md" in stale


def test_tables_link_to_recipes(cookbook):
    write_catalog(load_all(cookbook), cookbook)
    assert "(recipes/routing-switching/ospf-multi-area/)" in (cookbook / "README.md").read_text()
    category = (cookbook / "recipes" / "routing-switching" / "README.md").read_text()
    assert "(ospf-multi-area/)" in category
    assert "_No recipes yet._" in (cookbook / "recipes" / "security" / "README.md").read_text()


def test_index_entry(cookbook):
    entry = recipe_entry(load_recipe(cookbook / OSPF), cookbook)
    assert entry["nodes"] == 5
    assert entry["license_tier"] == "free"
    assert entry["refplat_only"] is True
    assert entry["node_definitions"] == ["iol-xe"]
    assert entry["last_tested"] is None


def test_index_is_valid_yaml(cookbook):
    write_catalog(load_all(cookbook), cookbook)
    index = load_yaml((cookbook / "index.yaml").read_text())
    assert [r["id"] for r in index["recipes"]] == ["ospf-multi-area"]


@pytest.mark.parametrize(
    ("routers", "tier"),
    [(1, "free"), (5, "free"), (6, "personal"), (20, "personal"), (21, "personal-plus"), (41, "enterprise")],
)
def test_license_tiers(routers, tier):
    nodes = [{"label": f"r{i}", "node_definition": "iol-xe"} for i in range(routers)]
    nodes += [{"label": "ext", "node_definition": "external_connector"}]
    nodes += [{"label": "ums", "node_definition": "unmanaged_switch"}]
    recipe = Recipe("routing-switching", Path("x"), {"topology": {"nodes": nodes}})
    assert recipe.licensed_node_count() == routers
    assert recipe.license_tier() == tier


def test_readme_needs_markers(cookbook):
    (cookbook / "README.md").write_text("# No markers\n")
    with pytest.raises(CatalogError):
        write_catalog(load_all(cookbook), cookbook)
