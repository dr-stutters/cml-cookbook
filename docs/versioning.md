# Versioning

Three things in this repo have versions, and each is tracked separately:

| What | Where the version lives | Git tag |
|---|---|---|
| Each recipe | `version:` in its `recipe.yaml`, plus its own `CHANGELOG.md` | `<id>/v<version>`, for example `ospf-multi-area/v1.2.0` |
| The toolkit (CLI, docs, templates) | `pyproject.toml`, plus the root `CHANGELOG.md` | `v<version>`, for example `v0.3.0` |
| The recipe format | `schema/v1/`, `schema/v2/`, ...; each recipe declares `schema_version` | none |

## Recipes

Recipes use [semantic versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`), judged from the point of view of someone who uses the lab, or who has automation, notes or a course built on it.

| Bump | When | Examples |
|---|---|---|
| **Major** | Something someone relies on breaks or changes meaning | A node, link or interface added, removed or renamed; addressing changed; a new required input; a check ID renamed or removed; a different image needed |
| **Minor** | New things, nothing existing changes | New checks; new optional inputs; new steps; config added that no existing check depends on |
| **Patch** | Fixes that don't change the lab's shape | A config bug fixed; README edits; a new `tested_on` entry; a check's pattern loosened to match a newer IOS |

Before `1.0.0`, a recipe is still settling and anything may change in a minor bump. A recipe usually reaches `1.0.0` when it first becomes `stable`.

### Rules

- **Every change bumps the version.** Any change to any file in a recipe's folder needs a higher `version` and a `CHANGELOG.md` entry for it. CI enforces this with `cookbook version-check`.
- **No version folders.** Old versions live in git tags, not in copies of the recipe. To get an old version, read the files at its tag.
- **Big changes make a new recipe.** If the old and new versions both need to exist side by side, the new one is a separate recipe with its own ID (`ospf-multi-area-ipv6`), not a version folder.
- **Never delete or move a recipe.** Set `status: deprecated` and `replaced_by: <new-id>`. It stays where it is so links keep working, and its old tags stay valid.

### Changelog format

Each recipe's `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/):

```markdown
## [1.1.0] - 2026-11-20

### Added

- Check that r5 has no external routes.

## [1.0.0] - 2026-11-02

### Changed

- First stable release, tested on CML 2.9.
```

The heading must be `## [<version>]` (the brackets and date are optional, but please include the date). The text under the heading becomes the release notes.

### Releases

When a pull request that bumps a recipe merges to `main`, the `release` workflow:

1. Finds every recipe whose current version has no tag yet (`cookbook release-plan`).
2. Tags it `<id>/v<version>` and creates a GitHub release with the changelog entry as its notes.
3. Attaches a zip of the recipe folder. Once `cookbook render` exists, it will also attach an importable CML lab file.

Releases of `draft` recipes are marked as pre-releases. Recipe releases are never marked as the repository's "latest" release, so that badge stays with toolkit releases.

### Pinning a version

People and agents can ask for `<id>@<version>`, for example `ospf-multi-area@1.2.0`, which means "the files at tag `ospf-multi-area/v1.2.0`". Without a version, use `main`.

## The toolkit

The `cookbook` CLI, docs and templates are versioned together in `pyproject.toml`, with changes listed in the root `CHANGELOG.md` under `Unreleased` until a release. Maintainers tag toolkit releases `v<version>` by hand.

## The recipe format

`schema_version` in each recipe says which schema it follows. Schemas live in `schema/v<N>/recipe.schema.json`.

- **Changes that keep every existing recipe valid** (a new optional field, a new check type) go into the current schema and get a toolkit minor bump.
- **Changes that would make any existing recipe invalid** need a new schema version in a new folder. The CLI then supports both versions until every recipe has been migrated, and each migrated recipe gets a version bump of its own.
