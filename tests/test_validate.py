import shutil
from pathlib import Path

from conftest import OSPF, REPO

from cml_cookbook.recipes import load_yaml
from cml_cookbook.validate import validate_repo


def errors(root: Path) -> list[str]:
    _, issues = validate_repo(root)
    return [issue.message for issue in issues if issue.level == "error"]


def test_this_repo_is_valid():
    assert errors(REPO) == []


def test_copy_is_valid(cookbook):
    assert errors(cookbook) == []


def test_dates_stay_strings():
    assert load_yaml("date: 2026-10-16") == {"date": "2026-10-16"}


def test_schema_errors_name_the_field(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d.update(version="1.0"))
    assert any(message.startswith("version:") for message in errors(cookbook))


def test_id_must_match_folder(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d.update(id="something-else"))
    assert any("doesn't match the folder name" in m for m in errors(cookbook))


def test_duplicate_label(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d["topology"]["nodes"][1].update(label="r1"))
    assert any("duplicate label 'r1'" in m for m in errors(cookbook))


def test_link_to_missing_node(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d["topology"]["links"][0].update(b="r9:Ethernet0/1"))
    assert any("no node labelled 'r9'" in m for m in errors(cookbook))


def test_interface_used_twice(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d["topology"]["links"][1].update(a="r1:Ethernet0/1"))
    assert any("already used by topology.links[0]" in m for m in errors(cookbook))


def test_missing_config_file(cookbook):
    (cookbook / OSPF / "configs" / "r3.cfg").unlink()
    assert any("configs/r3.cfg doesn't exist" in m for m in errors(cookbook))


def test_config_file_outside_recipe(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d["topology"]["nodes"][0].update(config_file="../../../README.md"))
    assert any("outside the recipe folder" in m for m in errors(cookbook))


def test_unlisted_node_definition(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d["topology"]["nodes"][0].update(node_definition="cat8000v"))
    assert any("'cat8000v' is used but not listed" in m for m in errors(cookbook))


def test_non_refplat_image_needs_source(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d["requirements"]["images"][0].update(refplat=False))
    assert any("'source' is a required property" in m for m in errors(cookbook))


def test_placeholders_must_be_declared_inputs(cookbook, edit_recipe):
    config = cookbook / OSPF / "configs" / "r1.cfg"
    config.write_text(config.read_text().replace("end\n", "ntp server {{ inputs.ntp_ip }}\nend\n"))
    assert any("undeclared input 'ntp_ip'" in m for m in errors(cookbook))

    edit_recipe(
        cookbook / OSPF,
        lambda d: d.update(inputs=[{"name": "ntp_ip", "description": "NTP server", "type": "ipv4"}]),
    )
    assert errors(cookbook) == []


def test_malformed_placeholder(cookbook):
    config = cookbook / OSPF / "configs" / "r1.cfg"
    config.write_text(config.read_text().replace("end\n", "ntp server {{ ntp_ip }}\nend\n"))
    assert any("isn't of the form" in m for m in errors(cookbook))


def test_secret_input_cannot_have_default(cookbook, edit_recipe):
    secret = {"name": "key", "description": "RADIUS key", "type": "secret", "default": "cisco"}
    edit_recipe(cookbook / OSPF, lambda d: d.update(inputs=[secret]))
    assert any(m.startswith("inputs[0]") for m in errors(cookbook))


def test_stable_needs_a_passing_run(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d.update(status="stable"))
    assert any("needs at least one tested_on entry" in m for m in errors(cookbook))

    run = {"recipe_version": "0.1.0", "cml_version": "2.9.0", "date": "2026-10-16", "result": "pass", "by": "test"}
    edit_recipe(cookbook / OSPF, lambda d: d.update(tested_on=[run]))
    assert errors(cookbook) == []


def test_deprecated_needs_existing_replacement(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d.update(status="deprecated"))
    assert any("'replaced_by' is a required property" in m for m in errors(cookbook))

    edit_recipe(cookbook / OSPF, lambda d: d.update(replaced_by="no-such-recipe"))
    assert any("no recipe with id 'no-such-recipe'" in m for m in errors(cookbook))


def test_changelog_entry_required(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d.update(version="0.2.0"))
    assert any("no entry for version 0.2.0" in m for m in errors(cookbook))


def test_check_fields_depend_on_type(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d["checks"][-1].update(command="show version"))
    assert any(m.startswith("checks[9]") for m in errors(cookbook))


def test_bad_regex(cookbook, edit_recipe):
    edit_recipe(cookbook / OSPF, lambda d: d["checks"][5]["expect"].update(pattern="type (extern"))
    assert any("not a valid regular expression" in m for m in errors(cookbook))


def test_step_must_verify_existing_checks(cookbook, edit_recipe):
    step = {"id": "s1", "title": "Step", "mode": "config", "node": "r1", "commands": "ip routing", "verify": ["nope"]}
    edit_recipe(cookbook / OSPF, lambda d: d.update(steps=[step]))
    assert any("no check with id 'nope'" in m for m in errors(cookbook))


def test_unknown_category_folder(cookbook):
    (cookbook / "recipes" / "misc").mkdir()
    assert any("unknown category" in m for m in errors(cookbook))


def test_ids_unique_across_categories(cookbook):
    shutil.copytree(cookbook / OSPF, cookbook / "recipes" / "enterprise" / "ospf-multi-area")
    assert any("ids must be unique" in m for m in errors(cookbook))


def test_folder_without_recipe_yaml(cookbook):
    (cookbook / "recipes" / "security" / "half-done").mkdir()
    assert any("missing recipe.yaml" in m for m in errors(cookbook))


def test_login_password_placeholder_must_be_declared(cookbook, edit_recipe):
    edit_recipe(
        cookbook / OSPF,
        lambda d: d["topology"]["nodes"][0].update(login={"username": "admin", "password": "{{ inputs.pw }}"}),
    )
    assert any("undeclared input 'pw'" in m for m in errors(cookbook))
