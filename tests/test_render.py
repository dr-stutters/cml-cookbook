from pathlib import Path
from typing import Any

import pytest
import yaml
from conftest import OSPF

from cml_cookbook.cli import main
from cml_cookbook.recipes import Recipe, load_recipe
from cml_cookbook.render import RenderError, render
from cml_cookbook.versioning import release_plan


def lab(text: str) -> dict[str, Any]:
    return yaml.safe_load(text)


def interface_label(topology: dict[str, Any], node_id: str, interface_id: str) -> str:
    node = next(n for n in topology["nodes"] if n["id"] == node_id)
    return next(i["label"] for i in node["interfaces"] if i["id"] == interface_id)


def make_recipe(tmp_path: Path, nodes: list[dict], links: list[dict], inputs: list[dict] | None = None) -> Recipe:
    folder = tmp_path / "routing-switching" / "test-lab"
    (folder / "configs").mkdir(parents=True)
    for node in nodes:
        if "config_file" in node:
            (folder / node["config_file"]).write_text(node.pop("_text"))
    data = {
        "id": "test-lab",
        "title": "Test lab",
        "version": "0.1.0",
        "status": "draft",
        "summary": "A lab for tests.",
        "topology": {"nodes": nodes, "links": links},
    }
    if inputs:
        data["inputs"] = inputs
    return Recipe("routing-switching", folder, data)


def test_renders_the_fixture_recipe(cookbook):
    recipe = load_recipe(cookbook / OSPF)
    topology = lab(render(recipe))
    assert topology["lab"]["version"] == "0.2.2"
    assert topology["lab"]["title"] == "OSPF multi-area (ospf-multi-area v0.1.0)"
    assert [n["label"] for n in topology["nodes"]] == ["r1", "r2", "r3", "r4", "r5"]
    assert len(topology["links"]) == 5


def test_configs_are_the_files_byte_for_byte(cookbook):
    recipe = load_recipe(cookbook / OSPF)
    topology = lab(render(recipe))
    for node in topology["nodes"]:
        assert node["configuration"] == (cookbook / OSPF / "configs" / f"{node['label']}.cfg").read_text()


def test_links_join_the_named_interfaces(cookbook):
    recipe = load_recipe(cookbook / OSPF)
    topology = lab(render(recipe))
    labels = {n["id"]: n["label"] for n in topology["nodes"]}
    rendered = {
        f"{labels[l['n1']]}:{interface_label(topology, l['n1'], l['i1'])}"
        f" {labels[l['n2']]}:{interface_label(topology, l['n2'], l['i2'])}"
        for l in topology["links"]
    }
    assert rendered == {f"{l['a']} {l['b']}" for l in recipe.data["topology"]["links"]}


def test_iol_interfaces_match_what_cml_creates(cookbook):
    topology = lab(render(load_recipe(cookbook / OSPF)))
    r2 = next(n for n in topology["nodes"] if n["label"] == "r2")
    assert r2["interfaces"] == [
        {"id": "i0", "label": "Loopback0", "type": "loopback"},
        {"id": "i1", "label": "Ethernet0/0", "slot": 0, "type": "physical"},
        {"id": "i2", "label": "Ethernet0/1", "slot": 1, "type": "physical"},
        {"id": "i3", "label": "Ethernet0/2", "slot": 2, "type": "physical"},
        {"id": "i4", "label": "Ethernet0/3", "slot": 3, "type": "physical"},
    ]


def test_ethernet1_0_adds_slot_4(tmp_path):
    nodes = [{"label": "sw1", "node_definition": "ioll2-xe"}, {"label": "sw2", "node_definition": "ioll2-xe"}]
    recipe = make_recipe(tmp_path, nodes, [{"a": "sw1:Ethernet1/0", "b": "sw2:Ethernet0/1"}])
    sw1 = lab(render(recipe))["nodes"][0]
    assert sw1["interfaces"][-1] == {"id": "i5", "label": "Ethernet1/0", "slot": 4, "type": "physical"}


def test_output_is_deterministic(cookbook):
    recipe = load_recipe(cookbook / OSPF)
    assert render(recipe) == render(recipe)


def test_unknown_node_definition(tmp_path):
    recipe = make_recipe(tmp_path, [{"label": "r1", "node_definition": "cat8000v"}], [])
    with pytest.raises(RenderError, match="doesn't know yet: cat8000v"):
        render(recipe)


def test_interface_the_node_doesnt_have(tmp_path):
    nodes = [{"label": "r1", "node_definition": "iol-xe"}, {"label": "r2", "node_definition": "iol-xe"}]
    recipe = make_recipe(tmp_path, nodes, [{"a": "r1:GigabitEthernet1", "b": "r2:Ethernet0/1"}])
    with pytest.raises(RenderError, match="isn't a physical interface of iol-xe"):
        render(recipe)


def test_long_titles_fall_back_to_id_and_version(tmp_path):
    recipe = make_recipe(tmp_path, [{"label": "r1", "node_definition": "iol-xe"}], [])
    recipe.data["title"] = "A" * 60
    assert lab(render(recipe))["lab"]["title"] == "test-lab v0.1.0"


@pytest.fixture
def with_inputs(tmp_path):
    nodes = [
        {
            "label": "r1",
            "node_definition": "iol-xe",
            "config_file": "configs/r1.cfg",
            "_text": "hostname r1\nntp server {{ inputs.ntp_ip }}\nradius key {{ inputs.key }}\nlogging {{ inputs.log_ip }}\nend\n",
        }
    ]
    inputs = [
        {"name": "ntp_ip", "description": "NTP server", "type": "ipv4"},
        {"name": "key", "description": "RADIUS key", "type": "secret"},
        {"name": "log_ip", "description": "Syslog server", "type": "ipv4", "default": "192.0.2.50"},
    ]
    return make_recipe(tmp_path, nodes, [], inputs)


def test_inputs_are_filled_in(with_inputs):
    config = lab(render(with_inputs, {"ntp_ip": "192.0.2.10", "key": "s3cret"}))["nodes"][0]["configuration"]
    assert config == "hostname r1\nntp server 192.0.2.10\nradius key s3cret\nlogging 192.0.2.50\nend\n"


def test_missing_required_inputs_are_listed(with_inputs):
    with pytest.raises(RenderError) as excinfo:
        render(with_inputs, {"ntp_ip": "192.0.2.10"})
    assert "--input key=..." in str(excinfo.value)
    assert "ntp_ip" not in str(excinfo.value)


def test_input_types_are_checked(with_inputs):
    with pytest.raises(RenderError, match="isn't a valid ipv4"):
        render(with_inputs, {"ntp_ip": "not-an-address", "key": "x"})


def test_unknown_input(with_inputs):
    with pytest.raises(RenderError, match="no input named typo"):
        render(with_inputs, {"ntp_ip": "192.0.2.10", "key": "x", "typo": "1"})


def test_cli_render_to_file(cookbook, tmp_path, capsys):
    out = tmp_path / "lab.yaml"
    assert main(["--root", str(cookbook), "render", "ospf-multi-area", "-o", str(out)]) == 0
    assert lab(out.read_text())["lab"]["title"] == "OSPF multi-area (ospf-multi-area v0.1.0)"
    assert "Import it in CML" in capsys.readouterr().err


def test_cli_render_refuses_to_print_secrets(cookbook, edit_recipe, capsys):
    config = cookbook / OSPF / "configs" / "r1.cfg"
    config.write_text(config.read_text().replace("end\n", "key {{ inputs.key }}\nend\n"))
    edit_recipe(cookbook / OSPF, lambda d: d.update(inputs=[{"name": "key", "description": "k", "type": "secret"}]))
    assert main(["--root", str(cookbook), "render", "ospf-multi-area", "--input", "key=s3cret"]) == 2
    captured = capsys.readouterr()
    assert "s3cret" not in captured.out + captured.err


def test_cli_render_refuses_invalid_recipes(cookbook):
    (cookbook / OSPF / "configs" / "r3.cfg").unlink()
    assert main(["--root", str(cookbook), "render", "ospf-multi-area"]) == 1


def test_release_plan_marks_renderable(git_cookbook, edit_recipe):
    assert release_plan(git_cookbook)[0]["renderable"] is True
    edit_recipe(
        git_cookbook / OSPF, lambda d: d.update(inputs=[{"name": "ise_ip", "description": "ISE", "type": "ipv4"}])
    )
    assert release_plan(git_cookbook)[0]["renderable"] is False


def test_every_recipe_in_the_repo_renders():
    """Each recipe that needs no inputs renders, with its configs and links intact."""
    from conftest import REPO

    from cml_cookbook.recipes import load_all
    from cml_cookbook.render import needs_inputs

    for recipe in load_all(REPO):
        if needs_inputs(recipe):
            continue
        topology = lab(render(recipe))
        for node, spec in zip(topology["nodes"], recipe.nodes):
            if "config_file" in spec:
                assert node["configuration"] == (recipe.path / spec["config_file"]).read_text(), recipe.id
        labels = {n["id"]: n["label"] for n in topology["nodes"]}
        rendered = {
            f"{labels[l['n1']]}:{interface_label(topology, l['n1'], l['i1'])}"
            f" {labels[l['n2']]}:{interface_label(topology, l['n2'], l['i2'])}"
            for l in topology["links"]
        }
        assert rendered == {f"{l['a']} {l['b']}" for l in recipe.data["topology"]["links"]}, recipe.id


def test_ftdv_fmcv_and_switch_layouts(tmp_path):
    nodes = [
        {"label": "ext", "node_definition": "external_connector", "config": "System Bridge"},
        {"label": "ums", "node_definition": "unmanaged_switch"},
        {"label": "fmc1", "node_definition": "fmcv"},
        {"label": "ftd2", "node_definition": "ftdv"},
        {"label": "isp3", "node_definition": "iol-xe"},
    ]
    links = [
        {"a": "ext:port", "b": "ums:port0"},
        {"a": "fmc1:eth0", "b": "ums:port1"},
        {"a": "ftd2:Management0/0", "b": "ums:port2"},
        {"a": "ftd2:GigabitEthernet0/2", "b": "isp3:Ethernet0/1"},
    ]
    topology = lab(render(make_recipe(tmp_path, nodes, links)))
    by_label = {n["label"]: n for n in topology["nodes"]}
    assert by_label["ext"]["configuration"] == "System Bridge"
    assert by_label["ext"]["interfaces"] == [{"id": "i0", "label": "port", "slot": 0, "type": "physical"}]
    assert [i["label"] for i in by_label["ums"]["interfaces"]] == [f"port{n}" for n in range(8)]
    assert by_label["fmc1"]["interfaces"] == [
        {"id": "i0", "label": "lo", "type": "loopback"},
        {"id": "i1", "label": "eth0", "slot": 0, "type": "physical"},
    ]
    ftd = [(i["label"], i["slot"]) for i in by_label["ftd2"]["interfaces"]]
    assert ftd == [
        ("Management0/0", 0),
        ("donotuse1", 1),
        ("GigabitEthernet0/0", 2),
        ("GigabitEthernet0/1", 3),
        ("GigabitEthernet0/2", 4),
    ]


def test_alpine_layout(tmp_path):
    nodes = [
        {"label": "h1", "node_definition": "alpine", "config": "hostname h1"},
        {"label": "h2", "node_definition": "alpine"},
    ]
    topology = lab(render(make_recipe(tmp_path, nodes, [{"a": "h1:eth0", "b": "h2:eth1"}])))
    by_label = {n["label"]: n for n in topology["nodes"]}
    assert by_label["h1"]["interfaces"] == [{"id": "i0", "label": "eth0", "slot": 0, "type": "physical"}]
    assert [(i["label"], i["slot"]) for i in by_label["h2"]["interfaces"]] == [("eth0", 0), ("eth1", 1)]


def test_reserved_ftdv_slot_cant_be_linked(tmp_path):
    nodes = [{"label": "ftd2", "node_definition": "ftdv"}, {"label": "r1", "node_definition": "iol-xe"}]
    recipe = make_recipe(tmp_path, nodes, [{"a": "ftd2:donotuse1", "b": "r1:Ethernet0/1"}])
    with pytest.raises(RenderError, match="isn't a physical interface of ftdv"):
        render(recipe)


def test_login_becomes_the_pyats_credentials(tmp_path):
    nodes = [
        {
            "label": "ftd2",
            "node_definition": "ftdv",
            "login": {"username": "admin", "password": "{{ inputs.admin_password }}"},
        }
    ]
    inputs = [{"name": "admin_password", "description": "admin password", "type": "secret"}]
    recipe = make_recipe(tmp_path, nodes, [], inputs)
    node = lab(render(recipe, {"admin_password": "Str0ng!Pass"}))["nodes"][0]
    assert node["pyats"] == {"username": "admin", "password": "Str0ng!Pass"}
