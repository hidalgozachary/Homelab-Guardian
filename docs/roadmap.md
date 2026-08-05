# Homelab Guardian Roadmap

This roadmap documents both the completed evolution of Homelab Guardian and the planned transition from a local monitoring utility into a production-ready infrastructure operations platform.

## Completed Releases

### v0.1.0

- CPU monitoring
- Memory monitoring
- Disk monitoring
- JSON report generation
- Terminal health report

### v0.2.0

- JSON configuration file
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

## Current Development

### v0.7.0 — Application Foundation

Status: In progress

Goals:

- Modular Python package architecture
- Centralized health scoring
- Terminal reporting
- JSON reporting
- Shared operational report format
- Discord webhook notifications
- Preserve Gmail notification support
- Project vision and architecture documentation
- Contribution and testing standards
- Architecture Decision Records
- Clear migration path from the legacy script

Completion criteria:

- All existing functionality works through the new package
- Automated tests pass
- Discord notifications are validated
- Documentation reflects the new architecture
- Legacy code has a documented migration path
- The repository is ready for PandaServer integration

## Planned Releases

### v0.8.0 — PandaServer Integration

Primary goal: Make PandaServer the first production monitored host.

Planned capabilities:

- Unraid platform detection
- CPU utilization and temperature
- Memory utilization
- Host uptime and load average
- Array state
- Array and cache utilization
- Assigned disk health
- Parity validity
- Parity-check history
- Disk temperatures
- Docker service state
- Running, stopped, and unhealthy containers
- Tailscale status
- Pi-hole status
- Uptime Kuma status
- Graceful handling of unavailable collectors

Completion criteria:

- Homelab Guardian runs successfully on PandaServer
- The operational report contains live Unraid data
- Collector failures do not crash the application
- Discord receives a complete PandaServer report
- Installation and rollback procedures are documented

### v0.9.0 — Backup and Historical Intelligence

Primary goal: Add operational history and backup assurance.

Planned capabilities:

- CA Appdata Backup verification
- Flash backup verification
- Backup age thresholds
- Backup retention checks
- Historical report comparison
- SQLite metric storage
- Trend detection
- Daily and weekly summaries
- Storage-capacity forecasting foundation

### v1.0.0 — Production Release

Primary goal: Deliver a stable, documented, production-ready release.

Planned capabilities:

- Stable Unraid deployment
- Installation script
- Update script
- Rollback procedure
- Persistent configuration
- Structured logging
- Production scheduling
- Security review
- Full test suite
- User documentation
- Troubleshooting guide
- Release notes
- Semantic versioning
- Supported-platform statement

## Future Releases

### v1.1.0 — Service Monitoring Expansion

Potential capabilities:

- Immich monitoring
- Jellyfin monitoring
- Audiobookshelf monitoring
- Grafana monitoring
- Prometheus monitoring
- Loki monitoring
- Nextcloud monitoring

### v1.2.0 — Web Dashboard

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
- Remote agent deployment
- Plugin-based collectors

## Release Principles

Each release should include:

- A focused scope
- Automated tests
- Documentation updates
- Changelog entries
- Migration notes when necessary
- Clear rollback instructions for production changes