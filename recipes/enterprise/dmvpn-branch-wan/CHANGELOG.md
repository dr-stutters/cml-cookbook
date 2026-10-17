# Changelog: dmvpn-branch-wan

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [0.1.1] - 2026-10-17

### Added

- First real test run: all 10 checks pass on CML 2.10.0 with IOL XE 17.18.02. Recorded in `tested_on`, along with `ram_mb`.

## [0.1.0] - 2026-10-17

### Added

- First draft: a hub and two spokes on DMVPN Phase 3 over a simulated internet, with OSPF point-to-multipoint on the tunnel and NHRP redirects building spoke-to-spoke tunnels on demand. Not yet tested on a real CML.
