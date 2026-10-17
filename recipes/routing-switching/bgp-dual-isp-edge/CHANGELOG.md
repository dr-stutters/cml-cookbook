# Changelog: bgp-dual-isp-edge

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [0.1.0] - 2026-10-17

### Added

- First draft: two edge routers in AS 65001 with eBGP to two simulated ISPs and iBGP between them, ISP A primary through local preference and AS-path prepending, and an outbound prefix list against transit. Not yet tested on a real CML.
