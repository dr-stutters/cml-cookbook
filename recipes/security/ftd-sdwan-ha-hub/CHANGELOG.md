# Changelog: ftd-sdwan-ha-hub

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [1.0.0] - 2026-10-22

### Changed

- First stable release. Passed all 17 checks twice on CML 2.10.0 with FMC 10.0.1 and FTDv 10.0.0: once following `prompts/ftd-sdwan-mcp.md`, once following `prompts/ftd-sdwan.md` with FMC's REST API only. The README's drills carry measured results: a switch of the active unit costs about 15-25 seconds and a failed active unit about 50, because the spokes rebuild their tunnels and BGP sessions on the new active unit (the dynamic VTI's sessions aren't carried over, as the first draft claimed). The REST hint for deploying the pair now says FMC lists it under the primary unit's id.

## [0.1.0] - 2026-10-22

### Added

- First draft: an SD-WAN hub that is an active/standby FTDv HA pair (failover link Gi0/4, state link Gi0/5) and two spokes, managed by an existing FMC, with three IOL carriers reaching the pair through shared segments and Alpine hosts. Post-boot FMC steps build the underlay, the HA pair with standby addresses, and an SD-WAN topology with the pair as the hub and an iBGP overlay. Ported from `ftd-sdwan-ha-hub` in cml-mcp-server and laid out like `ftd-sdwan-dual-hub`.
