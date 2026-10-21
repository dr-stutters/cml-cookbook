# Recipe format (schema v1)

A recipe is a folder under `recipes/<category>/<id>/`:

```
recipes/routing-switching/ospf-multi-area/
├── recipe.yaml     # the machine-readable recipe (this document)
├── README.md       # purpose, diagram, walkthrough for humans
├── CHANGELOG.md    # one entry per version
└── configs/        # day-0 config per node, referenced from recipe.yaml
    ├── r1.cfg
    └── r2.cfg
```

`recipe.yaml` is validated against [`schema/v1/recipe.schema.json`](../schema/v1/recipe.schema.json) and then by `cookbook validate`, which adds checks the schema can't express (references between fields, files that must exist, placeholders that must be declared).

The category comes from the folder the recipe lives in. It isn't repeated in `recipe.yaml`.

## Top-level fields

| Field | Required | Description |
|---|---|---|
| `schema_version` | yes | Always `1` for this schema. |
| `id` | yes | Kebab-case, unique across the whole repo, equal to the folder name. Never changes. |
| `title` | yes | Human title, 3–80 characters. |
| `version` | yes | Recipe version, `MAJOR.MINOR.PATCH`. See [versioning](versioning.md). |
| `status` | yes | `draft`, `stable` or `deprecated`. |
| `replaced_by` | when deprecated | `id` of the recipe that supersedes this one. |
| `summary` | yes | One or two sentences, shown in the catalog. |
| `level` | no | `beginner`, `intermediate` or `advanced`. |
| `tags` | no | Kebab-case keywords for search and cross-category grouping (`ospf`, `dot1x`, `campus`). |
| `maintainers` | yes | GitHub handles of the people who look after this recipe. |
| `requirements` | yes | What the CML server needs. See below. |
| `inputs` | no | Values the user supplies at build time. Only for external dependencies. |
| `addressing` | no | The prefixes the recipe uses and what they're for. Documentation only. |
| `topology` | yes | Nodes and links. |
| `steps` | no | Post-boot build steps, for anything day-0 config can't do. |
| `checks` | yes | At least one machine-readable check that proves the lab works. |
| `tested_on` | yes | Real CML runs. Empty (`[]`) for a draft. |

### Status rules

- **`draft`**: written but not yet proven on a real CML. Anyone can use it, but expect rough edges.
- **`stable`**: needs at least one `tested_on` entry with `result: pass`. `cookbook validate` enforces this.
- **`deprecated`**: kept in place so links don't break. Needs `replaced_by`.

## `requirements`

```yaml
requirements:
  cml_min_version: "2.7"        # quote it, or YAML reads 2.7 as a number
  ram_mb: 6144                  # optional; measured on a real run
  images:
    - node_definition: iol-xe
      refplat: true
    - node_definition: ftdv
      refplat: false
      source: https://software.cisco.com/  # required when refplat is false
      notes: Tested with 7.4.x
  external:                     # systems outside CML the lab depends on
    - name: ise
      description: Cisco ISE PAN reachable from the lab's external connector
      min_version: "3.2"
```

- Every `node_definition` used in `topology.nodes` has to be listed under `images`.
- `refplat: true` means the image ships on Cisco's CML reference platform ISO. Recipes should prefer these.
- `ram_mb` is left out until someone measures it. The catalog shows `?` until then.
- The node count and license tier aren't declared; `cookbook index` works them out from the topology. External connectors and unmanaged switches don't count toward CML's node license.

| Tier | Licensed nodes |
|---|---|
| `free` | up to 5 |
| `personal` | up to 20 |
| `personal-plus` | up to 40 |
| `enterprise` | more than 40 |

These match Cisco's published CML license limits at the time of writing. Check Cisco's current CML licensing if in doubt.

## `inputs`

Inputs exist so a public recipe never contains someone's real environment. Use them only for things outside the lab (an ISE address, a RADIUS shared secret, an FMC registration key). Everything inside the lab is fixed.

```yaml
inputs:
  - name: ise_ip
    description: IP address of the ISE PAN, reachable from the external connector
    type: ipv4
    example: 192.0.2.10
  - name: radius_key
    description: RADIUS shared secret configured for this switch in ISE
    type: secret
```

| Field | Description |
|---|---|
| `name` | `lower_snake_case`. |
| `description` | What it is and where to find it. |
| `type` | `string`, `integer`, `ipv4`, `ipv4_prefix`, `ipv6` or `secret`. |
| `required` | Defaults to `true`. |
| `default` | Optional. Not allowed on `secret` inputs. |
| `example` | Shown to the user when asking for a value. Use documentation addresses (`192.0.2.0/24`), or `198.18.0.0/15` when the recipe shows a real lab's values (see [conventions](conventions.md#ipv4-addressing)). |

Config files, inline configs and step commands refer to inputs as `{{ inputs.<name> }}`. `cookbook validate` fails on a placeholder that isn't declared and warns about an input that's never used. Agents must ask the user for required inputs, never invent them, and never echo `secret` values back.

## `addressing`

```yaml
addressing:
  - prefix: 10.255.0.0/24
    purpose: Loopback0 on every router (10.255.0.N/32 on rN)
  - prefix: 10.0.0.0/8
    purpose: Point-to-point links, 10.X.Y.0/24 between rX and rY
```

Documentation only: it tells a reader or an agent where things are without reading every config. Prefixes must be valid networks. See [conventions](conventions.md) for the standard plan.

## `topology`

```yaml
topology:
  nodes:
    - label: r1
      node_definition: iol-xe
      role: Area 0 internal router
      config_file: configs/r1.cfg
      x: 0
      y: -200
    - label: ext
      node_definition: external_connector
      config: System Bridge
  links:
    - a: r1:Ethernet0/1
      b: r2:Ethernet0/1
      description: Area 0
```

**Nodes**

| Field | Description |
|---|---|
| `label` | Node label and hostname. Lowercase, unique in the recipe. |
| `node_definition` | CML node definition ID (`iol-xe`, `ioll2-xe`, `cat8000v`, `ubuntu`, `external_connector`, ...). |
| `image_definition` | Optional pin to a specific image. Leave out to use the server's default. |
| `role` | Short description of what this node does in the lab. |
| `config_file` | Path to a day-0 config, relative to the recipe folder. |
| `config` | Inline day-0 config. Use it for short values such as an external connector's bridge name. Can't be combined with `config_file`. |
| `login` | `username` and `password` for console tools that run CLI commands on the node, when its day-0 config sets a login the node definition doesn't default to (FTDv, FMCv). The password can be an input placeholder. `cookbook render` writes it as the node's pyATS credentials. |
| `ram_mb`, `cpus` | Optional overrides of the node definition's defaults. |
| `x`, `y` | Optional canvas position. |

**Links** join two endpoints written as `<node label>:<interface label>`, with the interface label exactly as CML shows it. Each interface can be used by only one link.

## `steps`

Day-0 config should do as much as possible. Steps are for what it can't do: registering an FTD with FMC, adding a switch to ISE, waiting for a certificate, or anything that has to happen after another node is up.

```yaml
steps:
  - id: register-ftd
    title: Register ftd1 with FMC
    mode: exec
    node: ftd1
    commands: |
      configure manager add {{ inputs.fmc_ip }} {{ inputs.fmc_reg_key }}
    verify: [ftd-registered]
  - id: add-nad
    title: Add sw1 to ISE as a network device
    mode: manual
    instructions: |
      In ISE, add a network device named sw1 with IP 10.254.0.11 and the RADIUS
      shared secret from the radius_key input.
    verify: [radius-reachable]
```

| Field | Description |
|---|---|
| `id` | Kebab-case, unique in the recipe. |
| `title` | One line. |
| `mode` | `config` (send `commands` in configuration mode), `exec` (send them in exec mode) or `manual` (follow `instructions`, possibly with another tool or a GUI). |
| `node` | Target node for `config` and `exec`. |
| `commands` | Required for `config` and `exec`. |
| `instructions` | Required for `manual`. |
| `verify` | Check IDs to run once the step is done. The agent stops and reports if they fail. |

Steps run in the order listed, after every node has booted.

## `checks`

Every check has `id`, `type` and `description`. Agents run them after boot and after the steps, retrying each one until it passes or its `timeout` runs out (default 180 seconds), and report pass or fail for each with the output they saw.

### `ping`

```yaml
- id: ping-r4-r5
  type: ping
  description: r4 reaches r5's loopback across three areas
  node: r4
  target: 10.255.0.5
  source: Loopback0         # optional
  vrf: MGMT                 # optional
  expect:
    success_min: 80         # percent; default 80
```

Passes when the success rate is at least `success_min`. Use `success_max: 0` to prove that traffic is blocked, for example by a firewall policy.

### `cli_match`

```yaml
- id: r1-external-route
  type: cli_match
  description: r1 learns r4's LAN as an OSPF external type 2 route
  node: r1
  command: show ip route 172.16.4.0
  expect:
    pattern: 'type extern 2'
    not_pattern: 'not in table'
```

Runs one exec command. Passes when `pattern` matches the output and `not_pattern` doesn't (either can be left out, not both). Patterns are regular expressions searched across the whole output with multiline mode on; stick to the subset that Python's `re` and PCRE share. Use single quotes in YAML so backslashes survive.

### `ospf_neighbors`

```yaml
- id: r2-ospf-neighbors
  type: ospf_neighbors
  description: r2 is FULL with r1, r3 and r4
  node: r2
  expect:
    count: 3
    state: FULL                # default FULL
    neighbors: [10.255.0.1, 10.255.0.3, 10.255.0.4]   # optional router IDs
```

Passes when exactly `count` OSPF neighbors are in `state`. States are compared by prefix, so `FULL/DR`, `FULL/BDR` and `FULL/  -` all count as `FULL`. If `neighbors` is given, every listed router ID must be among them.

### `bgp_neighbors`

```yaml
- id: edge1-bgp
  type: bgp_neighbors
  description: edge1 has sessions to both ISPs
  node: edge1
  expect:
    count: 2
    state: Established         # default Established
    neighbors: [198.51.100.1, 203.0.113.1]
```

Passes when exactly `count` BGP neighbors (across address families, counted once per neighbor) are in `state`. On IOS, a neighbor showing a prefix count in the `State/PfxRcd` column is `Established`.

### `manual`

```yaml
- id: ftd-registered
  type: manual
  description: ftd1 shows as healthy in FMC
  instructions: In FMC, Devices > Device Management lists ftd1 with a green health status.
```

For anything an agent can't check from a node's CLI. An agent with a suitable tool (an FMC or ISE API, for example) may check it itself; otherwise it asks the user.

## `tested_on`

```yaml
tested_on:
  - recipe_version: 1.0.0
    cml_version: "2.9.0"
    date: "2026-10-16"
    result: pass             # pass, fail or partial
    by: dr-stutters
    images:
      iol-xe: iol-xe-17-15-01
    notes: All checks passed on the first run.
```

A record of real runs. Add an entry each time a recipe is tested, including failures. Adding one is a patch version bump.
