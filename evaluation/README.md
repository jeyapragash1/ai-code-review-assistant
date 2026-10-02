# Evaluation Fixtures

This directory contains deliberately vulnerable evaluation fixtures for the AI-Powered GitHub Code Review Assistant.

These files are not production application code. They must never be imported, executed, packaged into the application, or used as runtime examples. They exist only to measure static-analysis and AI-review accuracy against known ground-truth findings.

The first fixture, `fixtures/python/insecure_user_lookup.py`, contains three intentionally reviewable issues:

- SQL injection from inserting user-controlled `user_id` into a SQL query with string formatting.
- Missing validation for `user_id`.
- Weak error handling that catches every exception and hides failures by returning `None`.

The matching `expected-findings.json` file documents the expected results for automated evaluation. This Pull Request should remain open as an evaluation target and should not be merged into `main`.
