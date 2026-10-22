# Changelog: ftd-tls-cipher-policy

All notable changes to this recipe. Versions follow the cookbook's [versioning rules](../../../docs/versioning.md).

## [1.0.1] - 2026-10-22

### Changed

- README: results of the step-up experiments. Decrypt - Resign upgrades sessions only when the server preferred a suite FTD can't decrypt (NULL, RC4, Camellia), and downgrades TLS 1.2 ChaCha20, AES-CCM and ARIA to ECDHE-AES128-CBC-SHA the same way. Decrypt - Known Key, Platform Settings SSL and the decryption policy's advanced options don't change a transit session's cipher or version. A two-sided capture shows FTD removing the suites from the forwarded ClientHello. Lab files are unchanged.

## [1.0.0] - 2026-10-22

### Changed

- First stable release. All 12 checks passed twice on CML 2.10.0 with FMC 10.0.1 and FTDv 10.0.0: a clean build of h2 and srv3 from `configs/`, then a rebuild of srv3 with the boot-time ping that refreshes ftd1's ARP entry. ftd1 and the FMC steps were built once, and the findings in the README (TLS fields need a linked decryption policy; Block with reset on version and cipher suite; Decrypt - Resign strips RC4 but mirrors decryptable suites; block rules above the resign rule) were reproduced with fmc-mcp-server 0.16.0's decryption tools.

## [0.1.0] - 2026-10-21

### Added

- First draft.
