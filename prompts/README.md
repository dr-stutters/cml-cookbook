# Saved prompts

A saved prompt is a ready-made instruction you keep and run again whenever you need a lab. Recipes say *what* a lab is. A saved prompt says *how to drive a whole job* around one or more recipes: which recipe and version, your environment's values, the order of the work, guard rails for shared systems, drills, and tearing everything down again.

| Prompt | Recipes | Tools it expects |
|---|---|---|
| [`ftd-sdwan.md`](ftd-sdwan.md) | `ftd-sdwan-single-hub`, `ftd-sdwan-dual-hub`, `ftd-sdwan-ha-hub` | Anything that can drive CML, plus FMC's REST API or you clicking through FMC |
| [`ftd-sdwan-mcp.md`](ftd-sdwan-mcp.md) | The same | [cml-mcp-server](https://github.com/dr-stutters/cml-mcp-server) v0.11.0-rc2 or later and [fmc-mcp-server](https://github.com/dr-stutters/fmc-mcp-server) v0.14.2 or later, with writes and the dangerous tier on |

Both build the same lab and run the same checks. The MCP one maps every step to a tool call: one call to `fmc_create_sdwan_topology` builds the whole SD-WAN overlay. It also offers an OSPF overlay variant.

## Before you use one

1. **Replace the lab values.** Each prompt has a "My lab values" table near the top. The values in it (198.18.x.x addresses, an FMC at 198.18.134.76) come from the author's lab. Edit them to match yours.
2. **Don't save passwords in the file.** The agent asks for them when it needs them. The example passwords in the prompts and READMEs are made up, so never use them on a real device.
3. **Check what the recipe assumes.** The FTD SD-WAN recipes need an FMC that already exists, runs 7.6 or later, and is registered to a Smart Account with Export-Controlled Features enabled. The labs don't include an FMC.

## Using one in Claude Code

The prompts have Claude Code command frontmatter, so you can save one as a slash command. For yourself, in every project:

```bash
mkdir -p ~/.claude/commands && curl -fsSL -o ~/.claude/commands/ftd-sdwan.md https://raw.githubusercontent.com/dr-stutters/cml-cookbook/main/prompts/ftd-sdwan.md
```

Or for one project, so everyone working on it gets it: save it as `.claude/commands/ftd-sdwan.md` in that project. Then edit the lab values and run it:

```
/ftd-sdwan single-hub
/ftd-sdwan dual-hub check
/ftd-sdwan single-hub@0.1.0 drill
/ftd-sdwan single-hub teardown
```

The command name is the file name, so save `ftd-sdwan-mcp.md` the same way to get `/ftd-sdwan-mcp`.

## Using one with any other agent

Open the file, edit the lab values, and paste everything below the frontmatter into the agent. Replace the `Arguments: $ARGUMENTS` line with what you want, for example `Arguments: dual-hub build`. To reuse it, keep your edited copy (in a project's instructions, a snippet manager or a file next to your lab notes) and paste it again with different arguments.

## Arguments

| Argument | Values | Default |
|---|---|---|
| Topology | `single-hub`, `dual-hub`, `ha-hub`, optionally with `@<version>` to pin the recipe version | `single-hub` |
| Mode | `build` (build, configure FMC, run the checks), `check` (re-run the checks on an existing lab), `drill` (run the failover drills in the recipe's README), `teardown` (remove everything from FMC and CML) | `build` |
| `overlay=ospf` | MCP prompt, `single-hub` only: OSPF over the tunnels instead of iBGP, reported as a variant | off |

Pin a version (`single-hub@1.0.0`) when you want the same lab every time. Without one you get the recipe as it is on `main`.

## What they change

A `build` creates objects, devices and VPN topologies in your FMC, and a lab in your CML. Everything in FMC is named with the recipe's prefix (`sdwan-single-`, `sdwan-dual-` or `sdwan-ha-`), and the prompts tell the agent never to touch or deploy anything else. They also make it say what it's about to change and ask before anything that deletes or deploys. Run `teardown` when you're done: FMC outlives the lab, and leftovers make the next build stop at preflight.
