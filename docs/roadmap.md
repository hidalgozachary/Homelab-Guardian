# Homelab Guardian Roadmap

This roadmap documents the evolution of Homelab Guardian from a local monitoring utility into a production-ready infrastructure operations platform.

## Completed Releases

### v0.1.0

- CPU monitoring
- Memory monitoring
- Disk monitoring
- JSON report generation
- Terminal health report

### v0.2.0

- JSON configuration
- Configurable thresholds
- Configurable report path

### v0.3.0

- Persistent application logging
- INFO and WARNING log levels

### v0.4.0

- Historical report comparison
- Metric direction and change tracking

### v0.5.0

- Internet reachability checks
- HTTP response-time monitoring
- DNS resolution checks

### v0.6.0

- Gmail SMTP notifications
- Healthy and warning report modes
- Local environment-variable management

### v0.6.5

- Top CPU process monitoring
- Top memory process monitoring
- Process diagnostics in terminal output
- Process diagnostics in JSON reports
- Process diagnostics in email notifications

### v0.7.0 — Application Foundation

- Modular Python package architecture
- Centralized health scoring
- Terminal reporting
- JSON reporting
- Shared operational report format
- Discord webhook notifications
- Architecture and engineering documentation
- Collector runner and standardized collector results
- Migration path from the legacy script

### v0.8.0 — PandaServer Integration

- Unraid platform detection
- Host health collection
- Array and cache utilization
- Storage filesystem and block-device inventory
- Docker collection
- Unraid-specific operational reporting
- PandaServer Docker packaging
- SMART and device-role integration foundation
- Graceful handling of unavailable collectors

### v0.9.0 — PandaServer Production Monitoring

Primary goal: Turn Homelab Guardian into an unattended monitoring system running against PandaServer.

Completed capabilities:

- Production validation on PandaServer
- Hourly execution through Unraid User Scripts
- One-shot Docker runtime
- SMART monitoring for ATA and NVMe devices
- Kernel health monitoring
- Kernel fault and hardware-error detection
- OOM, filesystem, I/O, NVMe, RCU, and disk-reset detection
- Benign MCE message filtering
- Docker health inspection
- Stateful Docker restart-delta tracking
- Historical restart suppression
- Persistent JSON health history
- 30-day report retention
- Discord WARNING and CRITICAL alerts
- Healthy-report suppression
- Persistent scheduled-run logging
- Non-overlapping scheduled executions
- Secure webhook configuration outside source control
- Automated cleanup of temporary Guardian containers
- Full PandaServer validation at HEALTHY / 100

## Planned Releases

### v1.0.0 — Production Release

Primary goal: Formalize Homelab Guardian as a stable, documented production release.

Planned capabilities:

- Installation and deployment documentation
- Upgrade procedure
- Rollback procedure
- Stable production configuration contract
- Structured application logging
- Security review
- Troubleshooting guide
- Supported-platform statement
- Release automation
- Semantic-versioning workflow
- Legacy-script retirement plan
- Full production documentation review

### v1.1.0 — Backup and Historical Intelligence

Primary goal: Expand Guardian from current-state monitoring into operational history and backup assurance.

Potential capabilities:

- CA Appdata Backup verification
- Flash backup verification
- Backup-age thresholds
- Backup-retention checks
- SQLite metric storage
- Trend detection
- Daily summaries
- Weekly summaries
- Storage-capacity forecasting
- Historical alert analysis

### v1.2.0 — Service Monitoring Expansion

Potential capabilities:

- Immich application monitoring
- Jellyfin monitoring
- Audiobookshelf monitoring
- Grafana monitoring
- Prometheus monitoring
- Loki monitoring
- Nextcloud monitoring
- Service-specific health contracts

### v1.3.0 — Web Dashboard

Potential capabilities:

- Browser-based dashboard
- Health history
- Service status
- Historical charts
- Alert history
- Backup status
- Storage trends

### v1.5.0 — Automation and Remediation

Potential capabilities:

- Restart unhealthy containers
- Validate backup archives
- Scheduled maintenance workflows
- Disk-space cleanup recommendations
- Guided remediation actions
- Approval-based automation

### v2.0.0 — Multi-Host Monitoring

Potential capabilities:

- Multiple monitored hosts
- Remote collector agents
- Central Guardian controller
- Host groups
- Cross-host dashboards
- Distributed notifications
- Remote Linux and cloud monitoring

## Future Ideas

- AI-assisted incident summaries
- Suggested remediation actions
- Capacity forecasting
- Daily health summaries
- Weekly operational summaries
- Plugin-based collectors
- Remote agent deployment

## Release Principles

Each release should include:

- A focused scope
- Automated tests
- Documentation updates
- Changelog entries
- Migration notes when necessary
- Clear rollback instructions for production changes