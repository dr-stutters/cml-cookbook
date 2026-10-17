# Changelog: ospf-multi-area

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [0.1.1] - 2026-10-17

### Added

- First real test run: all 10 checks pass on CML 2.10.0 with IOL XE 17.18.02. Recorded in `tested_on`, along with `ram_mb`.

## [0.1.0] - 2026-10-16

### Added

- First draft: five IOL routers in three OSPF areas, with area 2 totally stubby and r4 redistributing a connected LAN. Not yet tested on a real CML.
