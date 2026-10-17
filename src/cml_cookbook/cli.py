"""The `cookbook` command."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from cml_cookbook import __version__
from cml_cookbook.catalog import CatalogError, write_catalog
from cml_cookbook.recipes import CATEGORIES, Issue, RecipeError, find_recipe, find_root
from cml_cookbook.render import REPO_URL, RenderError, parse_input_args, render
from cml_cookbook.scaffold import new_recipe
from cml_cookbook.validate import validate_repo
from cml_cookbook.versioning import GitError, release_plan, version_check

NOT_YET = "cookbook {command} isn't implemented yet. It's on the roadmap: " + REPO_URL + "/milestones"


def _report(issues: list[Issue], checked: str, strict: bool = False) -> int:
    for issue in issues:
        print(issue)
    errors = sum(1 for i in issues if i.level == "error")
    warnings = len(issues) - errors
    print(f"{checked}: {errors} error(s), {warnings} warning(s)")
    return 1 if errors or (strict and warnings) else 0


def cmd_validate(root: Path, args: argparse.Namespace) -> int:
    recipes, issues = validate_repo(root, args.ids)
    count = len(args.ids) if args.ids else len(recipes)
    return _report(issues, f"{count} recipe(s) checked", args.strict)


def cmd_index(root: Path, args: argparse.Namespace) -> int:
    recipes, issues = validate_repo(root)
    if any(issue.level == "error" for issue in issues):
        _report(issues, "catalog not written")
        return 1
    stale = write_catalog(recipes, root, check=args.check)
    names = [path.relative_to(root).as_posix() for path in stale]
    if args.check:
        if names:
            print("Out of date (run cookbook index): " + ", ".join(names))
            return 1
        print("Catalog is up to date.")
        return 0
    print(("Updated: " + ", ".join(names)) if names else "Catalog already up to date.")
    return 0


def cmd_new(root: Path, args: argparse.Namespace) -> int:
    path = new_recipe(root, args.category, args.id, args.title, args.maintainer)
    print(f"Created {path.relative_to(root).as_posix()}/. Next: fill in recipe.yaml, then run cookbook validate {args.id}")
    return 0


def cmd_version_check(root: Path, args: argparse.Namespace) -> int:
    return _report(version_check(root, args.base), f"versions checked against {args.base}")


def cmd_release_plan(root: Path, args: argparse.Namespace) -> int:
    plan = release_plan(root)
    if args.json:
        print(json.dumps(plan, indent=2))
    elif not plan:
        print("Every recipe version is already tagged.")
    else:
        for entry in plan:
            suffix = " (prerelease)" if entry["prerelease"] else ""
            print(f"{entry['tag']}{suffix}")
    return 0


def cmd_render(root: Path, args: argparse.Namespace) -> int:
    _, issues = validate_repo(root, [args.id])
    if any(issue.level == "error" for issue in issues):
        _report(issues, f"{args.id} not rendered")
        return 1
    recipe = find_recipe(root, args.id)
    given = parse_input_args(args.input)
    secrets = {item["name"] for item in recipe.data.get("inputs", []) if item["type"] == "secret"}
    has_secret = bool(secrets & set(given))
    if has_secret and args.output is None:
        raise RenderError("a secret input was given, so the lab file isn't printed; write it to a file with -o")
    text = render(recipe, given)
    if args.output is None:
        sys.stdout.write(text)
    else:
        args.output.write_text(text, encoding="utf-8")
        if has_secret:
            args.output.chmod(0o600)
        print(f"Wrote {args.output}. Import it in CML (Dashboard > Import), then start the lab.", file=sys.stderr)
    steps = recipe.data.get("steps", [])
    if steps:
        print(f"After the lab boots, run its {len(steps)} build step(s): see the recipe's README.", file=sys.stderr)
    return 0


def cmd_not_yet(root: Path, args: argparse.Namespace) -> int:
    print(NOT_YET.format(command=args.command), file=sys.stderr)
    return 2


COMMANDS: dict[str, Callable[[Path, argparse.Namespace], int]] = {
    "validate": cmd_validate,
    "index": cmd_index,
    "new": cmd_new,
    "version-check": cmd_version_check,
    "release-plan": cmd_release_plan,
    "render": cmd_render,
    "check": cmd_not_yet,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cookbook", description="Tools for the CML Cookbook recipe repository.")
    parser.add_argument("--root", type=Path, help="cookbook folder (default: found from the current directory)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    p = sub.add_parser("validate", help="check recipes against the schema and the repo rules")
    p.add_argument("ids", nargs="*", help="recipe ids (default: all)")
    p.add_argument("--strict", action="store_true", help="fail on warnings too")

    p = sub.add_parser("index", help="regenerate index.yaml and the README catalog tables")
    p.add_argument("--check", action="store_true", help="only report whether they are out of date")

    p = sub.add_parser("new", help="start a recipe from templates/recipe/")
    p.add_argument("category", choices=list(CATEGORIES))
    p.add_argument("id", help="kebab-case recipe id, for example bgp-dual-isp-edge")
    p.add_argument("--title", required=True)
    p.add_argument("--maintainer", required=True, help="your GitHub handle")

    p = sub.add_parser("version-check", help="check changed recipes have a version bump and changelog entry")
    p.add_argument("--base", default="origin/main", help="git ref to compare against (default: origin/main)")

    p = sub.add_parser("release-plan", help="list recipe versions that don't have a git tag yet")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("render", help="write a recipe as a CML lab file you can import and start")
    p.add_argument("id")
    p.add_argument(
        "--input", action="append", default=[], metavar="NAME=VALUE", help="value for one of the recipe's inputs"
    )
    p.add_argument("-o", "--output", type=Path, help="file to write (default: print it)")

    p = sub.add_parser("check", help="not implemented yet (on the roadmap)")
    p.add_argument("id")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = args.root.resolve() if args.root else find_root()
        return COMMANDS[args.command](root, args)
    except (RecipeError, CatalogError, GitError, RenderError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
