# Testing Guide

Homelab Guardian uses automated tests to protect monitoring, scoring, reporting, and notification behavior.

## Test Framework

The project uses pytest.

Run all tests from the repository root:

```bash
PYTHONPATH=src python -m pytest