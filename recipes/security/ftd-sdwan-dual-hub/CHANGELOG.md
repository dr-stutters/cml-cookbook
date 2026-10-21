# Changelog: ftd-sdwan-dual-hub

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [1.0.0] - 2026-10-21

### Changed

- First stable release. Passed all 19 checks twice on CML 2.10.0 with FMC 10.0.1 and FTDv 10.0.0: once following `prompts/ftd-sdwan-mcp.md`, once following `prompts/ftd-sdwan.md` with FMC's REST API only. The README's drills now carry measured results: the primary hub failover takes about 20 seconds with traffic flowing, and h8's route goes back to hub1 only after hub1's BGP sessions return (going back first lost every ping for about 90 seconds). The Alpine hosts need `sudo` to change routes.

## [0.1.0] - 2026-10-21

### Added

- First draft: a primary and a backup SD-WAN hub sharing a data center LAN, and two spokes, on FTDv 10.0 managed by an existing FMC, with three IOL carriers and Alpine hosts. Post-boot FMC steps build the underlay and an SD-WAN topology with a backup hub (each hub with its own dynamic VTI and pool), iBGP with multipath off. Ported from `ftd-sdwan-dual-hub` in cml-mcp-server and laid out like `ftd-sdwan-single-hub`.
