from cml_cookbook.cli import main


def run(cookbook, *args):
    return main(["--root", str(cookbook), *args])


def test_validate(cookbook, capsys):
    assert run(cookbook, "validate") == 0
    assert "1 recipe(s) checked: 0 error(s)" in capsys.readouterr().out


def test_validate_unknown_id(cookbook):
    assert run(cookbook, "validate", "no-such-recipe") == 1


def test_index_then_check(cookbook):
    assert run(cookbook, "index", "--check") == 1
    assert run(cookbook, "index") == 0
    assert run(cookbook, "index", "--check") == 0


def test_index_refuses_invalid_recipes(cookbook):
    (cookbook / "recipes" / "routing-switching" / "ospf-multi-area" / "README.md").unlink()
    assert run(cookbook, "index") == 1
    assert not (cookbook / "index.yaml").exists()


def test_new(cookbook):
    assert run(cookbook, "new", "enterprise", "campus-3-tier", "--title", "Campus 3-tier", "--maintainer", "me") == 0
    assert (cookbook / "recipes" / "enterprise" / "campus-3-tier" / "recipe.yaml").is_file()


def test_check_is_not_implemented(cookbook, capsys):
    assert run(cookbook, "check", "ospf-multi-area") == 2
    assert "isn't implemented yet" in capsys.readouterr().err
