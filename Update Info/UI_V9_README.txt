TRI GEAR V9 — UI refresh (first pass)
- Shared Tk/ttk theme in ui/theme.py (Segoe UI, navy/blue/white palette, updated tables and controls).
- Redesigned Login and Admin Dashboard, with Admin sidebar and live database metrics.
- All existing V8 business modules preserved; they inherit shared theme defaults where applicable.
- This is a first UI pass, NOT a completed redesign of every page.
- Do not overwrite your active database or uploads. Back up before migration.
Run on Windows: py -m pip install -r requirements.txt ; py main.py
