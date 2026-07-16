# Homelab Guardian Architecture

## Current Architecture

```text
                    Homelab Guardian
                           |
                 Load settings.json
                           |
              Load local .env credentials
                           |
              Collect system health data
              ├── CPU
              ├── Memory
              └── Disk
                           |
               Collect network health
               ├── Internet reachability
               ├── HTTP response status
               ├── Response time
               └── DNS resolution
                           |
             Compare with previous report
                           |
               Evaluate warning thresholds
                           |
              Save JSON report and logs
                           |
               Send Gmail notification
```

## Current Environment

Homelab Guardian currently runs locally on macOS for development and testing.

## Planned Deployment

```text
Internet
   |
Home Router
   |
Managed Switch
   |
Unraid Server
   |
Homelab Guardian
   ├── Docker monitoring
   ├── Immich monitoring
   ├── Tailscale checks
   ├── Backup validation
   ├── Email notifications
   └── Discord notifications
```

## Security Model

- Credentials remain in a local `.env` file.
- `.env` is excluded through `.gitignore`.
- No services are currently exposed publicly.
- Remote access is planned through Tailscale.
- Monitoring output does not include sensitive credentials.
