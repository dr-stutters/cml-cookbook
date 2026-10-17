# Routing & switching

One protocol or feature on its own: IGPs, BGP, VLANs and STP, first-hop redundancy, multicast.

See [conventions](../../docs/conventions.md#categories) for which category a recipe belongs in.

<!-- catalog:start -->

| Recipe | What it builds | Nodes | Tier | Status | Version |
|---|---|---|---|---|---|
| [BGP dual-ISP edge](bgp-dual-isp-edge/) | Two edge routers in AS 65001, each with eBGP to its own simulated ISP and iBGP between them. ISP A is primary both ways: local preference pulls outbound traffic to it, AS-path prepending toward ISP B pushes inbound traffic to it, and a prefix list stops the enterprise becoming a transit AS. | 4 | free | draft | 0.1.1 |
| [OSPF multi-area](ospf-multi-area/) | Five IOL routers in three OSPF areas: a backbone triangle, a normal area with an ASBR redistributing a LAN, and a totally stubby area that only sees a default route. | 5 | free | draft | 0.1.1 |

<!-- catalog:end -->
