# Changelog: ftd-sdwan-dual-hub

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [0.1.0] - 2026-10-21

### Added

- First draft: a primary and a backup SD-WAN hub sharing a data center LAN, and two spokes, on FTDv 10.0 managed by an existing FMC, with three IOL carriers and Alpine hosts. Post-boot FMC steps build the underlay and an SD-WAN topology with a backup hub (each hub with its own dynamic VTI and pool), iBGP with multipath off. Ported from `ftd-sdwan-dual-hub` in cml-mcp-server and laid out like `ftd-sdwan-single-hub`.
