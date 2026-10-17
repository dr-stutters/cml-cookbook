# Writing a recipe

A walkthrough from idea to pull request. The field reference is [recipe-format.md](recipe-format.md) and the shared rules are in [conventions.md](conventions.md).

## 1. Pick the shape

Before writing anything, decide:

- **What the lab proves.** One sentence: "eBGP to two ISPs with the edge preferring ISP A for outbound traffic." That sentence becomes the summary, and the checks prove it.
- **The category**, from the lab's main purpose ([conventions](conventions.md#categories)).
- **The smallest topology that shows it.** Every node costs RAM and license capacity for everyone who runs it. A recipe that fits in 5 nodes runs on CML-Free.
- **The images.** Prefer reference platform images, and IOL (`iol-xe`, `ioll2-xe`) where it supports the features you need.
- **What's outside the lab.** If it needs ISE, Catalyst Center, a domain controller or anything else that won't run inside CML, list it under `requirements.external`, and make each value from that system (address, key, secret) an `input`.

## 2. Create it from the template

```bash
cookbook new routing-switching bgp-dual-isp-edge --title "BGP dual-ISP edge" --maintainer <your-github-handle>
```

This creates `recipes/routing-switching/bgp-dual-isp-edge/` with a `recipe.yaml`, `README.md`, `CHANGELOG.md` and one example config, all at version `0.1.0` and status `draft`.

## 3. Lay out the topology

In `recipe.yaml`:

1. List every node under `topology.nodes` with its label, node definition and role. Number nodes so the [addressing plan](conventions.md#ipv4-addressing) works.
2. List every link under `topology.links` with exact interface labels. On IOL, start at `Ethernet0/1`.
3. List every node definition you used under `requirements.images`.
4. Summarize the address blocks under `addressing`.
5. Give nodes `x` and `y` positions so the lab opens looking like its diagram.

Run `cookbook validate bgp-dual-isp-edge` often. It catches broken references early.

## 4. Write the day-0 configs

One file per node in `configs/`, named `<label>.cfg`, starting and ending with the [standard lines](conventions.md#day-0-configs). Aim for every node to boot fully configured.

If something can't be done at day-0 (an FTD that has to register with FMC, a switch that has to be added to ISE first), add a `steps` entry for it. Prefer `config` or `exec` steps with exact commands over `manual` steps, and give every step a `verify` list.

## 5. Write the checks

Checks are how an agent, and a future you, knows the lab works. Cover:

- **Adjacencies:** `ospf_neighbors` or `bgp_neighbors` on every router that should have them, with the expected neighbor IDs.
- **The point of the lab:** `cli_match` on the route, policy or state that the recipe is about.
- **End-to-end reachability:** `ping` between the far edges, sourced from loopbacks.
- **Things that must not work**, where that matters: `ping` with `success_max: 0` through a firewall that should block it.

Keep patterns tolerant of small differences between IOS versions: match the key words, not whole lines.

## 6. Write the README

Fill in every section of the template README: what the lab is for, a Mermaid diagram, the node and addressing tables, how to build it, what each check proves, and things to try. Keep the "draft" banner until the recipe is stable.

## 7. Test it on a real CML

If you have a CML server, build the recipe (by hand, or by asking an agent to follow [AGENTS.md](../AGENTS.md)) and run every check. Add a `tested_on` entry with the result, your CML version and the image versions, and fill in `requirements.ram_mb` from what the running lab used.

If you don't have CML, submit it as a draft anyway. Someone who does can test it.

## 8. Open the pull request

```bash
cookbook validate
cookbook index
cookbook version-check
```

Then commit and open a pull request. The template asks you to confirm the checklist.
