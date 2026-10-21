# Changelog

Changes to the cookbook's tooling, schema and docs. Each recipe has its own `CHANGELOG.md` in its folder.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the toolkit uses [semantic versioning](https://semver.org/). See [docs/versioning.md](docs/versioning.md).

## [Unreleased]

### Added

- `cookbook render <id> [--input name=value] [-o FILE]` writes a recipe as a CML topology file to import and start. It uses lab schema 0.2.2 and knows the interface layout of `iol-xe` and `ioll2-xe`. Tested by importing all four stable recipes into CML 2.10.0, where every check passed.
- The release workflow attaches `<id>-v<version>.yaml` to every recipe release that needs no inputs, and `cookbook release-plan --json` reports which ones are `renderable`.

- Recipe format: optional `login` on a node (console credentials, may use an input). `cookbook render` writes it as the node's pyATS credentials.
- `cookbook render` knows `ftdv`, `fmcv`, `external_connector` and `unmanaged_switch`.
- `cookbook render` knows `alpine` (eth0-eth3). It's a KVM VM, so its console works on CML controllers where Docker IOL consoles stay silent.

- Saved prompts in `prompts/`: `ftd-sdwan.md` (any tools) and `ftd-sdwan-mcp.md` (cml-mcp-server and fmc-mcp-server) build, check, drill or tear down the FTD SD-WAN recipes. They work as Claude Code slash commands or pasted into any agent. `prompts/README.md` explains how to use them.

### Changed

- Conventions: input examples, docs and saved prompts may use `198.18.0.0/15` (RFC 2544) when they show a real lab's values, and a README may show a clearly labelled, made-up example for a secret input.
- AGENTS.md: when the user runs a saved prompt, follow it too; the stricter rule wins.
- AGENTS.md: agents whose tools can import CML topology YAML import the rendered lab file instead of building node by node.

### Fixed

- The release workflow gives the Latest badge back to the newest toolkit release after publishing recipe releases. GitHub had been marking recipe releases as Latest despite `--latest=false`.

## [0.1.0] - 2026-10-17

### Added

- Recipe format and JSON Schema v1 (`schema/v1/recipe.schema.json`).
- `cookbook` CLI with `validate`, `index`, `new`, `version-check` and `release-plan`. `render` and `check` are placeholders for now, planned in the Importable labs and Self-checking labs milestones.
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
