# Release Notes v1.0.5

Released: 2026-06-03

## What's new

- UI polish across the dashboard, logs, reports, and people screens.
- Export UI now shows progress status and disables buttons during export.
- Search and filter UX improved in logs and people screens.
- Update logic hardened for older installations and differently launched app folders.

## Fixes

- Resolved update path handling so updates can install correctly even when the app is started from a different working directory.
- Fixed version bump and update manifest support for older release installations.
- Cleaned up VAWC record form validation and birthdate/age handling.
- Improved update package restore safety by backing up database and existing files.
