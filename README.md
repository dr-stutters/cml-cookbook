# CML Cookbook

[![validate](https://github.com/dr-stutters/cml-cookbook/actions/workflows/validate.yml/badge.svg)](https://github.com/dr-stutters/cml-cookbook/actions/workflows/validate.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Recipes for building network topologies in [Cisco Modeling Labs (CML)](https://developer.cisco.com/modeling-labs/), written so that an AI agent, a script or a person can build the same lab and prove it works.

Each recipe is a fixed topology: the nodes, the links, a day-0 config for every node, and checks that say what "working" means (OSPF neighbors FULL, BGP Established, this host can ping that one). An agent reads the recipe, builds the lab in your CML, runs the checks and tells you which passed.

> **Early days.** The first four recipes are stable, each tested twice on CML 2.10.0. Each one imports straight into CML from its release. More are on the way, along with `cookbook check`. See the [roadmap](docs/design.md#roadmap).

## What's in a recipe

```
recipes/routing-switching/ospf-multi-area/
├── recipe.yaml     # topology, requirements, inputs, steps, checks, test history
├── README.md       # what it's for, diagram, walkthrough
├── CHANGELOG.md    # one entry per version
└── configs/        # day-0 config for each node
```

The full format is in [docs/recipe-format.md](docs/recipe-format.md) and the shared naming and addressing rules are in [docs/conventions.md](docs/conventions.md).

## Using a recipe

**With an AI agent.** Point any agent that can drive CML (an MCP server for CML, [virl2_client](https://pypi.org/project/virl2-client/) scripts, or anything else) at this repo and ask it to build a recipe:

> Build the `ospf-multi-area` recipe from github.com/dr-stutters/cml-cookbook in my CML and run its checks.

[AGENTS.md](AGENTS.md) tells the agent exactly how: checking your CML has the images and license capacity, building, waiting for convergence, running post-boot steps and checks, and reporting.

**Import it.** Each recipe's [GitHub release](https://github.com/dr-stutters/cml-cookbook/releases) has a CML lab file, `<id>-v<version>.yaml`. Download it, import it in CML (Dashboard → Import) and start the lab: every node boots fully configured. You can also make the file yourself with the CLI: `cookbook render <id> -o lab.yaml`. Recipes that need values from your own environment don't ship a lab file; render those with `--input name=value` for each input their README lists.

**By hand.** Each recipe's README lists the nodes, links and addresses. Create them in the CML UI, paste each node's file from `configs/` into its config, and start the lab.

**A specific version.** Every recipe version is tagged `<id>/v<version>`, for example `ospf-multi-area/v1.2.0`. Ask for `ospf-multi-area@1.2.0` to get exactly that version; without a version you get the latest on `main`.

## Saved prompts

Some jobs need more than "build this recipe": choosing between related labs, configuring a shared system such as FMC, failover drills, and cleaning up afterwards. [`prompts/`](prompts/) holds ready-made prompts for those. Save one as a Claude Code slash command or paste it into any agent:

| Prompt | What it does |
|---|---|
| [`ftd-sdwan.md`](prompts/ftd-sdwan.md) | Builds, checks, drills or tears down the FTD SD-WAN recipes with an FMC you already have, using any tools |
| [`ftd-sdwan-mcp.md`](prompts/ftd-sdwan-mcp.md) | The same with [cml-mcp-server](https://github.com/dr-stutters/cml-mcp-server) and [fmc-mcp-server](https://github.com/dr-stutters/fmc-mcp-server) |

[prompts/README.md](prompts/README.md) explains how to save and run them.

## Recipes

Node counts are licensed nodes (external connectors and unmanaged switches don't count). The tier is the smallest CML license that can run the lab: `free` (5 nodes), `personal` (20), `personal-plus` (40) or `enterprise`.

<!-- catalog:start -->

### [Routing & switching](recipes/routing-switching/)

| Recipe | What it builds | Nodes | Tier | Status | Version |
|---|---|---|---|---|---|
| [BGP dual-ISP edge](recipes/routing-switching/bgp-dual-isp-edge/) | Two edge routers in AS 65001, each with eBGP to its own simulated ISP and iBGP between them. ISP A is primary both ways: local preference pulls outbound traffic to it, AS-path prepending toward ISP B pushes inbound traffic to it, and a prefix list stops the enterprise becoming a transit AS. | 4 | free | stable | 1.0.1 |
| [OSPF multi-area](recipes/routing-switching/ospf-multi-area/) | Five IOL routers in three OSPF areas: a backbone triangle, a normal area with an ASBR redistributing a LAN, and a totally stubby area that only sees a default route. | 5 | free | stable | 1.0.1 |

### [Enterprise designs](recipes/enterprise/)

| Recipe | What it builds | Nodes | Tier | Status | Version |
|---|---|---|---|---|---|
| [Three-tier campus](recipes/enterprise/campus-3-tier/) | A three-tier campus in five nodes: a routed core, a distribution pair that runs OSPF to the core and HSRP gateways for three VLANs, and two dual-homed access switches on Rapid PVST+. Each VLAN's spanning-tree root is also its HSRP active router, so the load splits across both distribution switches. | 5 | free | stable | 1.0.1 |
| [DMVPN branch WAN](recipes/enterprise/dmvpn-branch-wan/) | A head-office hub and two branch spokes joined by DMVPN Phase 3 over a simulated internet. OSPF runs over the mGRE tunnel and sends branch-to-branch routes through the hub, then NHRP redirects build direct spoke-to-spoke tunnels on demand. | 4 | free | stable | 1.0.1 |

### [Security](recipes/security/)

| Recipe | What it builds | Nodes | Tier | Status | Version |
|---|---|---|---|---|---|
| [FTD internet edge with FMC](recipes/security/ftd-internet-edge/) | An FTDv internet edge managed by an FMCv in the same lab: the FTD registers itself at day 0, then FMC gives it zones, an access policy that blocks one site, a default route and PAT, so an inside host reaches a simulated internet that has no route back to it. | 4 | free | draft | 0.1.0 |
| [FTD SD-WAN with one hub](recipes/security/ftd-sdwan-single-hub/) | Secure Firewall SD-WAN with one hub and three spokes on FTDv, managed by an FMC you already have: three simulated carriers, a hub-and-spoke IPsec overlay over virtual tunnel interfaces with iBGP generated by FMC's SD-WAN wizard, and a backup tunnel over a second carrier for two spokes. | 11 | personal | stable | 1.0.0 |
| [FTD TLS cipher policy](recipes/security/ftd-tls-cipher-policy/) | An FTDv between a TLS client and a TLS server whose ports each pin a protocol version or cipher suite, managed by an FMC you already have: FTD logs the version and cipher of every TLS session to an in-lab syslog collector without decrypting it, then blocks old versions and weak ciphers, and a Decrypt - Resign rule shows what a terminating firewall does to the cipher on each side. | 3 | free | draft | 0.1.0 |

<!-- catalog:end -->

The same catalog, with tags, images, inputs and test history, is in [index.yaml](index.yaml) for agents and scripts.

## Contributing

New recipes, fixes, and test runs on your own CML are all welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Repository layout

| Path | What's there |
|---|---|
| [`recipes/`](recipes/) | Recipes, one folder per category |
| [`prompts/`](prompts/) | Saved prompts that drive whole jobs around recipes |
| [`schema/v1/`](schema/v1/) | JSON Schema for `recipe.yaml` |
| [`templates/recipe/`](templates/recipe/) | Starting point for a new recipe (`cookbook new`) |
| [`src/cml_cookbook/`](src/cml_cookbook/) | The `cookbook` CLI: validate, index, scaffold, render |
| [`docs/`](docs/) | [Design](docs/design.md), [recipe format](docs/recipe-format.md), [conventions](docs/conventions.md), [versioning](docs/versioning.md), [writing a recipe](docs/writing-a-recipe.md) |
| [`AGENTS.md`](AGENTS.md) | Instructions for AI agents building recipes or changing this repo |

## License

[Apache-2.0](LICENSE). Recipes contain only configuration written for this project; no Cisco software or images are included or distributed.

This project isn't affiliated with or endorsed by Cisco. Cisco and Cisco Modeling Labs are trademarks or registered trademarks of Cisco Systems, Inc.
