# Changelog

All notable changes to Homelab Guardian will be documented in this file.

## [Unreleased]

## [0.9.0] - 2026-08-18

### Added

- Kernel health monitoring through read-only `dmesg` inspection
- Detection of kernel faults, panics, page faults, RCU stalls, hardware errors, OOM events, filesystem errors, I/O errors, NVMe errors, and disk resets
- Kernel health summaries in terminal and operational reports
- Kernel health information in Discord notifications
- SMART monitoring for assigned ATA and NVMe devices
- ATA SMART temperature, power-on hours, reallocated-sector, pending-sector, and uncorrectable-sector reporting
- NVMe SMART temperature, power-on hours, media-error, endurance, and critical-warning reporting
- Docker container inspection and normalized health information
- Docker restart-delta tracking between health reports
- Previous-report loading for stateful Docker restart comparison
- JSON health-report retention with a 30-day production default
- Dedicated tests for JSON report persistence, loading, discovery, and pruning
- PandaServer production deployment through Unraid User Scripts
- Hourly one-shot Homelab Guardian execution
- Persistent scheduled-run logs
- File locking to prevent overlapping scheduled executions
- Secure environment-file support for the Discord webhook
- Production Discord alerting for WARNING and CRITICAL conditions
- Healthy-report suppression for automated hourly monitoring

### Changed

- PandaServer is now a production-validated Homelab Guardian host
- Docker restart scoring now distinguishes historical restart totals from new restart events
- Historical container restart counts no longer cause permanent warning states
- SMART collection now handles device-access failures without crashing the application
- Hardware-error detection was refined to avoid treating benign MCE initialization messages as failures
- Operational reports now include kernel-health information
- Discord reports now surface new Docker restarts without displaying stale restart counts as active problems
- Production notification defaults now disable email and enable Discord alerting
- Healthy scheduled runs now remain silent while still producing JSON reports
- Report history is automatically bounded through configurable retention

### Fixed

- False-positive kernel hardware alerts caused by benign `MCE: In-kernel MCE decoding enabled` messages
- SMART collector behavior when `smartctl` cannot access a device
- Storage collector unavailable-scenario test portability
- Docker restart warnings persisting after the underlying restart event was historical

### Validation

- Full automated test suite passes with 127 tests
- PandaServer validated at `HEALTHY` with a health score of `100 / 100`
- SMART monitoring validated against parity, array, and NVMe cache devices
- Kernel monitoring validated against the live PandaServer kernel log
- Docker restart-history comparison validated against live Immich container data
- Discord webhook delivery validated with a synthetic WARNING report
- Healthy Discord suppression validated in production
- Unraid User Scripts scheduling validated with successful one-shot execution and clean container removal

## [0.8.0] - 2026-08-07

### Added

- PandaServer integration design and operational report contract
- Standard collector execution framework
- Initial read-only Unraid platform collector
- Collector results integrated into the report pipeline
- Docker deployment packaging
- Docker CLI support
- Unraid data sanitization
- Modular PandaServer storage and Docker integration

### Changed

- Homelab Guardian transitioned from a standalone monitoring script toward a modular infrastructure operations application.

## [0.6.5]

### Added

- Top CPU process monitoring
- Top memory process monitoring
- Process diagnostics in terminal reports
- Process diagnostics in email notifications
- Process diagnostics in JSON reports