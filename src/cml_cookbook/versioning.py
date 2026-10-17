"""Recipe versions: semver, changelogs, and the git checks CI runs on pull requests."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from cml_cookbook.recipes import Issue, load_all, load_yaml
from cml_cookbook.render import needs_inputs, unsupported_node_definitions

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
CHANGELOG_HEADING = re.compile(r"^## \[?(\d+\.\d+\.\d+)\]?", re.MULTILINE)


class GitError(Exception):
    pass


def parse_semver(text: str) -> tuple[int, int, int]:
    match = SEMVER.match(str(text))
    if not match:
        raise ValueError(f"{text!r} isn't a MAJOR.MINOR.PATCH version")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def changelog_versions(text: str) -> list[str]:
    return CHANGELOG_HEADING.findall(text)


def changelog_section(text: str, version: str) -> str:
    """The body of the changelog entry for `version`, without its heading."""
    lines: list[str] = []
    collecting = False
    for line in text.splitlines():
        if line.startswith("## "):
            if collecting:
                break
            heading = CHANGELOG_HEADING.match(line)
            collecting = bool(heading and heading.group(1) == version)
            continue
        if collecting:
            lines.append(line)
    return "\n".join(lines).strip()


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def changed_paths(root: Path, merge_base: str) -> set[str]:
    """Files changed since `merge_base`, including uncommitted and untracked ones."""
    tracked = git(root, "diff", "--name-only", "--relative", merge_base).splitlines()
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return {path for path in tracked + untracked if path}


def file_at(root: Path, ref: str, path: str) -> str | None:
    try:
        return git(root, "show", f"{ref}:./{path}")
    except GitError:
        return None


def _version_of(text: str | None) -> str | None:
    if text is None:
        return None
    try:
        data = load_yaml(text)
    except Exception:
        return None
    version = data.get("version") if isinstance(data, dict) else None
    return str(version) if version is not None and SEMVER.match(str(version)) else None


def version_check(root: Path, base: str) -> list[Issue]:
    """Every recipe changed since `base` has a higher version and a changelog entry for it."""
    merge_base = git(root, "merge-base", base, "HEAD").strip()
    changed_recipes: set[tuple[str, str]] = set()
    for path in changed_paths(root, merge_base):
        parts = PurePosixPath(path).parts
        if len(parts) >= 4 and parts[0] == "recipes":
            changed_recipes.add((parts[1], parts[2]))

    issues: list[Issue] = []
    for category, recipe_id in sorted(changed_recipes):
        folder = f"recipes/{category}/{recipe_id}"
        recipe_file = root / folder / "recipe.yaml"
        before = _version_of(file_at(root, merge_base, f"{folder}/recipe.yaml"))

        if not recipe_file.is_file():
            if before is not None:
                issues.append(
                    Issue(
                        "error",
                        recipe_id,
                        f"{folder} was deleted or moved. Recipes are never removed: set status: deprecated "
                        "and replaced_by instead (docs/versioning.md)",
                    )
                )
            continue

        after = _version_of(recipe_file.read_text(encoding="utf-8"))
        if after is None:
            issues.append(Issue("error", recipe_id, "recipe.yaml has no valid version (run cookbook validate)"))
            continue
        if before is not None and parse_semver(after) <= parse_semver(before):
            issues.append(
                Issue(
                    "error",
                    recipe_id,
                    f"files changed but version is still {after} (it was {before} on {base}). "
                    "Bump it as described in docs/versioning.md",
                )
            )
        changelog = root / folder / "CHANGELOG.md"
        if not changelog.is_file() or after not in changelog_versions(changelog.read_text(encoding="utf-8")):
            issues.append(Issue("error", recipe_id, f"CHANGELOG.md has no entry for version {after}"))
    return issues


def release_plan(root: Path) -> list[dict[str, Any]]:
    """Recipe versions on this commit that don't have a git tag yet."""
    tags = set(git(root, "tag", "--list").splitlines())
    plan = []
    for recipe in load_all(root):
        tag = f"{recipe.id}/v{recipe.version}"
        if tag in tags:
            continue
        changelog = recipe.path / "CHANGELOG.md"
        notes = changelog_section(changelog.read_text(encoding="utf-8"), recipe.version) if changelog.is_file() else ""
        plan.append(
            {
                "id": recipe.id,
                "version": recipe.version,
                "tag": tag,
                "path": recipe.path.relative_to(root).as_posix(),
                "prerelease": recipe.data.get("status") == "draft",
                "renderable": not needs_inputs(recipe) and not unsupported_node_definitions(recipe),
                "notes": notes or f"{recipe.id} {recipe.version}",
            }
        )
    return plan
