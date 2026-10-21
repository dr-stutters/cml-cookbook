# Changelog: ftd-sdwan-single-hub

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [1.0.0] - 2026-10-21

### Changed

- First stable release. Passed all 22 checks twice on CML 2.10.0 with FMC 10.0.1 and FTDv 10.0.0: once following `prompts/ftd-sdwan-mcp.md`, once following `prompts/ftd-sdwan.md` with FMC's REST API only. The hosts are Alpine VMs (their consoles work where Docker IOL consoles stay silent), the steps say to use a leaf domain when the FMC has child domains, and the REST hints now cover every call in order, including the first deploy's Virtual Routers warning. The README's drills carry measured results.

## [0.1.0] - 2026-10-21

### Added

- First draft: one SD-WAN hub and three spokes on FTDv 10.0, managed by an existing FMC, with three IOL carriers and an Alpine host behind each FTD. Post-boot FMC steps build the underlay, the SD-WAN topology over mpls with an iBGP overlay, and backup tunnels over inet for spoke2 and spoke3. Ported from `ftd-sdwan-single` in cml-mcp-server, re-labelled and re-addressed to the cookbook's conventions.
