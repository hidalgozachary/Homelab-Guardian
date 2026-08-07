# Homelab Guardian Health Rules

## Purpose

This document defines the operational health rules used by Homelab Guardian.

Health rules are documented before they are implemented in code.

The goal is to ensure that health scoring remains:

- Predictable
- Explainable
- Testable
- Conservative
- Safe
- Easy to maintain

Homelab Guardian should answer:

> Is the monitored system operating normally, and is any action required?

---

# Health States

Homelab Guardian supports four overall health states.

## HEALTHY

The monitored infrastructure is operating within expected parameters.

No user action is required.

## WARNING

A condition requires attention but does not represent an immediate threat to data availability or critical service operation.

Examples:

- Elevated CPU usage
- Elevated storage utilization
- A small number of reallocated sectors
- High disk temperature
- Optional service unavailable

## CRITICAL

A condition represents immediate operational risk or a potentially serious hardware/service failure.

Examples:

- SMART overall health failed
- Pending sectors detected
- Offline uncorrectable sectors detected
- NVMe critical warning reported
- Required service unavailable
- Array stopped
- Missing assigned disk

## UNKNOWN

Guardian cannot confidently determine system health.

This may occur when required collectors fail or essential data is unavailable.

---

# Health Engine Principles

The health engine follows these rules:

1. Collector failures must not crash Homelab Guardian.
2. Missing optional information must not automatically become a failure.
3. Unconfigured services must not affect health.
4. Unassigned hardware slots must not affect health.
5. Critical conditions may override the numeric score.
6. Multiple issues may exist simultaneously.
7. Every deduction must produce a human-readable issue.
8. Health scoring must remain deterministic.
9. Collectors gather facts; the health engine interprets them.
10. Notification renderers must not calculate health independently.

---

# Severity Levels

Health rules use the following severities:

```text
INFO
WARNING
CRITICAL
```

## INFO

Operational information that does not reduce health.

## WARNING

A condition worth investigating.

Warnings reduce the health score.

## CRITICAL

A condition that may threaten availability, reliability, or data integrity.

Critical rules significantly reduce the score and may force overall status to `CRITICAL`.

---

# Score Model

Guardian begins with:

```text
100 points
```

Rules deduct points based on severity.

Recommended defaults:

| Severity | Typical Deduction |
|---|---:|
| INFO | 0 |
| WARNING | 5–15 |
| CRITICAL | 25–50 |

The score cannot fall below:

```text
0
```

Initial overall status mapping:

| Condition | Overall Status |
|---|---|
| Critical rule triggered | CRITICAL |
| One or more warnings | WARNING |
| No issues | HEALTHY |
| Required health information unavailable | UNKNOWN |

Critical conditions override numeric score.

For example:

```text
Score: 80
Critical SMART Failure: Yes

Overall Status: CRITICAL
```

The score alone must never hide a dangerous condition.

---

# SMART Health Rules

SMART rules apply only to assigned storage devices that support SMART collection.

Unassigned devices such as an unused `parity2` slot are ignored.

---

## SMART Overall Health Failure

Condition:

```text
smart.passed == false
```

Severity:

```text
CRITICAL
```

Recommended deduction:

```text
-50
```

Example issue:

```text
Parity disk reports SMART overall health failure.
```

---

## SMART Status Unknown

Condition:

```text
smart.passed == null
```

Severity:

```text
WARNING
```

Recommended deduction:

```text
-5
```

Only apply when SMART data was expected to be available.

Example:

```text
Unable to determine SMART health for Disk 1.
```

---

# ATA Disk Rules

These rules apply to ATA/SATA disks.

---

## Reallocated Sectors

Condition:

```text
reallocated_sectors > 0
```

Initial severity:

```text
WARNING
```

Recommended deduction:

```text
-10
```

Example:

```text
Disk 1 has 2 reallocated sectors.
```

Rationale:

Reallocated sectors do not necessarily indicate immediate failure, but they should be monitored for growth.

Future historical analysis may escalate severity if the value increases.

---

## Current Pending Sectors

Condition:

```text
pending_sectors > 0
```

Severity:

```text
CRITICAL
```

Recommended deduction:

```text
-35
```

Example:

```text
Disk 1 has 1 pending sector.
```

Rationale:

Pending sectors may represent unreadable or unstable sectors and require immediate attention.

---

## Offline Uncorrectable Sectors

Condition:

```text
uncorrectable_sectors > 0
```

Severity:

```text
CRITICAL
```

Recommended deduction:

```text
-40
```

Example:

```text
Disk 1 reports 1 offline uncorrectable sector.
```

---

## UDMA CRC Errors

Condition:

```text
crc_errors > 0
```

Initial severity:

```text
WARNING
```

Recommended deduction:

```text
-5
```

Example:

```text
Disk 1 reports 3 UDMA CRC errors.
```

Rationale:

CRC errors may indicate cabling or connection issues rather than disk media failure.

Historical growth will eventually be more important than the absolute value.

---

# NVMe Health Rules

---

## NVMe Critical Warning

Condition:

```text
critical_warning > 0
```

Severity:

```text
CRITICAL
```

Recommended deduction:

```text
-40
```

Example:

```text
Cache NVMe reports a critical warning.
```

---

## NVMe Media Errors

Condition:

```text
media_errors > 0
```

Severity:

```text
CRITICAL
```

Recommended deduction:

```text
-35
```

Example:

```text
Cache NVMe reports 2 media errors.
```

---

## NVMe Endurance Usage

Initial thresholds:

```text
percentage_used >= 80
```

Severity:

```text
WARNING
```

Recommended deduction:

```text
-10
```

At:

```text
percentage_used >= 100
```

Severity:

```text
CRITICAL
```

Recommended deduction:

```text
-30
```

These thresholds may be adjusted after production validation.

---

# Disk Temperature Rules

Temperature rules should be configurable.

Initial defaults:

## HDD / SATA

Warning:

```text
>= 45°C
```

Critical:

```text
>= 55°C
```

## NVMe / SSD

Warning:

```text
>= 70°C
```

Critical:

```text
>= 80°C
```

Temperature rules must use the disk protocol or device class when available.

Example warning:

```text
Parity disk temperature is elevated at 47°C.
```

Example critical:

```text
Cache NVMe temperature is critical at 82°C.
```

Temperature thresholds must eventually move into configuration rather than remain hardcoded.

---

# Unraid Rules

These rules will be implemented incrementally.

---

## Array State

Expected condition:

```text
mdState == STARTED
```

If the array is expected to be operational and the state is not `STARTED`:

Severity:

```text
CRITICAL
```

---

## Missing Assigned Disk

An assigned disk that Unraid reports as missing is:

```text
CRITICAL
```

Unused/unassigned disk slots must not trigger this rule.

---

## Disabled Disk

An assigned disk that Unraid reports as disabled is:

```text
CRITICAL
```

---

## Parity Validity

Invalid parity or an unexpected parity condition should be:

```text
CRITICAL
```

Exact implementation will be defined after PandaServer parity metadata discovery.

---

# Storage Capacity Rules

Initial thresholds:

## Warning

```text
usage >= 85%
```

## Critical

```text
usage >= 95%
```

Applies independently to:

- Array
- Cache/pools

These thresholds should remain configurable.

---

# Host Rules

Existing host rules remain:

## CPU Usage

Warning when:

```text
cpu_percent >= configured threshold
```

## Memory Usage

Warning when:

```text
memory_percent >= configured threshold
```

## Disk Usage

Legacy system disk rule remains supported until storage scoring fully replaces it.

---

# Network Rules

## Internet Unreachable

Severity:

```text
WARNING
```

This should not automatically become critical because Guardian may still be running correctly on the local network.

## DNS Failure

Severity:

```text
WARNING
```

Future required-DNS-service configuration may escalate this.

---

# Docker Rules

Planned.

Initial concepts:

| Condition | Severity |
|---|---|
| Docker unavailable when not required | INFO |
| Docker unavailable with required workloads | CRITICAL |
| Optional container stopped | WARNING |
| Required container stopped | CRITICAL |
| Container unhealthy | WARNING |
| Repeated restart loop | WARNING / CRITICAL |

Exact rules will be implemented with the Docker Collector.

---

# Service Rules

Services must distinguish:

```text
REQUIRED
OPTIONAL
NOT_CONFIGURED
```

An optional service that is not installed must not affect system health.

A required service that is unavailable should be:

```text
CRITICAL
```

---

# Backup Rules

Planned for a later milestone.

Likely conditions:

- Backup completed successfully
- Backup age
- Missing backup
- Verification failure
- Retention failure

Backup scoring must not be enabled until the Backup Collector is production-tested.

---

# Collector Failure Rules

Collectors themselves may fail.

## Optional Collector Failure

Severity:

```text
WARNING
```

or `INFO` depending on configuration.

## Required Collector Failure

Severity:

```text
WARNING
```

If enough required collectors fail that Guardian cannot determine operational health:

```text
UNKNOWN
```

Guardian must continue running whenever possible.

---

# Duplicate Issue Prevention

A single underlying condition should not unnecessarily trigger multiple identical deductions.

Example:

```text
SMART failed
pending sector detected
```

Both may appear as separate issues because they communicate different facts.

However, one failed collector should not create five duplicate "collector unavailable" deductions.

---

# Future Historical Rules

Historical intelligence is outside the initial Health Engine v2 scope.

Future examples:

- Reallocated sector count increased since yesterday
- Disk temperature rising week-over-week
- Storage growth accelerating
- Container restart count increasing
- Backup durations increasing
- SMART error count changed

Historical change may eventually be more significant than absolute values.

---

# Safety

Health evaluation is read-only.

The health engine must never:

- Restart services
- Restart containers
- Modify disks
- Start SMART tests
- Start parity checks
- Delete files
- Repair filesystems
- Modify network configuration

Evaluation produces information only.

Automation must remain a separate subsystem and disabled by default.

---

# Current PandaServer Healthy Baseline

During v0.8.0 discovery, PandaServer established the following healthy reference characteristics:

```text
Parity
SMART: PASSED
Reallocated sectors: 0
Pending sectors: 0
Offline uncorrectable: 0
CRC errors: 0

Disk 1
SMART: PASSED
Reallocated sectors: 0
Pending sectors: 0
Offline uncorrectable: 0
CRC errors: 0

Cache NVMe
SMART: PASSED
Critical warning: 0
Media errors: 0
Percentage used: 0
```

These values serve only as a development baseline.

They must not be hardcoded as expected production values.

---

# Rule Change Policy

Changes to health rules should include:

1. Documentation update
2. Automated tests
3. Explanation of severity
4. Explanation of score impact
5. Production validation where practical

Health-rule changes should be treated as behavioral changes because they can alter notifications and user expectations.