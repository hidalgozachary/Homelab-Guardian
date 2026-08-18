# 🐼 Homelab Guardian

[![Python CI](https://github.com/hidalgozachary/Homelab-Guardian/actions/workflows/python.yml/badge.svg)](https://github.com/hidalgozachary/Homelab-Guardian/actions/workflows/python.yml)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Stable Version](https://img.shields.io/badge/stable-v0.9.0-blue)
![Development](https://img.shields.io/badge/development-v1.0.0-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active%20development-orange)

Homelab Guardian is a modular Python infrastructure monitoring and operations application for self-hosted environments.

It collects operational data through independent collectors, evaluates overall health through a centralized scoring engine, produces consistent reports, maintains historical state, and delivers actionable alerts through supported notification channels.

**PandaServer**, a personal Unraid server, is the first production host monitored by Homelab Guardian.

> Version `0.9.0` is production-validated on PandaServer through Unraid and runs automatically as an hourly monitoring workload.

---

## Project Status

### Current Stable Release

```text
v0.9.0 — PandaServer Production Monitoring
```

Version `0.9.0` moves Homelab Guardian beyond PandaServer integration and into unattended production monitoring.

Current production capabilities include:

- Modular collector-based architecture
- Platform-neutral host monitoring
- Unraid platform and array monitoring
- Array and cache capacity monitoring
- ATA and NVMe SMART monitoring
- Disk temperatures and SMART attributes
- Kernel health monitoring
- Kernel fault and panic detection
- Hardware, MCE, and EDAC error detection
- Out-of-memory event detection
- BTRFS and XFS error detection
- I/O and NVMe error detection
- RCU stall detection
- Disk and controller reset detection
- Docker container state and health monitoring
- Stateful Docker restart-delta detection
- Network reachability monitoring
- DNS resolution monitoring
- Centralized health scoring
- Terminal operational reports
- Persistent JSON reports
- Previous-report comparison
- 30-day report retention
- Discord WARNING and CRITICAL alerts
- Healthy-report notification suppression
- Hourly execution through Unraid User Scripts
- Persistent scheduled-run logs
- Protection against overlapping scheduled runs
- Disposable one-shot Docker execution
- Automated test coverage

### Current Production State

PandaServer runs Homelab Guardian automatically once per hour.

A healthy production execution currently produces:

```text
================================================
                Homelab Guardian
                 Version 0.9.0
================================================

Overall Health
------------------------------------------------
Status:            HEALTHY
Health Score:      100 / 100
```

Healthy runs:

- Generate a JSON health report
- Maintain historical state
- Write a scheduled-run log
- Remain silent in Discord

`WARNING` and `CRITICAL` states generate Discord alerts for review.

### Current Development

```text
v1.0.0 — Production Release
```

Development toward `v1.0.0` focuses on formalizing and hardening the production system established in v0.9.0.

Current priorities include:

- Installation documentation
- Deployment documentation
- Upgrade procedures
- Rollback procedures
- Stable production configuration
- Structured application logging
- Security review
- Troubleshooting documentation
- Supported-platform documentation
- Release automation
- Legacy-script retirement
- Production hardening

---

## Why Homelab Guardian?

Self-hosted environments often rely on several independent monitoring tools:

- Unraid notifications
- Uptime Kuma
- Docker health checks
- Discord webhooks
- Backup applications
- Grafana and Prometheus
- Service-specific dashboards

These tools are valuable, but they do not always provide one consolidated answer to the most important operational question:

> Is the homelab operating normally, and is any action required?

Homelab Guardian provides that consolidated operational view while preserving native monitoring systems as independent safety layers.

It is not intended to replace Unraid alerts, Uptime Kuma, Prometheus, or other specialized monitoring systems.

Instead, Guardian provides a higher-level operational summary across infrastructure domains.

---

## Core Principles

Homelab Guardian follows several engineering principles:

- One source of truth for operational health
- Independent collectors
- Graceful degradation
- Clear separation of responsibilities
- Read-only collection by default
- Configuration instead of hardcoding
- No secrets committed to source control
- Automated tests for new behavior
- Documentation as part of feature development
- Explicit deployment and rollback procedures
- No automatic remediation by default

Collector failures should be represented honestly without crashing the entire monitoring application.

For example:

```text
Host Collector          COLLECTED
Kernel Collector        COLLECTED
Unraid Collector        COLLECTED
Storage Collector       COLLECTED
SMART Collector         COLLECTED
Docker Collector        COLLECTED
Backup Collector        NOT_IMPLEMENTED
```

---

## Production Architecture

PandaServer uses an hourly one-shot deployment model.

```text
                       PandaServer / Unraid
                              │
                              ▼
                       Unraid User Scripts
                        Hourly Execution
                              │
                              ▼
                       run-guardian.sh
                              │
                              ▼
                    homelab-guardian:prod
                              │
                              ▼
                         Collectors
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
      Host                 Storage                Kernel
      Unraid               SMART                  Docker
      Network
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    Previous Report State
                              │
                              ▼
                       Health Scoring
                              │
                              ▼
                    Operational Report
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
          Terminal           JSON           Discord
                              │                │
                        30-Day History    WARNING/CRITICAL
                                             Alerts
```

Each scheduled execution is disposable.

The Guardian container:

1. Starts
2. Collects infrastructure state
3. Loads historical state where required
4. Evaluates health
5. Generates reports
6. Sends alerts when necessary
7. Exits
8. Is automatically removed

No permanent Homelab Guardian container is required.

---

## Application Architecture

Inside the application, responsibilities remain separated:

```text
                    Configuration
                          │
                          ▼
                     Collectors
                          │
                          ▼
                  Collector Runner
                          │
                          ▼
                Historical Context
                          │
                          ▼
                  Health Scoring
                          │
                          ▼
              Operational Report Model
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
      Terminal           JSON         Discord
```

### Collectors

Collectors gather infrastructure data only.

Current production collector domains include:

```text
Host
Network
Unraid
Storage
SMART
Kernel
Docker
```

Collectors do not determine overall application health independently and do not perform remediation.

### Health Scoring

The centralized scoring engine evaluates normalized collector data and produces:

- Health status
- Health score
- Issue list
- Issue summary

Current health states are:

```text
HEALTHY
WARNING
CRITICAL
```

### Reports

Report renderers present already-collected and already-scored information.

Current report formats include:

- Terminal
- JSON
- Discord operational summary

### Notifications

Notification modules deliver completed reports.

Production v0.9.0 alerting uses Discord.

Notification modules do not collect infrastructure data or calculate health independently.

---

## Collector Result Contract

Framework-based collectors return a standardized result structure.

Example:

```json
{
  "name": "storage",
  "status": "COLLECTED",
  "available": true,
  "data": {},
  "error": null
}
```

Collector statuses include:

```text
COLLECTED
UNAVAILABLE
FAILED
NOT_IMPLEMENTED
```

This allows optional or unavailable integrations to degrade gracefully without terminating the complete monitoring run.

---

## Current Collector Capabilities

### Host Collector

The platform-neutral Host Collector gathers:

- Hostname
- Operating system
- Platform
- Kernel
- Architecture
- Python version
- CPU model
- Logical CPU threads
- Physical CPU cores
- CPU utilization
- CPU temperature when supported
- Memory utilization
- Swap utilization
- Uptime
- Boot time
- Load average

The Host Collector supports macOS development environments and Linux/Unraid production environments.

---

### Unraid Collector

The Unraid Collector gathers Unraid-specific platform information including:

- Unraid detection
- Unraid version
- Array state
- Disk assignments
- Assigned-device information
- Platform availability

On non-Unraid systems, the collector returns an unavailable state rather than failing the application.

---

### Storage Collector

The Storage Collector gathers:

- Array capacity
- Array utilization
- Cache capacity
- Cache utilization
- Filesystem type
- Mounted device
- Mount point
- Mount options
- Read-only block-device inventory
- Device name
- Device path
- Device type
- Model
- Serial
- Capacity
- Filesystem
- Mount points
- Conservative device-role information

Collection remains read-only.

---

### SMART Collector

SMART monitoring is integrated with PandaServer device assignments and supports ATA and NVMe devices.

ATA monitoring includes:

- Overall SMART health
- Temperature
- Power-on hours
- Reallocated sectors
- Pending sectors
- Offline uncorrectable sectors

NVMe monitoring includes:

- Overall health
- Temperature
- Power-on hours
- Media errors
- Critical warning state
- Endurance percentage used

SMART device-access failures are handled as unavailable data rather than crashing the complete Guardian run.

Guardian does not automatically start SMART self-tests.

---

### Kernel Health Collector

The Kernel Health Collector performs read-only inspection of the Linux kernel message buffer through `dmesg`.

It detects high-signal infrastructure events including:

- Kernel faults
- Oops events
- Kernel panics
- Page faults
- RCU stalls
- Machine Check events
- Hardware errors
- EDAC errors
- Out-of-memory events
- BTRFS errors
- XFS errors
- I/O errors
- NVMe errors
- NVMe timeouts
- Disk resets
- Controller resets

Known benign initialization output is filtered to reduce false-positive alerts.

For example:

```text
MCE: In-kernel MCE decoding enabled.
```

does not count as a hardware failure.

---

### Docker Collector

The Docker Collector gathers read-only information from the local Docker engine.

Current data includes:

- Container name
- Container image
- Container state
- Docker health-check status
- Exit code
- Lifetime restart count
- Running container count
- Stopped container count
- Healthy container count
- Unhealthy container count
- Restarting container count
- Paused container count

Docker inspection is performed through the Docker CLI and read-only access to the Docker socket.

Guardian does not:

- Restart containers
- Stop containers
- Remove containers
- Update containers
- Delete images

---

### Stateful Docker Restart Detection

A lifetime Docker restart count by itself does not necessarily indicate a current problem.

Guardian therefore compares the current restart count with the previous JSON health report.

Example:

```text
Previous restart count: 6
Current restart count:  6
Restart delta:          0
```

No warning is generated.

If a new restart occurs:

```text
Previous restart count: 6
Current restart count:  7
Restart delta:          1
```

Guardian surfaces the new restart as a current operational issue.

This prevents historical container restarts from creating permanent warning states.

---

### Network Monitoring

Current network checks include:

- Internet reachability
- HTTP response status
- HTTP response time
- DNS resolution

Network failures contribute to health scoring and issue reporting.

---

## Health Scoring

Homelab Guardian evaluates collected infrastructure state using a centralized scoring engine.

A healthy system begins with:

```text
100 / 100
```

Detected issues reduce the health score according to severity.

Examples of conditions considered by the scoring engine include:

- High CPU utilization
- High memory utilization
- High disk utilization
- Network failure
- DNS failure
- Array problems
- Missing disks
- Storage-capacity thresholds
- SMART health failures
- SMART temperature thresholds
- Pending or uncorrectable sectors
- NVMe media errors
- Kernel faults
- Hardware errors
- OOM events
- Filesystem errors
- I/O errors
- Docker unhealthy states
- Docker restart activity
- Non-zero container exit codes

Certain serious conditions can force a `CRITICAL` state independently of the remaining score.

---

## Current PandaServer Example

A production PandaServer execution resembles:

```text
================================================
                Homelab Guardian
                 Version 0.9.0
================================================

Overall Health
------------------------------------------------
Status:            HEALTHY
Health Score:      100 / 100

System Information
------------------------------------------------
Hostname:          PandaServer
Operating System:  Linux / Unraid
Python Version:    3.11

System Health
------------------------------------------------
CPU Usage:         Healthy
Memory Usage:      Healthy
Disk Usage:        Healthy

Network Health
------------------------------------------------
Internet:          Reachable
DNS:               Resolved

SMART Health
------------------------------------------------
Parity             PASSED
Disk1              PASSED
Cache              PASSED

Kernel Health
------------------------------------------------
Status:            HEALTHY
Detected Events:   0

Docker
------------------------------------------------
Running:           Healthy
Unhealthy:         0
Restarting:        0

Issues
------------------------------------------------
- No monitored issues detected.

================================================
Everything looks healthy.
================================================
```

The exact values vary with live infrastructure state.

---

## Operational Reporting

Homelab Guardian produces a consolidated PandaServer operational report containing relevant data from:

- Overall health
- System metrics
- Storage
- SMART
- Kernel health
- Docker
- Network
- Uptime
- Active issues

The original PandaServer integration contract is documented in:

```text
docs/releases/v0.8.0-pandaserver-design.md
```

The production implementation and validation are documented in:

```text
docs/releases/v0.9.0-pandaserver-production.md
```

---

## Persistent Health History

Every successful monitoring execution writes a timestamped JSON report.

Example:

```text
health_report_20260818_204115.json
```

Reports contain the normalized infrastructure state used during that execution.

The production configuration uses a 30-day retention period.

Retention cleanup:

- Runs after a new report is successfully saved
- Deletes only Guardian health-report files
- Leaves unrelated files untouched
- Preserves recent health history
- Prevents indefinite report growth

Historical JSON reports are also used for stateful comparisons such as Docker restart-delta detection.

---

## Production Deployment

PandaServer runs Homelab Guardian through **Unraid User Scripts**.

The production schedule is:

```text
Hourly
```

The User Script launches:

```text
/mnt/cache/appdata/homelab-guardian/run-guardian.sh
```

The production launcher:

- Starts `homelab-guardian:prod`
- Uses host networking
- Provides required read-only system access
- Provides SMART device access
- Mounts the Docker socket read-only
- Mounts required Unraid paths read-only
- Loads the Discord webhook from a protected `.env` file
- Stores JSON reports persistently
- Writes persistent execution logs
- Uses `flock` to prevent overlapping runs
- Returns the Guardian exit code
- Removes the temporary container after completion

Production secrets are stored outside the Git repository.

---

## Scheduled Run Logging

Each scheduled Guardian run writes a persistent log under the production appdata directory.

Example:

```text
guardian_20260818_164112.log
```

Production log files are created with restricted permissions.

The launcher records:

- Run start time
- Guardian output
- Run completion time
- Exit code

This provides a simple audit trail for scheduled execution independent of JSON health history.

---

## Discord Notifications

Discord is the primary production alert channel for v0.9.0.

The webhook is supplied through:

```dotenv
GUARDIAN_DISCORD_WEBHOOK_URL=
```

Production notification behavior is:

```text
HEALTHY   → JSON report + log only
WARNING   → JSON report + log + Discord
CRITICAL  → JSON report + log + Discord
```

Healthy-report suppression avoids unnecessary hourly notification noise.

WARNING and CRITICAL reports use status-specific Discord embed presentation.

Webhook credentials must never be committed to source control.

---

## Gmail Notifications

Gmail notification support exists in the project's earlier/legacy monitoring path.

Environment variables include:

```dotenv
GUARDIAN_EMAIL_FROM=
GUARDIAN_EMAIL_TO=
GUARDIAN_EMAIL_APP_PASSWORD=
```

The v0.9.0 PandaServer production deployment uses Discord as its validated alert channel.

Gmail should not be considered part of the v0.9.0 production notification contract unless separately configured and validated.

---

## Screenshots

Existing screenshots may represent earlier project releases and will be refreshed as the production reporting interface evolves.

### Terminal Health Report

![Homelab Guardian terminal health report](assets/terminal-output.png)

### Gmail Notification

![Homelab Guardian Gmail notification](assets/email-notification.png)

---

## Project Structure

```text
Homelab-Guardian/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE/
│   └── workflows/
├── config/
│   └── settings.json
├── docs/
│   ├── adr/
│   ├── architecture/
│   ├── releases/
│   │   ├── v0.8.0-pandaserver-design.md
│   │   └── v0.9.0-pandaserver-production.md
│   ├── architecture.md
│   ├── roadmap.md
│   ├── CHANGELOG_GUIDE.md
│   ├── CODING_STANDARDS.md
│   ├── CONTRIBUTING.md
│   ├── TESTING.md
│   └── VISION.md
├── logs/
├── sample-output/
├── src/
│   ├── guardian.py
│   └── homelab_guardian/
│       ├── collectors/
│       │   ├── docker.py
│       │   ├── host.py
│       │   ├── kernel.py
│       │   ├── network.py
│       │   ├── runner.py
│       │   ├── smart.py
│       │   ├── storage.py
│       │   ├── system.py
│       │   └── unraid.py
│       ├── notifications/
│       │   └── discord.py
│       ├── reports/
│       │   ├── discord.py
│       │   ├── json_report.py
│       │   ├── operational.py
│       │   └── terminal.py
│       ├── __init__.py
│       ├── __main__.py
│       ├── config.py
│       ├── main.py
│       ├── models.py
│       └── scoring.py
├── tests/
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── Dockerfile
├── LICENSE
├── README.md
├── requirements.txt
└── requirements-dev.txt
```

The legacy `src/guardian.py` remains in the repository while migration and retirement work continues toward v1.0.0.

---

## Requirements

### Development

- Python 3.9 or newer
- `psutil`
- `python-dotenv`
- Development dependencies from `requirements-dev.txt`

Development primarily occurs on macOS.

### Production

The current validated production environment is:

```text
PandaServer
Unraid
Docker
Python 3.11 container runtime
```

SMART monitoring additionally requires access to the assigned block devices and `smartctl`.

Kernel health monitoring requires permission to read `dmesg`.

---

## Installation for Development

Clone the repository:

```bash
git clone https://github.com/hidalgozachary/Homelab-Guardian.git
cd Homelab-Guardian
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

---

## Configuration

Application settings are stored in:

```text
config/settings.json
```

Current configuration areas include:

- Guardian name
- Application version
- Warning thresholds
- SMART temperature thresholds
- Report directory
- Report retention
- Logging
- Network checks
- Process monitoring
- Notification behavior

Environment-specific secrets are stored outside source control.

For local development:

```text
.env
```

For the PandaServer production deployment:

```text
/mnt/cache/appdata/homelab-guardian/.env
```

The production environment file is protected with restricted permissions.

Example:

```dotenv
GUARDIAN_DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_here
```

Real credentials must never be committed.

---

## Running the Application

From the project root:

```bash
PYTHONPATH=src python -m homelab_guardian
```

A normal application execution:

1. Loads configuration
2. Loads environment variables
3. Collects system information
4. Performs network checks
5. Runs Host collection
6. Runs Kernel collection
7. Runs Unraid collection
8. Runs Storage collection
9. Runs Docker collection
10. Resolves assigned devices
11. Runs SMART collection
12. Loads the previous JSON report when available
13. Calculates Docker restart deltas
14. Evaluates overall health
15. Saves a timestamped JSON report
16. Prunes expired reports
17. Prints the terminal report
18. Sends enabled notifications

---

## Running Tests

Run the complete test suite:

```bash
PYTHONPATH=src python -m pytest -q
```

The v0.9.0 release candidate currently passes:

```text
127 passed
```

Run a specific test file:

```bash
PYTHONPATH=src python -m pytest \
  tests/test_storage_collector.py -v
```

Current automated coverage includes:

- Collector execution
- Host collection
- Unraid detection
- Storage collection
- SMART collection
- SMART access failures
- Kernel collection
- Kernel event classification
- Benign kernel-message filtering
- Docker collection
- Docker inspection
- Docker restart-delta calculation
- Health scoring
- SMART scoring
- Kernel scoring
- Docker scoring
- JSON report persistence
- JSON report loading
- Report discovery
- Report retention
- Terminal reporting
- Operational reporting
- Discord report formatting
- Application report construction

GitHub Actions runs automated validation against repository changes.

---

## Security and Operational Safety

Homelab Guardian is designed around read-only monitoring.

The production monitoring scope does not:

- Restart containers automatically
- Stop containers automatically
- Delete containers
- Delete Docker images
- Update containers
- Modify Unraid array assignments
- Start parity checks
- Start SMART self-tests
- Repair filesystems
- Restore backups
- Expose PandaServer publicly
- Commit secrets to Git
- Perform automatic remediation

Automatic remediation may be considered in later releases but must remain:

- Disabled by default
- Explicitly configured
- Logged
- Tested
- Reviewable
- Reversible where practical

Remote administration of PandaServer can remain behind private networking such as Tailscale.

---

## Production Validation

Version `0.9.0` was validated directly against PandaServer.

Production validation included:

- Docker image build
- One-shot production execution
- Host metrics
- Network reachability
- DNS resolution
- ATA SMART monitoring
- NVMe SMART monitoring
- Kernel health monitoring
- Docker inspection
- Historical Docker restart handling
- JSON report persistence
- Report retention behavior
- Persistent launcher logging
- Secure environment-file loading
- Synthetic Discord WARNING delivery
- Healthy Discord suppression
- Unraid User Scripts execution
- Successful temporary-container removal
- Scheduled-run exit code propagation

Validated healthy state:

```text
Status:            HEALTHY
Health Score:      100 / 100
```

---

## Rollback

The PandaServer scheduled deployment can be disabled without modifying the application repository.

The Unraid User Scripts schedule can be disabled to stop future Guardian executions.

Because reports, logs, and secrets are stored outside the temporary container:

- Existing JSON health history remains available
- Existing scheduled-run logs remain available
- The production `.env` remains persistent
- A previously validated Docker image can be restored if required

More formal upgrade and rollback documentation is planned for v1.0.0.

---

## Roadmap

### Completed

```text
v0.7.0 — Application Foundation
v0.8.0 — PandaServer Integration
v0.9.0 — PandaServer Production Monitoring
```

Version `0.9.0` establishes PandaServer as the first production-monitored Homelab Guardian host.

### Current Development

```text
v1.0.0 — Production Release
```

The v1.0.0 milestone focuses on:

- Production hardening
- Installation documentation
- Upgrade procedures
- Rollback procedures
- Security review
- Troubleshooting documentation
- Supported-platform documentation
- Release automation
- Stable configuration contracts
- Legacy-script retirement

### Future Direction

Future releases may expand into:

- Backup assurance
- Historical intelligence
- Metric trend analysis
- Storage-capacity forecasting
- Service-specific monitoring
- Web-based visualization
- Guided remediation
- Multi-host monitoring

See the complete roadmap:

[docs/roadmap.md](docs/roadmap.md)

---

## Documentation

Project documentation includes:

- [Vision](docs/VISION.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Coding Standards](docs/CODING_STANDARDS.md)
- [Testing Guide](docs/TESTING.md)
- [Contributing Guide](docs/CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [PandaServer v0.8.0 Design](docs/releases/v0.8.0-pandaserver-design.md)
- [PandaServer v0.9.0 Production Monitoring](docs/releases/v0.9.0-pandaserver-production.md)
- [Architecture Decisions](docs/adr/)

---

## Development Workflow

Development follows a feature-oriented Git workflow:

```text
Design
  ↓
Feature Branch
  ↓
Implementation
  ↓
Automated Tests
  ↓
Documentation
  ↓
Integration
  ↓
Validation
  ↓
Merge
  ↓
Release
```

Changes should use focused commit messages such as:

```text
feat: add kernel health monitoring
fix: refine kernel hardware error detection
feat: track Docker restart changes across reports
test: add report retention coverage
docs: prepare v0.9.0 release documentation
```

Development changes are made through Git and validated before deployment to PandaServer.

The PandaServer checkout acts as a runtime/deployment target rather than the primary development environment.

---

## Changelog

Project changes are recorded in:

[CHANGELOG.md](CHANGELOG.md)

Major release plans, implementation contracts, and production validation documents are stored under:

```text
docs/releases/
```

---

## Release History

### v0.9.0

PandaServer Production Monitoring.

Major additions include:

- SMART monitoring
- Kernel health monitoring
- Docker restart intelligence
- Persistent health history
- Report retention
- Discord production alerts
- Hourly Unraid deployment
- Production validation

### v0.8.0

PandaServer Integration.

Established the PandaServer integration architecture, Unraid collection foundation, Docker deployment packaging, and operational-report contract.

### v0.7.0

Application Foundation.

Established the modular package architecture, collector framework, centralized scoring, reports, and notification foundation.

---

## License

Homelab Guardian is licensed under the MIT License.

See:

[LICENSE](LICENSE)

---

## Author

**Zachary Hidalgo**

Production Support Engineer building practical experience in:

- Python application development
- Infrastructure monitoring
- Linux and Unraid
- Docker operations
- Networking
- Observability
- Automation
- Testing
- Continuous integration
- Production reliability

Homelab Guardian is developed as both a real operational tool for PandaServer and a flagship infrastructure engineering project.