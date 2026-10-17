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

### Changed

- Design roadmap: the first four recipes are stable at 1.0.0.
- The roadmap now lives in GitHub milestones and issues. `docs/design.md` summarizes it and links there.

### Fixed

- Conventions: anything that depends on how the file configures an interface (`router bgp` with `update-source Loopback0`, `passive-interface` on a port that becomes routed) goes after the interfaces in a day-0 file. Putting it first made IOS drop those lines at boot.
- AGENTS.md: after boot, check each node's console for day-0 lines the device rejected.
- Conventions: note that IOL L2 has no object tracking.
