import shutil

import pytest
from conftest import OSPF, commit_all, run_git

from cml_cookbook.scaffold import new_recipe
from cml_cookbook.versioning import changelog_section, changelog_versions, parse_semver, release_plan, version_check

CHANGELOG = """# Changelog

## [1.1.0] - 2026-11-01

### Changed

- Faster.

## [1.0.0] - 2026-10-16

- First.
"""


def messages(root, base="base"):
    return [issue.message for issue in version_check(root, base)]


def test_semver_ordering():
    assert parse_semver("1.10.0") > parse_semver("1.9.9")
    assert parse_semver("2.0.0") > parse_semver("1.99.99")
    with pytest.raises(ValueError):
        parse_semver("1.0")


def test_changelog_parsing():
    assert changelog_versions(CHANGELOG) == ["1.1.0", "1.0.0"]
    assert changelog_section(CHANGELOG, "1.1.0") == "### Changed\n\n- Faster."
    assert changelog_section(CHANGELOG, "1.0.0") == "- First."
    assert changelog_section(CHANGELOG, "9.9.9") == ""


def test_unchanged_repo_passes(git_cookbook):
    assert messages(git_cookbook) == []


def test_change_without_bump_fails(git_cookbook):
    readme = git_cookbook / OSPF / "README.md"
    readme.write_text(readme.read_text() + "\nA typo fix.\n")
    assert any("version is still 0.1.0" in m for m in messages(git_cookbook))


def test_bump_with_changelog_passes(git_cookbook, edit_recipe):
    folder = git_cookbook / OSPF
    edit_recipe(folder, lambda d: d.update(version="0.1.1"))
    changelog = folder / "CHANGELOG.md"
    changelog.write_text(
        changelog.read_text().replace("## [0.1.0]", "## [0.1.1] - 2026-10-17\n\n### Fixed\n\n- Typo.\n\n## [0.1.0]")
    )
    assert messages(git_cookbook) == []


def test_bump_without_changelog_fails(git_cookbook, edit_recipe):
    edit_recipe(git_cookbook / OSPF, lambda d: d.update(version="0.2.0"))
    assert any("no entry for version 0.2.0" in m for m in messages(git_cookbook))


def test_committed_changes_are_compared_to_merge_base(git_cookbook):
    readme = git_cookbook / OSPF / "README.md"
    readme.write_text(readme.read_text() + "\nCommitted change.\n")
    commit_all(git_cookbook, "change")
    assert any("version is still 0.1.0" in m for m in messages(git_cookbook))


def test_deleting_a_recipe_fails(git_cookbook):
    shutil.rmtree(git_cookbook / OSPF)
    assert any("deleted or moved" in m for m in messages(git_cookbook))


def test_new_recipe_passes(git_cookbook):
    new_recipe(git_cookbook, "enterprise", "campus-3-tier", "Campus 3-tier", "test")
    assert messages(git_cookbook) == []


def test_release_plan(git_cookbook):
    plan = release_plan(git_cookbook)
    assert [(p["tag"], p["prerelease"]) for p in plan] == [("ospf-multi-area/v0.1.0", True)]
    assert plan[0]["notes"].startswith("### Added")

    run_git(git_cookbook, "tag", "ospf-multi-area/v0.1.0")
    assert release_plan(git_cookbook) == []
