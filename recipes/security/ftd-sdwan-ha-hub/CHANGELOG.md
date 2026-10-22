# Changelog: ftd-sdwan-ha-hub

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [0.1.0] - 2026-10-22

### Added

- First draft: an SD-WAN hub that is an active/standby FTDv HA pair (failover link Gi0/4, state link Gi0/5) and two spokes, managed by an existing FMC, with three IOL carriers reaching the pair through shared segments and Alpine hosts. Post-boot FMC steps build the underlay, the HA pair with standby addresses, and an SD-WAN topology with the pair as the hub and an iBGP overlay. Ported from `ftd-sdwan-ha-hub` in cml-mcp-server and laid out like `ftd-sdwan-dual-hub`.
