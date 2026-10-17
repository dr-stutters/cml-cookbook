# Enterprise designs

Whole-network designs: campus, branch and WAN, data center fabrics, SD-WAN.

See [conventions](../../docs/conventions.md#categories) for which category a recipe belongs in.

<!-- catalog:start -->

| Recipe | What it builds | Nodes | Tier | Status | Version |
|---|---|---|---|---|---|
| [Three-tier campus](campus-3-tier/) | A three-tier campus in five nodes: a routed core, a distribution pair that runs OSPF to the core and HSRP gateways for three VLANs, and two dual-homed access switches on Rapid PVST+. Each VLAN's spanning-tree root is also its HSRP active router, so the load splits across both distribution switches. | 5 | free | draft | 0.2.0 |
| [DMVPN branch WAN](dmvpn-branch-wan/) | A head-office hub and two branch spokes joined by DMVPN Phase 3 over a simulated internet. OSPF runs over the mGRE tunnel and sends branch-to-branch routes through the hub, then NHRP redirects build direct spoke-to-spoke tunnels on demand. | 4 | free | draft | 0.1.1 |

<!-- catalog:end -->
