"""Validating recipes: the JSON Schema first, then the rules it can't express."""

from __future__ import annotations

import ipaddress
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cml_cookbook.recipes import CATEGORIES, Issue, Recipe, RecipeError, load_recipe, recipe_dirs
from cml_cookbook.versioning import changelog_versions, parse_semver

PLACEHOLDER = re.compile(r"\{\{(.*?)\}\}")
INPUT_PLACEHOLDER = re.compile(r"^\s*inputs\.([a-z][a-z0-9_]*)\s*$")


def load_validator(root: Path) -> Draft202012Validator:
    schema_file = root / "schema" / "v1" / "recipe.schema.json"
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _path(parts: Iterable[Any]) -> str:
    out = ""
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += f".{part}" if out else str(part)
    return out or "(top level)"


def schema_issues(recipe: Recipe, validator: Draft202012Validator) -> list[Issue]:
    errors = sorted(validator.iter_errors(recipe.data), key=lambda e: [str(p) for p in e.absolute_path])
    return [Issue("error", recipe.id, f"{_path(e.absolute_path)}: {e.message}") for e in errors]


def semantic_issues(recipe: Recipe) -> list[Issue]:
    """Rules beyond the schema. Assumes the recipe already passed the schema."""
    issues: list[Issue] = []
    data = recipe.data

    def error(message: str) -> None:
        issues.append(Issue("error", recipe.id, message))

    def warn(message: str) -> None:
        issues.append(Issue("warning", recipe.id, message))

    if data["id"] != recipe.id:
        error(f"id: {data['id']!r} doesn't match the folder name {recipe.id!r}")

    # Nodes and their day-0 configs. `texts` collects everything that may hold placeholders.
    labels: set[str] = set()
    texts: list[tuple[str, str]] = []
    recipe_root = recipe.path.resolve()
    for i, node in enumerate(recipe.nodes):
        where = f"topology.nodes[{i}]"
        if node["label"] in labels:
            error(f"{where}.label: duplicate label {node['label']!r}")
        labels.add(node["label"])
        if "config" in node:
            texts.append((f"{where}.config", node["config"]))
        if "login" in node:
            texts.append((f"{where}.login.password", node["login"]["password"]))
        if "config_file" in node:
            config_path = (recipe.path / node["config_file"]).resolve()
            if not config_path.is_relative_to(recipe_root):
                error(f"{where}.config_file: {node['config_file']} is outside the recipe folder")
            elif not config_path.is_file():
                error(f"{where}.config_file: {node['config_file']} doesn't exist")
            else:
                texts.append((node["config_file"], config_path.read_text(encoding="utf-8")))

    # Every node definition in use is listed under requirements.images, and nothing extra.
    listed: list[str] = [image["node_definition"] for image in data["requirements"]["images"]]
    for duplicate in sorted({d for d in listed if listed.count(d) > 1}):
        error(f"requirements.images: {duplicate!r} is listed more than once")
    used = {node["node_definition"] for node in recipe.nodes}
    for missing in sorted(used - set(listed)):
        error(f"requirements.images: node definition {missing!r} is used but not listed")
    for unused in sorted(set(listed) - used):
        warn(f"requirements.images: {unused!r} is listed but no node uses it")

    # Links join existing nodes, and each interface is used once.
    endpoints: dict[tuple[str, str], int] = {}
    for i, link in enumerate(data["topology"]["links"]):
        for side in ("a", "b"):
            label, _, interface = link[side].partition(":")
            if label not in labels:
                error(f"topology.links[{i}].{side}: no node labelled {label!r}")
            if (label, interface) in endpoints:
                error(
                    f"topology.links[{i}].{side}: {link[side]} is already used by "
                    f"topology.links[{endpoints[(label, interface)]}]"
                )
            endpoints[(label, interface)] = i

    for i, entry in enumerate(data.get("addressing", [])):
        try:
            ipaddress.ip_network(entry["prefix"], strict=True)
        except ValueError as exc:
            error(f"addressing[{i}].prefix: {exc}")

    # Checks.
    check_ids: set[str] = set()
    for i, check in enumerate(data["checks"]):
        where = f"checks[{i}]"
        if check["id"] in check_ids:
            error(f"{where}.id: duplicate check id {check['id']!r}")
        check_ids.add(check["id"])
        if "node" in check and check["node"] not in labels:
            error(f"{where}.node: no node labelled {check['node']!r}")
        expect = check.get("expect", {})
        for key in ("pattern", "not_pattern"):
            if key in expect:
                try:
                    re.compile(expect[key])
                except re.error as exc:
                    error(f"{where}.expect.{key}: not a valid regular expression: {exc}")
        if expect.get("success_min", 0) > expect.get("success_max", 100):
            error(f"{where}.expect: success_min is greater than success_max")
        for key in ("target", "command", "instructions"):
            if key in check:
                texts.append((f"{where}.{key}", check[key]))

    # Steps.
    step_ids: set[str] = set()
    for i, step in enumerate(data.get("steps", [])):
        where = f"steps[{i}]"
        if step["id"] in step_ids:
            error(f"{where}.id: duplicate step id {step['id']!r}")
        step_ids.add(step["id"])
        if "node" in step and step["node"] not in labels:
            error(f"{where}.node: no node labelled {step['node']!r}")
        for check_id in step.get("verify", []):
            if check_id not in check_ids:
                error(f"{where}.verify: no check with id {check_id!r}")
        for key in ("commands", "instructions"):
            if key in step:
                texts.append((f"{where}.{key}", step[key]))

    # Inputs and the placeholders that use them.
    inputs: set[str] = set()
    for i, item in enumerate(data.get("inputs", [])):
        if item["name"] in inputs:
            error(f"inputs[{i}].name: duplicate input {item['name']!r}")
        inputs.add(item["name"])
    used_inputs: set[str] = set()
    for where, text in texts:
        for match in PLACEHOLDER.finditer(text):
            name = INPUT_PLACEHOLDER.match(match.group(1))
            if not name:
                error(f"{where}: placeholder {match.group(0)!r} isn't of the form {{{{ inputs.<name> }}}}")
            elif name.group(1) not in inputs:
                error(f"{where}: {match.group(0)} refers to an undeclared input {name.group(1)!r}")
            else:
                used_inputs.add(name.group(1))
    for unused_input in sorted(inputs - used_inputs):
        warn(f"inputs: {unused_input!r} is declared but never used")

    # Status and test records.
    status = data["status"]
    if status == "stable" and not any(run["result"] == "pass" for run in data["tested_on"]):
        error("status: a stable recipe needs at least one tested_on entry with result: pass")
    if status != "deprecated" and "replaced_by" in data:
        error("replaced_by: only deprecated recipes have a replacement")
    if data.get("replaced_by") == recipe.id:
        error("replaced_by: a recipe can't replace itself")
    for i, run in enumerate(data["tested_on"]):
        if parse_semver(run["recipe_version"]) > parse_semver(data["version"]):
            error(f"tested_on[{i}].recipe_version: {run['recipe_version']} is newer than version {data['version']}")

    # Files every recipe has.
    if not (recipe.path / "README.md").is_file():
        error("README.md is missing")
    changelog = recipe.path / "CHANGELOG.md"
    if not changelog.is_file():
        error("CHANGELOG.md is missing")
    elif data["version"] not in changelog_versions(changelog.read_text(encoding="utf-8")):
        error(f"CHANGELOG.md has no entry for version {data['version']}")

    for key in ("title", "summary"):
        if "TODO" in data[key]:
            warn(f"{key}: still contains TODO")
    for i, node in enumerate(recipe.nodes):
        if "TODO" in node.get("role", ""):
            warn(f"topology.nodes[{i}].role: still contains TODO")

    return issues


def validate_repo(root: Path, ids: Iterable[str] = ()) -> tuple[list[Recipe], list[Issue]]:
    """Validate every recipe (or just `ids`) and return the loadable recipes with all issues."""
    wanted = set(ids)
    validator = load_validator(root)
    issues: list[Issue] = []
    recipes: list[Recipe] = []

    for category_dir in sorted(p for p in (root / "recipes").iterdir() if p.is_dir()):
        if category_dir.name not in CATEGORIES:
            known = ", ".join(CATEGORIES)
            issues.append(
                Issue("error", f"recipes/{category_dir.name}", f"unknown category (expected one of: {known})")
            )
    for category in CATEGORIES:
        if not (root / "recipes" / category / "README.md").is_file():
            issues.append(Issue("error", f"recipes/{category}", "category README.md is missing"))

    for path in recipe_dirs(root):
        try:
            recipe = load_recipe(path)
        except RecipeError as exc:
            issues.append(Issue("error", path.relative_to(root).as_posix(), str(exc).split(": ", 1)[-1]))
            continue
        recipes.append(recipe)

    seen: dict[str, Recipe] = {}
    for recipe in recipes:
        if recipe.id in seen:
            issues.append(
                Issue(
                    "error",
                    recipe.id,
                    f"id is also used by recipes/{seen[recipe.id].category}/{recipe.id}; ids must be unique",
                )
            )
        seen[recipe.id] = recipe

    for recipe in recipes:
        if wanted and recipe.id not in wanted:
            continue
        found = schema_issues(recipe, validator)
        if not found:
            found = semantic_issues(recipe)
            replacement = recipe.data.get("replaced_by")
            if replacement and replacement not in seen:
                found.append(Issue("error", recipe.id, f"replaced_by: no recipe with id {replacement!r}"))
        issues.extend(found)

    for missing in sorted(wanted - set(seen)):
        issues.append(Issue("error", missing, "no recipe with this id"))

    return recipes, issues
