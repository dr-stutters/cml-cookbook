# Contributing

Thanks for helping. There are four main ways to contribute:

- **Ask for a recipe.** Open a [recipe request](https://github.com/dr-stutters/cml-cookbook/issues/new?template=recipe-request.yml).
- **Report a broken recipe.** Open a [recipe bug](https://github.com/dr-stutters/cml-cookbook/issues/new?template=recipe-broken.yml) with the recipe version, your CML version and the image versions.
- **Test a draft on your CML.** Build it, run its checks, and send a pull request adding a `tested_on` entry, whether it passed or failed. This is how drafts become stable.
- **Write or improve a recipe.** See below and [docs/writing-a-recipe.md](docs/writing-a-recipe.md).

## Setup

You need Python 3.10 or newer and git.

```bash
git clone https://github.com/dr-stutters/cml-cookbook.git
cd cml-cookbook
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Before you open a pull request

```bash
cookbook validate          # schema and repo rules
cookbook index             # regenerate index.yaml and the README catalog tables
cookbook version-check     # every changed recipe has a version bump and changelog entry
pytest                     # only needed if you changed the tooling
```

CI runs the same checks and fails the pull request if any of them fail.

## Rules for recipes

- **Use the template.** Start with `cookbook new <category> <id> --title "..." --maintainer <your-github-handle>`.
- **Follow the [conventions](docs/conventions.md)** for IDs, node labels, addressing, credentials and config layout.
- **Configure everything at day-0 if you can.** Use `steps` only for what can't be done in a day-0 config, and give every step a check in `verify`.
- **Give every recipe real checks.** "It booted" isn't a check. Prove the thing the lab is about works.
- **Keep recipes self-contained.** A recipe never reads files from another recipe. Copy what you need.
- **Prefer reference platform images**, and IOL where it can do the job.
- **Include nothing from your real environment.** No real addresses, hostnames, secrets or license keys. Anything outside the lab goes in `inputs`, with documentation addresses (`192.0.2.0/24`) as examples.
- **Include no Cisco software.** Never commit images, licenses or files copied from Cisco downloads.
- **Bump the version.** Every change to a recipe's files needs a version bump and a changelog entry. See [docs/versioning.md](docs/versioning.md).
- **Never delete or move a recipe.** Deprecate it instead.

## Status: draft to stable

New recipes start as `draft`. A maintainer moves one to `stable` once it has at least one `tested_on` entry with `result: pass` from a real CML run, and its checks cover what the lab is for. `cookbook validate` refuses `stable` without a passing run.

## Changes to tooling, schema and docs

- Changes to the CLI need tests in `tests/`.
- A change to the schema that would make an existing valid recipe invalid needs a new schema version (`schema/v2/`). See [docs/versioning.md](docs/versioning.md#the-recipe-format).
- Add a line to the root [CHANGELOG.md](CHANGELOG.md) under `Unreleased` for anything outside `recipes/`.

## Using an AI agent to contribute

That's fine and expected. Point it at [AGENTS.md](AGENTS.md), which has the same rules, and check its work: you're responsible for what you submit. In particular, never let an agent add a passing `tested_on` entry for a run that didn't happen.

## License

By contributing, you agree that your contributions are licensed under the [Apache-2.0 license](LICENSE).
