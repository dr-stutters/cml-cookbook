# Changelog

Changes to the cookbook's tooling, schema and docs. Each recipe has its own `CHANGELOG.md` in its folder.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the toolkit uses [semantic versioning](https://semver.org/). See [docs/versioning.md](docs/versioning.md).

## [Unreleased]

### Added

- Recipe format and JSON Schema v1 (`schema/v1/recipe.schema.json`).
- `cookbook` CLI with `validate`, `index`, `new`, `version-check` and `release-plan`. `render` and `check` are placeholders until a CML server is available to test them.
- Recipe template, category folders, generated catalog (`index.yaml` and README tables).
- Docs: design, recipe format, conventions, versioning, writing a recipe, and AGENTS.md for AI agents.
- CI to validate pull requests, and a release workflow that tags each new recipe version.
- First draft recipe: `ospf-multi-area`.
