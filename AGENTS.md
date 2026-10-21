# Instructions for AI agents

This file is for any AI agent working with this repository. There are two jobs:

1. [Building a recipe](#building-a-recipe) in someone's CML and proving it works.
2. [Changing this repository](#changing-this-repository): adding or fixing recipes, docs or tooling.

## Building a recipe

The recipe's `recipe.yaml` is the source of truth. Its README explains the lab to humans; if the two disagree, follow `recipe.yaml` and tell the user about the mismatch. The format is defined in [docs/recipe-format.md](docs/recipe-format.md).

These instructions don't assume a particular tool. Use whatever you have that can drive CML: an MCP server for CML, the `virl2_client` Python library, or CML's REST API directly.

If the user ran a saved prompt from [`prompts/`](prompts/), follow it as well: it supplies their environment's values and adds rules (which FMC objects you may touch, when to ask) on top of these instructions. Where the two disagree, the stricter rule wins.

### 1. Find the recipe

- [`index.yaml`](index.yaml) lists every recipe with its path, version, status, size, images and inputs.
- If the user asks for a specific version (`ospf-multi-area@1.2.0`), read the files at git tag `ospf-multi-area/v1.2.0`. Otherwise use `main`.
- Tell the user if the recipe is `draft` (not yet proven on a real CML) or `deprecated` (offer the `replaced_by` recipe instead).

### 2. Preflight

Check all of these before creating anything, and stop with a clear explanation if one fails:

- **CML version** is at least `requirements.cml_min_version`.
- **Images:** every `requirements.images[].node_definition` exists on the server. For one with `refplat: false`, point the user to its `source`.
- **License capacity:** count the nodes in `topology.nodes`, excluding `external_connector` and `unmanaged_switch`. Compare with what the license allows, counting nodes already running in other labs. Suggest which labs to stop if there isn't room.
- **RAM:** if `requirements.ram_mb` is set, check the server has that much free.
- **External systems:** for each `requirements.external` entry, confirm with the user that it exists and is reachable.
- **Inputs:** ask the user for every required `inputs` entry, showing its `description` and `example`. Never invent a value for a required input. Never echo, log or store a `secret` input.

### 3. Build

**If your tool can import CML topology YAML, import the recipe's rendered lab file.** It holds exactly the recipe's nodes, links and day-0 configs, so nothing is copied by hand. Use the `<id>-v<version>.yaml` attached to the recipe's GitHub release, or make it with `cookbook render <id> -o lab.yaml`, adding `--input name=value` for each input. Then skip to step 4.

Otherwise, build it node by node:

- Create one lab titled `<title> (<id> v<version>)`, with the recipe ID and version in the lab description.
- Create each node in `topology.nodes` with exactly its `label` and `node_definition`, plus `image_definition`, `ram_mb`, `cpus`, `x` and `y` when given. If a node has `login`, give your console tool those credentials (with inputs filled in).
- Set each node's day-0 configuration before it starts: the contents of `config_file` (relative to the recipe folder) or the inline `config`. Replace every `{{ inputs.<name> }}` with the user's value. Change nothing else.
- Create each link in `topology.links` between exactly the named interfaces (`<label>:<interface label>`). Create missing interfaces on a node if the tool requires it.

### 4. Start and wait

- Start the lab and wait until every node reports booted. Slow images (FTDv, Catalyst 9000v, NX-OS) can take 10–30 minutes; poll patiently rather than failing early.
- A booted node is not a converged network. Routing protocols need time after boot, which is why checks retry (step 6).
- Look for day-0 lines the device rejected: search each node's console log for `% Invalid input`. Any match is a bug in the recipe. Report it even if every check passes.

### 5. Run the steps

If the recipe has `steps`, run them in order after every node has booted:

- `config`: send `commands` in configuration mode on `node`.
- `exec`: send `commands` in exec mode on `node`.
- `manual`: follow `instructions`. If you have a tool that can do it (an API for FMC or ISE, for example), you may use it. Otherwise ask the user to do it and wait for them to confirm.

After each step, run the checks listed in its `verify`. If any fails, stop and report; don't carry on to the next step.

### 6. Run the checks

Run every check in `checks`. Retry each one until it passes or its `timeout` runs out (default 180 seconds). The exact pass rules for each type are in [docs/recipe-format.md](docs/recipe-format.md#checks):

| Type | Pass rule (short version) |
|---|---|
| `ping` | Success rate is at least `expect.success_min` (default 80) and at most `expect.success_max` (default 100) |
| `cli_match` | `expect.pattern` matches the output of `command` and `expect.not_pattern` doesn't |
| `ospf_neighbors` | Exactly `expect.count` neighbors in `expect.state` (default `FULL`), including any listed `neighbors` |
| `bgp_neighbors` | Exactly `expect.count` neighbors in `expect.state` (default `Established`), including any listed `neighbors` |
| `manual` | Confirmed by the user, or by you with a suitable tool |

### 7. Report

Give the user a table with every check: its ID, pass or fail, and for failures the output you saw. Then say clearly whether the recipe as a whole passed.

- Don't silently fix the lab to make a check pass. If you troubleshoot and change something, say exactly what you changed and that the lab no longer matches the recipe.
- If a check fails in a way that looks like a bug in the recipe, offer to open an issue using the "Recipe doesn't work" template, including the recipe version, CML version and image versions.

### Recording a test run

When the user is a contributor testing a recipe for the repo, add an entry to `tested_on` (see [docs/recipe-format.md](docs/recipe-format.md#tested_on)) with the result, CML version, image versions and date, and follow [Changing this repository](#changing-this-repository). Record failures too.

## Changing this repository

Read [CONTRIBUTING.md](CONTRIBUTING.md) first. The rules that matter most:

- **Run the tools.** Set up with `pip install -e ".[dev]"`, then before finishing any change run:

  ```bash
  cookbook validate
  cookbook index
  pytest
  ```

  `cookbook index` regenerates `index.yaml` and the catalog tables in the READMEs. Never edit those by hand.
- **Bump the version.** Any change to a file inside a recipe folder needs a version bump in its `recipe.yaml` and a matching entry in its `CHANGELOG.md`, following [docs/versioning.md](docs/versioning.md). Check with `cookbook version-check --base origin/main`.
- **Start new recipes from the template:** `cookbook new <category> <id> --title "..." --maintainer <github-handle>`.
- **Follow [docs/conventions.md](docs/conventions.md)** for IDs, labels, addressing, credentials and config layout.
- **Recipes are self-contained.** No shared files or includes between recipes.
- **Never delete or move a recipe.** Deprecate it with `status: deprecated` and `replaced_by`.
- **A recipe is `stable` only after a real run passes.** Never mark a recipe stable, or add a passing `tested_on` entry, without a real CML run that passed.
- **Nothing from anyone's real environment.** No real IP addresses, hostnames, secrets or license keys in recipes. Use `inputs` for anything outside the lab.
- **No Cisco software.** Never commit images, image definitions copied from a server, or license files.
