
DBF Record Cleaner v2.0 — Enterprise Build Guide (Windows)
=========================================================

Runtime target: **Python 3.7 (32-bit)** — compatible with Windows 7/8/10/11 and legacy POS.

Prerequisites
-------------
1) Install Python 3.7 x86 and make sure the `py` launcher can see it as `-V:3.7-32`.
2) Install PyInstaller for Python 3.7-32.

Quick Build
-----------
1) Open an elevated **x86** Developer Command Prompt or regular cmd.
2) `cd dbf_cleaner_v2`
3) Run: `build.bat`

Outputs
-------
- `dist/dbfcleaner_gui.exe` — GUI edition
- `dist/dbfcleaner_cli.exe` — CLI edition

Notes
-----
- If building on a path with spaces, PyInstaller handles it, but avoid very long paths on older systems.
- If you cannot use pip online, vendor the `dbf` and `PyYAML` wheels locally and install from file.
