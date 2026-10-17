# Changelog: ospf-multi-area

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [1.0.1] - 2026-10-17

### Changed

- README: how to import the CML lab file now attached to each release (made by `cookbook render`). The lab itself is unchanged.

## [1.0.0] - 2026-10-17

### Changed

- First stable release. The topology, configs and checks are unchanged from 0.1.1. A second, independent run, rebuilt from a fresh clone of the GitHub repo at 088954b, passed all 10 checks on CML 2.10.0 and is recorded in `tested_on`.

## [0.1.1] - 2026-10-17

### Added

- First real test run: all 10 checks pass on CML 2.10.0 with IOL XE 17.18.02. Recorded in `tested_on`, along with `ram_mb`.

## [0.1.0] - 2026-10-16

### Added

- First draft: five IOL routers in three OSPF areas, with area 2 totally stubby and r4 redistributing a connected LAN. Not yet tested on a real CML.
