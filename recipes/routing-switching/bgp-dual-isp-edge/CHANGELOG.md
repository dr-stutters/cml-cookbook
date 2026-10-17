# Changelog: bgp-dual-isp-edge

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [1.0.0] - 2026-10-17

### Changed

- First stable release. The topology, configs and checks are unchanged from 0.1.1. A second, independent run, rebuilt from a fresh clone of the GitHub repo at 088954b, passed all 14 checks on CML 2.10.0 and is recorded in `tested_on`.

## [0.1.1] - 2026-10-17

### Fixed

- Moved each `router bgp` block after the interfaces. IOS rejected `neighbor ... update-source Loopback0` at boot because Loopback0 didn't exist yet, so the iBGP session between edge1 and edge2 stayed Idle. Found on the first real run (CML 2.10.0, IOL XE 17.18.02).

### Added

- Test runs recorded in `tested_on`: 0.1.0 failed as described above, and 0.1.1 passes all 14 checks on CML 2.10.0 with IOL XE 17.18.02. Also added `ram_mb`.

## [0.1.0] - 2026-10-17

### Added

- First draft: two edge routers in AS 65001 with eBGP to two simulated ISPs and iBGP between them, ISP A primary through local preference and AS-path prepending, and an outbound prefix list against transit. Not yet tested on a real CML.
