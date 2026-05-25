# VAWC Case Logging System v1.0.4

## Release Date
2026-05-25

## Summary
This release focuses on making the desktop app easier to use and more robust for case management. It includes accessibility and UI improvements, stronger VAWC numbering behavior, safer import/restore handling, enhanced trash workflow, and cleaner PDF export formatting.

## Key Changes

- UI & Accessibility
  - Added theme switching and font scaling controls in the main header.
  - Added a `Text Size` slider in Settings for easier large-text use.
  - Improved overall layout and visual consistency across the app.

- VAWC Number & Add Record
  - Added VAWC number input to the Add Record form.
  - `Date of Report` now appears before VAWC number and drives the year portion.
  - VAWC number now uses the format `VAWC-YEAR-0000` and auto-updates the year.
  - Latest VAWC number reference is shown for the selected report year.
  - Duplicate VAWC checks and save behavior were fixed so the add record page remains open after saving.

- Import / Restore / Trash
  - Added support for importing `.sqlite` and `.sql` database package files.
  - Improved import validation for hashed credentials and legacy plaintext passcodes.
  - Fixed the settings import crash and parent reference errors.
  - Added trash management with multi-select restore and permanent delete.

- PDF Export
  - Updated PDF export to auto-fit table columns and wrap text so generated reports are readable.

- Bug Fixes
  - Fixed startup import failure caused by a missing helper function.
  - Fixed logout behavior and application session handling.

## Files Updated
- `version.txt`
- `update_manifest.json`
- `config.json`
- `screens/main_window.py`
- `screens/settings.py`
- `screens/add_record.py`
- `screens/reports.py`
- `utils/helpers.py`
- `utils/db_backup.py`
- `utils/pdf_export.py`
- `db.py`

## Notes
This release is ready for GitHub release posting. Use `VAWC_APP/RELEASE_CHECKLIST.txt` to verify installation and update behavior.
