# Coding Standards

These standards apply to all Homelab Guardian code.

## Python Version

The project currently supports Python 3.9 and newer.

New syntax must remain compatible with the oldest supported Python version unless the support policy is deliberately changed.

## General Principles

- Prefer clarity over cleverness.
- Keep functions focused on one responsibility.
- Avoid duplicated logic.
- Use configuration instead of hardcoded environment-specific values.
- Fail clearly and predictably.
- Handle optional integrations gracefully.
- Keep collection, scoring, rendering, and delivery separate.

## Type Hints

Public functions should include type hints for parameters and return values.

Example:

```python
def collect_system_metrics(
    settings: dict[str, object],
) -> dict[str, object]:
    ...