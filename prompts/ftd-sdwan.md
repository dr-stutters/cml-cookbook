---
description: Build, check, drill or tear down a CML Cookbook FTD SD-WAN lab in CML, configured by an existing FMC (any tools)
argument-hint: "[single-hub|dual-hub|ha-hub][@version] [build|check|drill|teardown]"
---

# FTD SD-WAN lab from the CML Cookbook

Arguments: $ARGUMENTS

<!-- Pasting this file into an agent instead of running it as a command? Replace the line above
     with your choice, for example: Arguments: single-hub build -->

Build, check, drill or tear down one of the FTD SD-WAN recipes from
https://github.com/dr-stutters/cml-cookbook in my CML, configured by my existing FMC. Use whatever
tools you have that can drive CML (an MCP server, `virl2_client`, the REST API) and FMC (its REST
API, or ask me to click through its web UI).

## 1. What to do

Read the arguments:

- **Topology** (first word, default `single-hub`): `single-hub` is the recipe
  `ftd-sdwan-single-hub`, `dual-hub` is `ftd-sdwan-dual-hub`, `ha-hub` is `ftd-sdwan-ha-hub`. The
  recipes live in `recipes/security/<recipe id>/`.
- **Version** (optional, `single-hub@0.1.0`): read the recipe at the git tag
  `<recipe id>/v<version>`. Without one, use `main`.
- **Mode** (second word, default `build`): `build`, `check`, `drill` or `teardown`.

If the recipe doesn't exist at that version, say so and stop. If it's `draft`, tell me before
you start.

## 2. My lab values

> **These are from the author's lab. Replace them with your own before you run this prompt.**

| Value | Mine |
|---|---|
| FMC | `198.18.134.76`, domain `Global/mcp-test-leaf` |
| Management network | mask `255.255.192.0`, gateway `198.18.128.1`, DNS `198.18.133.1` |
| `single-hub` management addresses | hub1 `198.18.128.224`, spoke2 `.225`, spoke3 `.226`, spoke4 `.227` |
| `dual-hub` management addresses | hub1 `198.18.128.228`, hub2 `.229`, spoke3 `.230`, spoke4 `.231` |
| `ha-hub` management addresses | hub1 `198.18.128.232`, hub2 `.233`, spoke3 `.234`, spoke4 `.235` |

These map onto the recipe's inputs: `fmc_ip`, `mgmt_mask`, `mgmt_gateway`, `mgmt_dns` and one
`<node>_mgmt_ip` per FTD.

**Passwords: ask me for them when you need them.** Never echo, log or save them, and never write
them into this file. The examples only show the format and are made up:

- `admin_password` for the FTDs, for example `Sdwan#Lab-2026` (strong, no `"` or `\`)
- my FMC login for the REST API, for example `cookbook-api` / `Fmc-Api#Lab-2026`
- my CML login

## 3. Ground rules

- The recipe's `recipe.yaml` is the source of truth. Follow the repo's `AGENTS.md` for preflight,
  build, boot, steps, checks and the report.
- **This prompt assumes an FMC already exists**, runs 7.6 or later, and is registered to a Smart
  Account with **Export-Controlled Features enabled**. The lab doesn't include an FMC. If those
  aren't true, stop and tell me.
- **My FMC is shared with other work.** Create, change, deploy or delete only:
  - things whose names start with the recipe's prefix (`sdwan-single-`, `sdwan-dual-` or `sdwan-ha-`);
  - the hub tunnel interfaces the recipe names (`sdwan-dvti...`);
  - this lab's own FTDs.

  Always name the devices when you deploy, and never deploy to any other device.
- Tell me what you're about to change in FMC before you change it. Ask me first before anything
  that deletes, deploys, registers or unregisters a device, or stops a lab.
- Don't quietly fix the lab to make a check pass. If you change anything the recipe doesn't
  say, tell me exactly what, and that the lab no longer matches the recipe.

## 4. `build`

1. **Preflight**, as in `AGENTS.md`. Also check that:
   - FMC is 7.6 or later and licensed with export control
     (`GET /api/fmc_platform/v1/license/smartlicenses`: `regStatus` REGISTERED, `exportControl` true);
   - nothing named with the recipe's prefix exists in FMC yet. If something does, a previous build
     wasn't torn down: stop and ask me;
   - none of the management addresses answers a ping or is already a device in FMC;
   - CML has the licence capacity and RAM (about 36 GB for four FTDv nodes).
2. **Build the lab.** Prefer `cookbook render <recipe id> -o lab.yaml --input name=value ...`
   (`pip install "cml-cookbook @ git+https://github.com/dr-stutters/cml-cookbook"`) and import the
   file. The rendered file contains the admin password, so don't print it, and delete it afterwards.
   Otherwise build node by node as `AGENTS.md` says.
3. **Start it and wait.** FTDv takes 15–30 minutes to boot, so be patient. Before you register
   anything, wait until `show managers` on every FTD lists the FMC as Pending.
4. **Run the recipe's steps in order**, and run each step's `verify` checks before the next step.
   Use the FMC REST API if you can reach it: the steps give the paths. Otherwise walk me through the
   FMC web UI one step at a time and wait for me to confirm each one.
5. **Run every check**, retrying each until it passes or its timeout runs out. Run the CLI checks
   on the devices' consoles: FMC's command API refuses some of them.
6. **Report:** a table of every check (ID, pass or fail, and the output for failures), whether the
   recipe passed as a whole, and how long the build took. Then list what now exists in FMC, and say
   that `teardown` removes it.

## 5. `check`

Find the lab from an earlier `build` (its title includes the recipe ID). Run every check in the
recipe against it and report as in `build`. Change nothing.

## 6. `drill`

Run the exercises in the recipe README's **Drills** section, one at a time. For each one:
- say what you're about to do;
- do it;
- measure what the drill asks for (loss window, failover time, which path carries traffic);
- put the lab back exactly as it was and re-run the affected checks.

Never leave a link down or conditioned. Finish with a table of the drills and what you measured.

## 7. `teardown`

Follow the recipe README's **Clean up** section in order. Ask me before each deletion and
deploy. At the end:
- confirm that nothing named with the recipe's prefix is left in FMC;
- stop and delete the CML lab (ask first).

If a step fails, stop and tell me what's left.

## 8. FMC 10.0.1 quirks seen while proving these recipes

- FMC only registers devices in a leaf domain ("Device cannot be registered to non-leaf domain"). If the FMC has child domains, create every object, policy, device and topology in the one leaf domain from my lab values.

- A deploy right after a registration can be refused with "another deployment in progress":
  wait a minute and retry.
- Access rules that use the overlay zone before any tunnel is in it make every deploy warn. That's
  why the recipes add that rule after the SD-WAN topology.
- Over REST, create the topology as `AUTO_VPN`. `HUB_AND_SPOKE` silently drops `autoVpnSettings`.
- A spoke's second WAN tunnel is a second SD-WAN topology on the same hub (its own DVTI, loopback
  and pool). Backup interfaces on the spokes of one topology are accepted but never stored.
- FMC's tunnel status lags: a tunnel can read UNKNOWN for minutes after a deploy. Trust
  `show crypto ikev2 sa` on the devices.
- FMC's command API refuses `show bgp summary` and `show path-monitoring`. The device console runs
  both.
- With two hubs, turn BGP multipath off when the DC LAN routes back through one hub: ECMP over both
  hubs makes traffic asymmetric and it gets dropped.
- Before you pair two FTDs for HA, deploy both of them: FMC refuses to pair "dirty" peers.
- Over REST, the first deploy of newly registered FTDs fails with "The changes to Virtual Routers
  may cause traffic disruption" unless `ignoreWarning` is true (the web UI shows the same warning
  with a Proceed button). Later deploys don't need it.
- `GET deployment/deployabledevices` is enough for the deploy version; `expanded=true` returns
  every device's full policy state, which is huge.
- Registration over REST returns at once with a task; it takes about 5 minutes. Poll
  `job/taskstatuses/{id}` or `show managers` on the FTD.
- FMC rate-limits its API (about 110 requests a minute): a 429 changes nothing, so wait and retry.
