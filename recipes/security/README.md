# Security

Firewalls, identity and policy: FTD and FMC, ISE (802.1X, MAB, TrustSec), VPNs, and labs that integrate with external security appliances.

See [conventions](../../docs/conventions.md#categories) for which category a recipe belongs in.

<!-- catalog:start -->

| Recipe | What it builds | Nodes | Tier | Status | Version |
|---|---|---|---|---|---|
| [FTD internet edge with FMC](ftd-internet-edge/) | An FTDv internet edge managed by an FMCv in the same lab: the FTD registers itself at day 0, then FMC gives it zones, an access policy that blocks one site, a default route and PAT, so an inside host reaches a simulated internet that has no route back to it. | 4 | free | draft | 0.1.0 |

<!-- catalog:end -->
