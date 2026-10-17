# Changelog: campus-3-tier

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [0.2.0] - 2026-10-17

First real run on CML 2.10.0 with IOL XE and IOL L2 XE 17.18.02.

### Fixed

- Moved `passive-interface default` and `no passive-interface Ethernet0/1` on dist2 and dist3 into a second `router ospf 1` block after the interfaces. IOS rejected `no passive-interface Ethernet0/1` at boot because Ethernet0/1 was still a Layer 2 port, so the uplinks stayed passive and neither distribution switch formed an adjacency with core1.

### Changed

- dist2 and dist3 now run OSPF with each other over VLAN 99 (point-to-point), so a distribution switch that loses its uplink routes through its peer. `dist2-ospf-neighbors` and `dist3-ospf-neighbors` now expect two neighbors.

### Removed

- HSRP uplink tracking (`track 1 interface Ethernet0/1 line-protocol` and `standby ... track 1 decrement 20`). The IOL Layer 2 image has no object tracking, so IOS rejected the `track` line at boot and the HSRP lines tracked nothing.

### Added

- Test runs recorded in `tested_on`: 0.1.0 failed as described above, and 0.2.0 passes all 17 checks on CML 2.10.0 with IOL XE and IOL L2 XE 17.18.02. Also added `ram_mb`.

## [0.1.0] - 2026-10-17

### Added

- First draft: a routed core, a distribution pair with OSPF and HSRP for three VLANs, and two dual-homed access switches on Rapid PVST+, with spanning-tree roots aligned to the HSRP active routers. Not yet tested on a real CML.
