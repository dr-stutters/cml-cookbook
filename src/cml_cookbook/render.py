"""`cookbook render`: a recipe as a CML topology file you can import and start."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import yaml

from cml_cookbook.recipes import Recipe

# CML accepts topology schema versions 0.0.1 to 0.3.1 on import (CML 2.10 exports 0.3.1).
# 0.2.2 is the oldest one with everything a recipe uses, so rendered files have the best
# chance of importing on older CML releases. Tested on CML 2.10.0.
SCHEMA_VERSION = "0.2.2"
REPO_URL = "https://github.com/dr-stutters/cml-cookbook"
TITLE_MAX = 64

PLACEHOLDER = re.compile(r"\{\{\s*inputs\.([a-z][a-z0-9_]*)\s*\}\}")


class RenderError(Exception):
    pass


@dataclass(frozen=True)
class NodeDefinition:
    """How CML lays out a node definition's interfaces, as seen in a lab exported from CML."""

    loopback: str | None  # label of the interface CML creates with type loopback, if any
    default_slots: int  # physical interfaces CML creates for a new node
    max_slots: int
    physical_label: Callable[[int], str]  # slot number -> interface label

    def slot_of(self, label: str) -> int | None:
        for slot in range(self.max_slots):
            if self.physical_label(slot) == label:
                return slot
        return None


def _iol(slot: int) -> str:
    return f"Ethernet{slot // 4}/{slot % 4}"


# Read from labs exported from CML 2.10.0 with IOL XE and IOL L2 XE 17.18.02: Loopback0 is a
# loopback interface, and slot N is Ethernet{N // 4}/{N % 4} (Ethernet1/0 is slot 4).
# To support another node definition, export a lab that uses it and add it here.
NODE_DEFINITIONS: dict[str, NodeDefinition] = {
    "iol-xe": NodeDefinition(loopback="Loopback0", default_slots=4, max_slots=32, physical_label=_iol),
    "ioll2-xe": NodeDefinition(loopback="Loopback0", default_slots=4, max_slots=32, physical_label=_iol),
}


def parse_input_args(pairs: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for pair in pairs:
        name, sep, value = pair.partition("=")
        if not sep or not name:
            raise RenderError(f"--input {pair!r}: expected name=value")
        values[name.strip()] = value
    return values


def _check_type(name: str, kind: str, value: str) -> None:
    try:
        if kind == "integer":
            int(value)
        elif kind == "ipv4":
            ipaddress.IPv4Address(value)
        elif kind == "ipv6":
            ipaddress.IPv6Address(value)
        elif kind == "ipv4_prefix":
            ipaddress.IPv4Network(value, strict=True)
    except ValueError as exc:
        raise RenderError(f"input {name}: {value!r} isn't a valid {kind} ({exc})") from exc


def resolve_inputs(recipe: Recipe, given: dict[str, str]) -> dict[str, str]:
    """Values for the recipe's inputs: given ones first, then defaults. Errors list what's missing."""
    declared = {item["name"]: item for item in recipe.data.get("inputs", [])}
    unknown = sorted(set(given) - set(declared))
    if unknown:
        raise RenderError(f"{recipe.id} has no input named {', '.join(unknown)}")
    values: dict[str, str] = {}
    missing = []
    for name, item in declared.items():
        if name in given:
            values[name] = given[name]
        elif "default" in item:
            values[name] = str(item["default"])
        elif item.get("required", True):
            missing.append(item)
            continue
        else:
            continue
        _check_type(name, item["type"], values[name])
    if missing:
        lines = [f"  --input {item['name']}=...  {item['description']}" for item in missing]
        raise RenderError(f"{recipe.id} needs values for its required inputs:\n" + "\n".join(lines))
    return values


def needs_inputs(recipe: Recipe) -> bool:
    """True when the recipe can't be rendered without values from the user's environment."""
    return any(
        item.get("required", True) and "default" not in item for item in recipe.data.get("inputs", [])
    )


def unsupported_node_definitions(recipe: Recipe) -> list[str]:
    return sorted({node["node_definition"] for node in recipe.nodes} - set(NODE_DEFINITIONS))


def _fill(text: str, values: dict[str, str], where: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            raise RenderError(f"{where}: {match.group(0)} has no value (pass --input {name}=...)")
        return values[name]

    return PLACEHOLDER.sub(replace, text)


def _title(recipe: Recipe) -> str:
    title = f"{recipe.data['title']} ({recipe.id} v{recipe.version})"
    return title if len(title) <= TITLE_MAX else f"{recipe.id} v{recipe.version}"[:TITLE_MAX]


def _notes(recipe: Recipe) -> str:
    folder = recipe.path.parent.name + "/" + recipe.id
    ref = f"{recipe.id}/v{recipe.version}"
    lines = [
        f"**{recipe.data['title']}**: CML Cookbook recipe `{recipe.id}` v{recipe.version} ({recipe.data['status']}).",
        "",
        " ".join(recipe.data["summary"].split()),
        "",
        f"- Recipe: {REPO_URL}/tree/{ref}/recipes/{folder}",
        f"- Checks that prove it works: {REPO_URL}/blob/{ref}/recipes/{folder}/recipe.yaml",
    ]
    steps = recipe.data.get("steps", [])
    if steps:
        lines.append(f"- After every node has booted, run its {len(steps)} build step(s) from the recipe.")
    return "\n".join(lines)


def build_topology(recipe: Recipe, values: dict[str, str]) -> dict[str, Any]:
    unknown = unsupported_node_definitions(recipe)
    if unknown:
        raise RenderError(
            f"{recipe.id} uses node definitions cookbook render doesn't know yet: {', '.join(unknown)}. "
            "Add them to NODE_DEFINITIONS in src/cml_cookbook/render.py from a lab exported from CML."
        )

    node_ids = {node["label"]: f"n{i}" for i, node in enumerate(recipe.nodes)}
    used_slots: dict[str, dict[str, int]] = {node["label"]: {} for node in recipe.nodes}
    definitions = {node["label"]: NODE_DEFINITIONS[node["node_definition"]] for node in recipe.nodes}
    for i, link in enumerate(recipe.data["topology"]["links"]):
        for side in ("a", "b"):
            label, _, interface = link[side].partition(":")
            definition = definitions[label]
            slot = definition.slot_of(interface)
            if slot is None:
                node_definition = next(n["node_definition"] for n in recipe.nodes if n["label"] == label)
                first, last = definition.physical_label(0), definition.physical_label(definition.max_slots - 1)
                raise RenderError(
                    f"topology.links[{i}].{side}: {interface!r} isn't a physical interface of "
                    f"{node_definition} (expected {first} to {last})"
                )
            used_slots[label][interface] = slot

    nodes = []
    interface_ids: dict[tuple[str, str], str] = {}
    for i, node in enumerate(recipe.nodes):
        label = node["label"]
        definition = definitions[label]
        interfaces = []
        if definition.loopback:
            interfaces.append({"id": "i0", "label": definition.loopback, "type": "loopback"})
        slots = max([definition.default_slots - 1, *used_slots[label].values()]) + 1
        for slot in range(slots):
            interface_id = f"i{len(interfaces)}"
            interface_label = definition.physical_label(slot)
            interfaces.append({"id": interface_id, "label": interface_label, "slot": slot, "type": "physical"})
            interface_ids[(label, interface_label)] = interface_id

        entry: dict[str, Any] = {
            "id": node_ids[label],
            "label": label,
            "node_definition": node["node_definition"],
            "x": node.get("x", (i % 5) * 200),
            "y": node.get("y", (i // 5) * 200),
        }
        for key, field in (("image_definition", "image_definition"), ("ram_mb", "ram"), ("cpus", "cpus")):
            if key in node:
                entry[field] = node[key]
        entry["tags"] = []
        if "config_file" in node:
            text = (recipe.path / node["config_file"]).read_text(encoding="utf-8")
            entry["configuration"] = _fill(text, values, node["config_file"])
        elif "config" in node:
            entry["configuration"] = _fill(node["config"], values, f"topology.nodes[{i}].config")
        entry["interfaces"] = interfaces
        nodes.append(entry)

    links = []
    for i, link in enumerate(recipe.data["topology"]["links"]):
        a_label, _, a_interface = link["a"].partition(":")
        b_label, _, b_interface = link["b"].partition(":")
        links.append(
            {
                "id": f"l{i}",
                "n1": node_ids[a_label],
                "n2": node_ids[b_label],
                "i1": interface_ids[(a_label, a_interface)],
                "i2": interface_ids[(b_label, b_interface)],
                "label": f"{link['a']}<->{link['b']}",
            }
        )

    return {
        "lab": {
            "version": SCHEMA_VERSION,
            "title": _title(recipe),
            "description": " ".join(recipe.data["summary"].split()),
            "notes": _notes(recipe),
        },
        "nodes": nodes,
        "links": links,
        "annotations": [],
    }


class _Dumper(yaml.SafeDumper):
    """Write multi-line strings (the day-0 configs) as literal blocks, so the file stays readable."""


def _str(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(str, _str)


def render(recipe: Recipe, given: dict[str, str] | None = None) -> str:
    values = resolve_inputs(recipe, given or {})
    topology = build_topology(recipe, values)
    header = (
        f"# CML lab for the CML Cookbook recipe {recipe.id} v{recipe.version}, written by cookbook render.\n"
        "# Import it in CML (Dashboard > Import), then start the lab.\n"
    )
    body = yaml.dump(topology, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=1000)
    return header + body
