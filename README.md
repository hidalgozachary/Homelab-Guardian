# Homelab Guardian

Homelab Guardian is a Python-based monitoring and automation project that I am building for my personal homelab.

The project currently runs locally on macOS while I prepare my Unraid server. Its purpose is to collect system-health information, identify potential issues, and create structured reports that can later be expanded into notifications, service monitoring, backup validation, and AI-assisted incident summaries.

## Current Features

- Collects CPU utilization
- Collects memory utilization
- Collects disk utilization
- Detects hostname and operating system
- Records the active Python version
- Evaluates system metrics against warning thresholds
- Displays a readable terminal health report
- Saves each report as timestamped JSON
- Returns a clear success or failure exit code

## Current Status

**Version:** 0.1.0  
**Environment:** Local macOS development and testing  
**Server deployment:** Planned for Unraid

The physical homelab server is still being prepared. Current features are being developed and tested locally so they can later be moved into the Unraid environment.

## Planned Homelab Services

- Unraid
- Docker
- Immich
- Tailscale
- Automated backups
- Infrastructure monitoring
- Remote health notifications
- Panda Innovations storage and services

## Planned Guardian Features

- Configurable warning thresholds
- Persistent application logging
- Historical metric tracking
- Network and DNS health checks
- Docker container monitoring
- Immich health monitoring
- Tailscale connectivity monitoring
- Backup validation and retention checks
- Email or Discord notifications
- HTML health reports
- AI-assisted incident summaries
- Storage-growth analysis and capacity forecasting

## Project Structure

```text
Homelab-Guardian/
├── docs/
│   ├── architecture.md
│   └── roadmap.md
├── powershell/
│   └── Get-SystemHealth.ps1
├── sample-output/
├── src/
│   ├── backup_manager.py
│   └── guardian.py
├── .gitignore
├── README.md
└── requirements.txt
```
