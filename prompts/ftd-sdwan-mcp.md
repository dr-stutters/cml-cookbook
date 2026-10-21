---
description: Build, check, drill or tear down a CML Cookbook FTD SD-WAN lab with cml-mcp-server and fmc-mcp-server
argument-hint: "[single-hub|dual-hub|ha-hub][@version] [build|check|drill|teardown] [overlay=ospf]"
---

# FTD SD-WAN lab from the CML Cookbook, with the MCP servers

Arguments: $ARGUMENTS

<!-- Pasting this file into an agent instead of running it as a command? Replace the line above
     with your choice, for example: Arguments: single-hub build -->

Build, check, drill or tear down one of the FTD SD-WAN recipes from
https://github.com/dr-stutters/cml-cookbook in my CML, configured by my existing FMC, using two
MCP servers:

- [cml-mcp-server](https://github.com/dr-stutters/cml-mcp-server) v0.11.0-rc2 or later, for CML;
- [fmc-mcp-server](https://github.com/dr-stutters/fmc-mcp-server) v0.14.2 or later, for FMC.

Both need `MCP_ENABLE_WRITES=true` and `MCP_ENABLE_DANGEROUS=true`: importing labs, registering
devices, deploying and deleting are in those tiers. Call `cml_status` and `fmc_status` first, and
stop if either server is unreachable or a tier is off.

## 1. What to do

Read the arguments:

- **Topology** (first word, default `single-hub`): `single-hub` is the recipe
  `ftd-sdwan-single-hub`, `dual-hub` is `ftd-sdwan-dual-hub`, `ha-hub` is `ftd-sdwan-ha-hub`, in
  `recipes/security/<recipe id>/`.
- **Version** (optional, `single-hub@0.1.0`): read the recipe at the git tag
  `<recipe id>/v<version>`. Without one, use `main`.
- **Mode** (default `build`): `build`, `check`, `drill` or `teardown`.
- **`overlay=ospf`** (optional, `single-hub` only): see section 5.

If the recipe doesn't exist at that version, say so and stop. If it's `draft`, tell me before
you start.

## 2. My lab values

> **These are from the author's lab. Replace them with your own before you run this prompt.**

| Value | Mine |
|---|---|
| FMC | `198.18.134.76`, domain `Global` (fmc-mcp-server is already pointed at it) |
| Management network | mask `255.255.192.0`, gateway `198.18.128.1`, DNS `198.18.133.1` |
| `single-hub` management addresses | hub1 `198.18.128.224`, spoke2 `.225`, spoke3 `.226`, spoke4 `.227` |
| `dual-hub` management addresses | hub1 `198.18.128.228`, hub2 `.229`, spoke3 `.230`, spoke4 `.231` |
| `ha-hub` management addresses | hub1 `198.18.128.232`, hub2 `.233`, spoke3 `.234`, spoke4 `.235` |

These map onto the recipe's inputs: `fmc_ip`, `mgmt_mask`, `mgmt_gateway`, `mgmt_dns` and one
`<node>_mgmt_ip` per FTD.

**Ask me for the FTDs' `admin_password` when you need it** (example format, made up:
`Sdwan#Lab-2026`). Never echo, log or save it. The FMC and CML logins live in the MCP servers'
own configuration, so you never need them.

## 3. Ground rules

- The recipe's `recipe.yaml` is the source of truth. Follow the repo's `AGENTS.md` for preflight,
  build, boot, steps, checks and the report. The tool calls below are one way to do each step.
- **This prompt assumes an FMC already exists**, runs 7.6 or later, and is registered to a Smart
  Account with **Export-Controlled Features enabled**. The lab doesn't include an FMC.
- **Every write tool previews first.** A call without `confirm` changes nothing and returns a
  preview and a token.
  - Show me each preview. Confirm only after I approve it. I may approve a batch of creates in one
    step at once.
  - Never confirm a deletion, deploy, registration or lab stop without asking.
  - Don't script confirmations.
- **My FMC is shared with other work.** Create, change, deploy or delete only:
  - things whose names start with the recipe's prefix (`sdwan-single-`, `sdwan-dual-` or `sdwan-ha-`);
  - the hub tunnel interfaces the recipe names (`sdwan-dvti...`);
  - this lab's own FTDs.

  Always pass `devices=[...]` to `fmc_deploy`: without it, it deploys every device with pending
  changes.
- Don't quietly fix the lab to make a check pass. Tell me exactly what you changed and that the lab
  no longer matches the recipe.

## 4. `build`

**Preflight**

- `fmc_status`: the FMC version is 7.6 or later.
- `fmc_license_status(check_policies=false)`: `regStatus` REGISTERED and `exportControl` true.
- `fmc_list_devices(name=<prefix>)` and `fmc_list_objects` / `fmc_find_object` for the prefix:
  expect nothing. If something exists, a previous build wasn't torn down: stop and ask.
- The management addresses: none of them should answer a ping or appear in `fmc_list_devices`.
- `cml_list_node_definitions`: `ftdv` and `iol-xe` exist.

**Build the lab**

1. Render it with the cookbook CLI:
   - `pip install "cml-cookbook @ git+https://github.com/dr-stutters/cml-cookbook"`
   - `cookbook render <recipe id> -o lab.yaml --input name=value ...`
2. Pass the file's contents to `cml_import_lab(topology_yaml=...)`. The file contains the admin
   password: don't print it, and delete it afterwards.
3. `cml_plan_licences(target=<the new lab>)`. If something has to stop to make room, ask me which.
4. `cml_start_lab(lab, wait=false)`, then `cml_wait_for_converged(lab)`. FTDv takes 15–30 minutes.
5. Poll `cml_run_commands(nodes=[the FTDs], commands=['show managers'])` until every FTD lists the
   FMC.

**The FMC steps for `single-hub`** (`dual-hub` and `ha-hub` follow their own `recipe.yaml` with the
same tools):

| Recipe step | Tool calls |
|---|---|
| `fmc-objects` | `fmc_create_security_zone` x3 (`interface_mode='ROUTED'`); `fmc_create_object(type='network')` x3; `fmc_create_access_policy(name='sdwan-single-acp', default_action='BLOCK')` |
| `fmc-register` | `fmc_register_device(name='sdwan-single-hub1', host=<hub1 address>, access_policy='sdwan-single-acp', reg_key='cookbook', performance_tier='FTDv5')`, once per FTD. It waits for the first deployment. Newer servers also have `fmc_register_devices` for all four at once. |
| `fmc-interfaces-routes` | `fmc_update_interface(device, interface='Ethernet0/0', logical_name='mpls', security_zone='sdwan-single-wan', ipv4='10.5.N.N/24', enabled=True)` for each port in the recipe's table (16 calls); `fmc_create_static_route(device, interface='mpls', networks=['sdwan-single-mpls'], gateway='10.5.N.5')` and the same for inet and lte (12 calls) |
| `fmc-deploy-underlay` | `fmc_deploy(devices=[the four])` |
| `fmc-sdwan-topology` and `fmc-sdwan-backup-wan` | One call builds both (see below) |
| `fmc-access-rule` | `fmc_create_access_rule(policy='sdwan-single-acp', name='sdwan-single-allow-overlay', action='ALLOW', source_zones=['sdwan-single-inside','sdwan-single-overlay'], destination_zones=['sdwan-single-inside','sdwan-single-overlay'])` |
| `fmc-deploy-overlay` | `fmc_deploy(devices=[the four])` |

The SD-WAN call. It creates exactly the recipe's names: the companion topology
`sdwan-single-wan2`, the pools `sdwan-single-pool` and `sdwan-single-wan2-pool`, the DVTIs
`sdwan-dvti` and `sdwan-dvti-wan2`, and the loopbacks `sdwan-dvti-lo` and `sdwan-dvti-wan2-lo`.

```
fmc_create_sdwan_topology(
  name='sdwan-single', hub='sdwan-single-hub1', hub_wan_interface='mpls',
  hub_inside_interfaces=['inside'], tunnel_zone='sdwan-single-overlay',
  spoke_pool='10.255.1.0/24', hub_backup_wan_interface='inet', backup_wan_pool='10.255.2.0/24',
  spokes=[
    {'device': 'sdwan-single-spoke2', 'wan_interface': 'mpls', 'backup_wan_interface': 'inet', 'inside_interfaces': ['inside']},
    {'device': 'sdwan-single-spoke3', 'wan_interface': 'mpls', 'backup_wan_interface': 'inet', 'inside_interfaces': ['inside']},
    {'device': 'sdwan-single-spoke4', 'wan_interface': 'mpls', 'inside_interfaces': ['inside']}],
  bgp_as=65000, community=1000, multipath=True)
```

**Checks**

- Run the CLI checks with `cml_run_commands` on the device consoles: `show managers`,
  `show interface ip brief`, `show crypto ikev2 sa`, `show bgp summary`, `show route bgp` and
  `ping`.
- Use `cml_check_reachability` (or `ping` on the IOL hosts) for the ping checks.
- `fmc_get_vpn_topology`, `fmc_list_vpn_tunnels` and `fmc_sdwan_status` add FMC's view, but it lags
  by minutes: the recipe's checks decide.

**Report:** a table of every check (ID, pass or fail, and the output for failures), whether the
recipe passed as a whole, and how long the build took. Then list what now exists in FMC, and say
that `teardown` removes it.

## 5. `overlay=ospf` (`single-hub` only, a variant)

This builds OSPF over the tunnels instead of FMC's iBGP, without the backup tunnels. The recipe's
BGP checks no longer apply, so report it as a variant, never as a recipe pass.

- Replace the SD-WAN call with:

  ```
  fmc_create_sdwan_topology(name='sdwan-single', hub='sdwan-single-hub1', hub_wan_interface='mpls',
    hub_inside_interfaces=['inside'], tunnel_zone='sdwan-single-overlay', spoke_pool='10.255.1.0/24',
    overlay='ospf', spoke_loopbacks='10.255.9.0/29', spokes=[...each spoke on mpls with inside...])
  ```

- Then run `fmc_configure_ospf` in area 0:
  - on hub1: the overlay pool `10.255.1.0/24` and `172.16.1.0/24`;
  - on each spoke: its `/32` from `10.255.9.0/29` and its own inside LAN.

  You may need network objects for these, named with the `sdwan-single-` prefix.
- Deploy the four devices.
- Instead of the BGP checks, check that every spoke has OSPF routes to the other LANs
  (`show route ospf`). The ping checks still apply.

## 6. `check`

Find the lab from an earlier `build` with `cml_list_labs` (its title includes the recipe ID). Run
every check in the recipe against it and report. Change nothing.

## 7. `drill`

Run the exercises in the recipe README's **Drills** section, one at a time, with these tools:

- pull a link: `cml_set_link_state(lab, link='spoke2<->isp5', state='down')`, then `up` again;
- degrade a link: `cml_apply_link_scenario`, for example `brownout`, then `cml_clear_link_scenarios`;
- measure: `cml_run_commands` on the hosts (for example `ping 172.16.1.8 repeat 200 timeout 1`);
- FMC's view: `fmc_sdwan_status`. Its path metrics lag by about 5 minutes.

Put the lab back exactly as it was after each drill and re-run the affected checks. Finish with a
table of the drills and what you measured.

## 8. `teardown`

Follow the recipe README's **Clean up** section in order, previewing each call and asking me
first. For `single-hub`:

1. `fmc_delete_s2s_vpn('sdwan-single')` and `fmc_delete_s2s_vpn('sdwan-single-wan2')`, then
   `fmc_deploy(devices=[the four])`.
2. `fmc_delete_interface` on hub1 for `sdwan-dvti`, `sdwan-dvti-wan2`, `sdwan-dvti-lo` and
   `sdwan-dvti-wan2-lo`, then `fmc_deploy(devices=['sdwan-single-hub1'])`.
3. Delete the pools. `fmc_delete_object` doesn't handle address pools, so find each id with
   `fmc_api_call(GET, 'object/ipv4addresspools')` and delete it with
   `fmc_api_call(DELETE, 'object/ipv4addresspools/<id>')`.
4. `fmc_delete_device` for each of the four FTDs.
5. `fmc_delete_policy('sdwan-single-acp')`, then `fmc_delete_object` for the three networks and the
   three zones (`type='security_zone'`).
6. `cml_stop_lab`, then `cml_delete_lab`.

Finish by confirming that `fmc_list_devices` and `fmc_find_object` show nothing with the prefix,
and that `fmc_get_vpn_topology('sdwan-single')` is gone.

## 9. FMC 10.0.1 quirks seen while proving these recipes

- A deploy right after a registration can be refused with "another deployment in progress":
  wait a minute and retry.
- An access rule that uses the overlay zone before any tunnel is in it makes every deploy warn,
  and `fmc_deploy` won't ignore warnings unless you pass `ignore_warning`. That's why the rule comes
  after the SD-WAN topology.
- FMC's tunnel status (`fmc_list_vpn_tunnels`) can read UNKNOWN for minutes after a deploy. Trust
  `show crypto ikev2 sa` on the devices.
- FMC's command API (`fmc_run_show_command`) refuses `show bgp summary` and
  `show path-monitoring`. `cml_run_commands` runs them on the console.
- With two hubs, pass `multipath=False` when the DC LAN routes back through one hub.
- Before `fmc_create_ha_pair`, deploy both units: FMC refuses to pair "dirty" peers.
