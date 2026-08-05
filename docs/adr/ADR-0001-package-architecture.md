# ADR-0001

## Title

Adopt a modular package architecture.

## Status

Accepted

## Context

The project began as a collection of standalone scripts.

As functionality expanded, maintaining a flat structure became increasingly difficult.

## Decision

The project will use a modular package architecture organized by responsibility.

Examples include:

- collectors
- notifications
- reports
- configuration
- scoring
- utilities

Each module should have a single responsibility.

## Consequences

Benefits:

- Easier testing
- Better maintainability
- Simpler onboarding
- Cleaner separation of concerns
- Scalable architecture

Trade-offs:

- Slightly more files
- More imports
- Higher initial organization cost

These trade-offs are acceptable given the long-term goals of the project.