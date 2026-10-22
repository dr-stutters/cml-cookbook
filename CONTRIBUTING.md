# Contributing

This cookbook is written and maintained by [@dr-stutters](https://github.com/dr-stutters) alone. **It doesn't accept pull requests, new recipes or edits to existing recipes from anyone else.** Pull requests from other people will be closed without review.

You're still welcome to:

- **Report a broken recipe.** Open a [recipe bug](https://github.com/dr-stutters/cml-cookbook/issues/new?template=recipe-broken.yml) with the recipe version, your CML version and the image versions.
- **Ask for a recipe.** Open a [recipe request](https://github.com/dr-stutters/cml-cookbook/issues/new?template=recipe-request.yml). The maintainer decides whether to write it.
- **Use, fork and adapt the recipes** under the [Apache-2.0 license](LICENSE).

The rest of this page is the maintainer's own workflow.

## Setup

You need Python 3.10 or newer and git.

```bash
git clone https://github.com/dr-stutters/cml-cookbook.git
cd cml-cookbook
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Before merging a change

```bash
cookbook validate          # schema and repo rules
cookbook index             # regenerate index.yaml and the README catalog tables
cookbook version-check     # every changed recipe has a version bump and changelog entry
pytest                     # only needed if you changed the tooling
```

CI runs the same checks and fails the pull request if any of them fail.

## Rules for recipes

- **Use the template.** Start with `cookbook new <category> <id> --title "..." --maintainer dr-stutters`.
- **Follow the [conventions](docs/conventions.md)** for IDs, node labels, addressing, credentials and config layout.
- **Configure everything at day-0 if you can.** Use `steps` only for what can't be done in a day-0 config, and give every step a check in `verify`.
- **Give every recipe real checks.** "It booted" isn't a check. Prove the thing the lab is about works.
- **Keep recipes self-contained.** A recipe never reads files from another recipe. Copy what you need.
- **Prefer reference platform images**, and IOL where it can do the job.
- **Include nothing from a real environment.** No real addresses, hostnames, secrets or license keys. Anything outside the lab goes in `inputs`, with documentation addresses (`192.0.2.0/24`) as examples.
- **Include no Cisco software.** Never commit images, licenses or files copied from Cisco downloads.
- **Bump the version.** Every change to a recipe's files needs a version bump and a changelog entry. See [docs/versioning.md](docs/versioning.md).
- **Never delete or move a recipe.** Deprecate it instead.

## Status: draft to stable

New recipes start as `draft`. The maintainer moves one to `stable` once it has at least one `tested_on` entry with `result: pass` from a real CML run, and its checks cover what the lab is for. `cookbook validate` refuses `stable` without a passing run.

## Changes to tooling, schema and docs

- Changes to the CLI need tests in `tests/`.
- A change to the schema that would make an existing valid recipe invalid needs a new schema version (`schema/v2/`). See [docs/versioning.md](docs/versioning.md#the-recipe-format).
- Add a line to the root [CHANGELOG.md](CHANGELOG.md) under `Unreleased` for anything outside `recipes/`.

## Using an AI agent

Point it at [AGENTS.md](AGENTS.md), which has the same rules, and check its work. In particular, never let an agent add a passing `tested_on` entry for a run that didn't happen.

## License

The cookbook is licensed under the [Apache-2.0 license](LICENSE).
