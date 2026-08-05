# 🐼 Homelab Guardian Architecture

## Overview

Homelab Guardian is designed as a modular infrastructure monitoring and operations platform.

Rather than functioning as a collection of standalone scripts, the application follows a layered architecture that separates data collection, health evaluation, report generation, and notification delivery.

Each layer has a single responsibility and communicates only with the adjacent layer.

---

# High-Level Architecture

```text
                 Collectors
                      │
                      ▼
              Health Scoring Engine
                      │
                      ▼
             Operational Report Model
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
      Terminal      JSON      Notifications
                                 │
                           ┌─────┴─────┐
                           ▼           ▼
                       Discord      Gmail
```

---

# Core Components

## Collectors

Collectors gather operational information from infrastructure.

Current collectors include:

- System
- Network

Planned collectors include:

- Docker
- Storage
- Services
- Backups
- Unraid
- Pi-hole
- Tailscale
- Immich
- Jellyfin

Collectors never:

- Generate reports
- Send notifications
- Evaluate health

Each collector should be independent so that failure of one collector does not terminate the application.

---

## Health Scoring Engine

The scoring engine evaluates collected metrics against configured thresholds.

It produces:

- Health Score
- Overall Status
- Issue List

This becomes the single source of truth for infrastructure health.

---

## Operational Report

The operational report combines collected metrics and health evaluation into a standardized operational model.

Every renderer and notification system consumes this model.

No renderer should calculate health independently.

---

## Output Renderers

Renderers present information to the user.

Current renderers:

- Terminal
- JSON

Planned renderers:

- HTML
- Markdown

Renderers never collect data.

---

## Notifications

Notification modules are responsible only for delivery.

Current integrations:

- Gmail
- Discord

Future integrations may include:

- Slack
- Microsoft Teams
- Pushover
- ntfy

Notifications never:

- Collect information
- Evaluate health
- Modify infrastructure

They simply deliver already-generated operational reports.

---

# Current Development Environment

Homelab Guardian is currently developed and tested locally on macOS.

Development focuses on:

- Feature implementation
- Automated testing
- Architecture refinement
- Documentation
- GitHub workflow

This allows rapid iteration before deployment to production infrastructure.

---

# Production Deployment

The primary production deployment target is PandaServer running Unraid.

```text
Internet
      │
      ▼
Home Router
      │
      ▼
Managed Switch
      │
      ▼
PandaServer (Unraid)
      │
      ▼
Homelab Guardian
      ├── Unraid Monitoring
      ├── Docker Monitoring
      ├── Storage Monitoring
      ├── Pi-hole Monitoring
      ├── Uptime Kuma Monitoring
      ├── Tailscale Monitoring
      ├── Backup Verification
      ├── Discord Notifications
      └── Gmail Notifications
```

Future versions may support monitoring multiple Linux hosts and remote systems from a centralized Guardian controller.

---

# Security Principles

Homelab Guardian follows several security principles.

- Secrets are stored in local environment variables.
- Example configuration is provided through `.env.example`.
- Real credentials are never committed.
- Configuration is externalized whenever practical.
- Notification modules must never expose secrets in logs.
- Remote administration is expected to occur through Tailscale.
- Operational reports should never expose sensitive credentials.

---

# Architectural Principles

Every feature should follow these principles.

## One Source of Truth

Health is evaluated once.

Every renderer and notification consumes the same operational report.

---

## Separation of Responsibilities

Collectors collect.

Scoring evaluates.

Renderers render.

Notifications deliver.

Modules should not cross these responsibilities.

---

## Independent Collectors

Each collector should fail gracefully.

Failure of one collector should not terminate the application.

---

## Configuration Over Hardcoding

Environment-specific values belong in:

- settings.json
- Environment variables
- Command-line arguments

Never hardcode deployment-specific configuration.

---

## Testability

Every collector, scoring rule, renderer, and notification pathway should be testable through automated tests.

---

## Graceful Degradation

Unavailable infrastructure should be reported honestly.

Example:

```text
Docker: Not Collected
```

is preferred over falsely reporting healthy status.

---

# Long-Term Vision

Homelab Guardian is intended to evolve into a complete infrastructure operations platform capable of monitoring:

- Unraid
- Linux
- Docker
- NAS devices
- Raspberry Pi systems
- Cloud virtual machines
- Network appliances

Future versions will add:

- Historical analytics
- Capacity forecasting
- Dashboard interface
- Automation
- Multi-host monitoring
- Intelligent operational reporting