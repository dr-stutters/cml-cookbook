# Conventions

Shared rules so every recipe looks and reads the same. A recipe can break a convention when the lab needs it to, but should say why in its README.

## Recipe IDs

- Kebab-case: `<technology>-<shape>`, for example `ospf-multi-area`, `bgp-dual-isp-edge`, `campus-3-tier`.
- No version numbers, no category prefix, no platform names unless the platform is the point (`nxos-vxlan-evpn` is fine).
- An ID never changes once the recipe is merged. If the lab changes so much that it needs a new name, it's a new recipe.

## Categories

| Folder | What goes in it |
|---|---|
| `routing-switching` | One protocol or feature on its own: IGPs, BGP, VLANs and STP, first-hop redundancy, multicast. |
| `enterprise` | Whole-network designs: campus, branch and WAN, data center fabrics, SD-WAN. |
| `security` | Firewalls, identity and policy: FTD and FMC, ISE (802.1X, MAB, TrustSec), VPNs, and labs that integrate with external security appliances. |

A recipe goes in the category of its main purpose. Everything else goes in `tags`. A campus with 802.1X on the access layer is `security` if the lab is about 802.1X and `enterprise` if it's about the campus design.

## Node labels

The label is also the hostname. Lowercase, a role prefix and a number:

| Prefix | Role |
|---|---|
| `r` | Router |
| `sw` | Switch (single-tier labs) |
| `core`, `dist`, `acc` | Campus tiers |
| `spine`, `leaf` | Data center fabric |
| `edge` | Internet or WAN edge router |
| `isp` | Simulated service provider |
| `hub`, `spoke` | Hub-and-spoke WAN |
| `ftd`, `fmc`, `asa` | Security appliances |
| `h` | End host (Alpine, Ubuntu, desktop) |
| `srv` | Server (DNS, web, syslog) |
| `ext` | External connector |
| `ums` | Unmanaged switch |

Numbers start at 1. The number is what the addressing plan uses, so keep numbers unique across routing roles within a recipe (`r1`, `r2`, `edge3`, not `r1` and `edge1`).

## Interfaces

- On IOL (`iol-xe`, `ioll2-xe`), `Ethernet0/0` is left free for out-of-band management. Lab links start at `Ethernet0/1`.
- Every connected interface has a description: `to <peer label> <peer interface>`, for example `to r2 Ethernet0/1`.
- Interfaces the lab doesn't use are left out of the config.

## IPv4 addressing

| Use | Prefix | Rule |
|---|---|---|
| Loopback0 / router ID | `10.255.0.0/24` | `10.255.0.N/32` on node N |
| Point-to-point links | `10.X.Y.0/24` | Between nodes X and Y (X < Y); node X is `.X`, node Y is `.Y` |
| LAN and user segments | `172.16.V.0/24` | V is the VLAN ID (or the node number for a routed LAN). Gateway `.1`, HSRP/VRRP physical addresses `.2` and `.3`. |
| In-lab management | `10.254.0.0/24` | `10.254.0.N` on node N |
| Simulated internet | `198.51.100.0/24`, `203.0.113.0/24` | Documentation ranges ([RFC 5737](https://www.rfc-editor.org/rfc/rfc5737)) |
| Examples of external addresses | `192.0.2.0/24` | Only in `inputs` examples and docs |

Point-to-point links use `/24` because `10.1.2.1` and `10.1.2.2` are easier to read in `show` output than a `/31` would be. Labs aren't short of address space.

## IPv6 addressing

All IPv6 comes from the documentation prefix `2001:db8::/32` ([RFC 3849](https://www.rfc-editor.org/rfc/rfc3849)):

| Use | Prefix |
|---|---|
| Loopback0 | `2001:db8:ffff::N/128` |
| Point-to-point links | `2001:db8:X:Y::/64`, node X is `::X`, node Y is `::Y` |
| LANs | `2001:db8:16:V::/64` |

## AS numbers

- Lab-internal ASNs: private range `65000`–`65534`.
- Simulated ISPs and other "public" networks: documentation range `64496`–`64511` ([RFC 5398](https://www.rfc-editor.org/rfc/rfc5398)).

## Routing protocol defaults

- Router ID is always set explicitly to the Loopback0 address.
- OSPF uses process `1`, is enabled per interface (`ip ospf 1 area N`), and Ethernet links between two routers are `ip ospf network point-to-point`.
- In a day-0 file, `router ospf` (and any IGP enabled per interface) comes before the interfaces, so the router ID is set before any interface joins.
- Anything that depends on how the file configures an interface comes after the interfaces. That includes `router bgp` (its `update-source Loopback0` needs the loopback to exist), `passive-interface` for a port the file turns into a routed port with `no switchport`, `tunnel source Loopback0` and `source-interface Loopback0`. IOS rejects these lines at boot when they come too early, and the only sign is that the line is missing from the running config.
- When a routing process needs both, split it into two blocks for the same process: the `router-id` before the interfaces, everything else after them.

## Credentials

Every node uses the same **lab-only** credentials:

| | |
|---|---|
| Username | `cisco` |
| Password / secret | `cisco` |
| Enable secret | `cisco` |

These are public and deliberately weak. A recipe that bridges into a real network through an external connector must say so at the top of its README and must never be exposed to an untrusted network.

Appliances that enforce strong passwords, such as FTDv and FMCv, take theirs from a `secret` input named `admin_password` instead, and the node's `login` says so. Never put a fixed password for a box that sits on a bridged network in a public recipe.

## Day-0 configs

- One file per node: `configs/<label>.cfg`, or `configs/<label>.json` for node definitions whose day-0 config is JSON (FTDv, FMCv).
- The file is the complete config the node boots with, ending in `end`.
- Standard lines at the top of every IOS / IOS-XE file:

  ```
  hostname <label>
  !
  no ip domain lookup
  username cisco privilege 15 secret cisco
  enable secret cisco
  ```

- Standard lines at the bottom:

  ```
  line con 0
   exec-timeout 0 0
   logging synchronous
  line vty 0 4
   login local
  !
  end
  ```

- No placeholders other than declared `{{ inputs.<name> }}`.

## Layout

`x` and `y` are optional, but a recipe with more than a few nodes should set them so the lab opens in CML looking like its diagram. Use steps of 200, with traffic flowing left to right or top to bottom.

## Images

- Prefer reference platform images, and `iol-xe` / `ioll2-xe` where they can do the job: they boot in under a minute and use little RAM.
- `ioll2-xe` (IOL L2 XE 17.18) has no object tracking: `track` isn't a command on it, so HSRP and VRRP can't track an interface or route there. Get the same protection from routing instead, or use a platform that supports tracking.
- Never commit image files, licenses or anything else from Cisco software downloads.
- A recipe that needs a non-refplat image says where to get it in `requirements.images[].source`.
