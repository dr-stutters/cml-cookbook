# Changelog: ftd-sdwan-single-hub

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [0.1.0] - 2026-10-21

### Added

- First draft: one SD-WAN hub and three spokes on FTDv 10.0, managed by an existing FMC, with three IOL carriers and an IOL host behind each FTD. Post-boot FMC steps build the underlay, the SD-WAN topology over mpls with an iBGP overlay, and backup tunnels over inet for spoke2 and spoke3. Ported from `ftd-sdwan-single` in cml-mcp-server, re-labelled and re-addressed to the cookbook's conventions.
