# Z's PTO calculator

## End user instructions
1. Go to Tempo > Home > View Leave Balances > Download to Excel
2. Move downloaded file to ./input/tempo-downloads
3. Run `uv run scripts/sync_leave_balances.py`

## One-time setup

You need [uv](https://docs.astral.sh/uv/) and a Coda API token.

1. Generate a token at <https://coda.io/account> (API settings > Generate API token)
2. `cp .env.example .env` and paste the token in

Dependencies are declared inline in the script ([PEP 723](https://peps.python.org/pep-0723/)),
so `uv run` installs them on demand — there is no venv or lockfile to manage.

## scripts/sync_leave_balances.py

Syncs a Tempo export into the Coda doc
[PTO Calculator](https://docs.superhuman.com/d/PTO-Calculator_dOxYiewNUHt).

```
uv run scripts/sync_leave_balances.py                # newest file in input/tempo-downloads
uv run scripts/sync_leave_balances.py path/to.xls    # a specific file
uv run scripts/sync_leave_balances.py --dry-run      # parse and print, no API calls
```

The Tempo export is one row per leave category and 148 columns wide (12 months
x 12 metrics). The script flattens it to one row per category+month — 72 rows
for a 6-category year — and upserts them into the `Leave Balances` table.

Rows are keyed on `Key` (`Employee|Year|Category|Month#`), so re-running is
idempotent: the same month gets updated in place rather than duplicated, and
adding a second employee or a new year just adds rows.

Cells that are blank in the export (e.g. `Waiting Period End`) are left out
rather than written as zero — Tempo emits an explicit `0` for a real zero, so
blank means "not applicable".

`--doc` / `--table` (or `CODA_DOC_ID` / `CODA_TABLE_ID`) override the target if
you ever point this at a different doc.

### If Tempo changes its export format

The script validates the header row and all 144 month/metric columns up front
and fails with a specific message rather than silently writing partial data.
Column names match on both sides, so a rename in Coda surfaces as a Coda API
error naming the column.

## The projection (lives in Coda, not here)

The balance projection and the per-day leave-type allocation are **Coda formula
columns**, not Python. There is nothing to run and no button to click — add a date
to `Projected time off` and every number updates instantly.

Day to day you only need two things in the doc:

- **`Projected time off`** — the only table you edit. One row per day off.
- **`PTO Balances`** → the **`Timesheet values`** view — what to put on the monthly
  timesheet: hours of LY and AL per month.

For how any of it works — table and column IDs, formula bodies, the Coda
constraints that shaped the design, and the checks to run after a change — see
[CLAUDE.md](CLAUDE.md), or open the
[Coda doc](https://docs.superhuman.com/d/PTO-Calculator_dOxYiewNUHt) itself.