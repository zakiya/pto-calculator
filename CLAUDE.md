Keep README.md up to date — but keep it **user-facing**. Coda internals (IDs,
formulas, constraints) belong in this file, not the README.

**Never write identifying details into any file in this repo** — no personal name,
no email address, no machine/host name, no home-directory paths. Say "the user".
**Never infer gender; use they/them.** This applies to code, comments, commit
messages, and docs. Employee names arrive at runtime from the Tempo export and
live only in the Coda doc and the gitignored `input/` directory — never in source.

# Coda reference

Everything Claude needs to work on the PTO Calculator Coda doc without
re-deriving it. Read this before touching the doc.

**Doc:** `coda://docs/OxYiewNUHt` — "PTO Calculator"
<https://docs.superhuman.com/d/PTO-Calculator_dOxYiewNUHt>
Single employee.

Use the Superhuman Docs MCP tools (deferred — load via `ToolSearch` first). They
reach Coda docs despite the name.

## Architecture in one paragraph

`scripts/sync_leave_balances.py` writes Tempo's export into `Leave balances`.
Everything else is **Coda formula columns** — no Python, no button, no
automation. `Projection Months` projects balances forward month by month;
`Projected time off` computes the per-day LY/AL split. Both recalculate live.

## Pages

| Page | pageId | canvas | Holds |
|---|---|---|---|
| `Tempo records` (hidden) | `section-Sk8ipVCkKz` | `canvas-M2LP01maXQ` | `Leave balances` + "do not edit" callout |
| *(title blank)* | `section-0PgKM55LS1` | `canvas-0PgKM55LS1` | `Projected time off` (pageType `table`) |
| `PTO Balances` | `section-I6Q9Skge0B` | `canvas-I6Q9Skge0B` | `Projection Months` + 6 canvas formulas |

Hidden pages still compute. An orphaned table `grid-5vfGwrUBvv` sits on a deleted
page; its *name field* holds the user's pasted 2025–26 timesheet history — the best
record of how leave is actually charged, worth rescuing someday.

## Tables

### `Leave balances` — `grid-qTEhXKpw1j` (72 rows, all stored, script-written)

`Key` c-KlvtH-erTu · `Employee` c-Ly_ZPQevLz · `Year` c--UTddEub3w ·
`Month #` c--2YIWzMpu- · `Month` c-lbQKScTkO9 · `Category` c-TAbYSES-j4 ·
`Last Updated` c-W7dFAf1RtW · `Begin` c-OyeftvrBVC · `Used` c-C-l-mTq4uz ·
`Accrued` c-kL4ZAyF_bN · `Misc` c-m0iaXlgonS · `FLSA CTO` c-s8RrNTD-kx ·
`CTO` c-KDCE8BJcv0 · `End` c-j1bicpqF-Y · `Waiting Period End` c-RKhWaqsIF- ·
`SSMOS` c-oYk1AE_c7R · `Proj. Accrual` c-UIVwC9zx-k · `Proj. End` c-Lcw6vGWmSF ·
`Proj. SSM` c-deQ5PCjnn3 · `Synced At` c-M0_mkw9BZR

Categories: AL (annual), LY, PT, PH, HI, FL. **`SSMOS > 0` is the discriminator
between months Tempo has actually posted and months it merely projects.** Posted
months carry Begin/Used/Accrued/End; unposted ones zero those and fill `Proj.*`.
Tempo's `Proj.*` assumes **zero** time off — that is exactly what this tool fixes.

### `Projected time off` — `grid-uTmawCuem9` (the only table the user edits)

Stored: `Date to use` c-dUC9TXi91M (date) · `Reason` c-LOxFYbVmai (display) ·
`Notes` c-SwtohKpWwn (**canvas — cannot hold a formula**) · `Hours override` c-HraVd0TYnq

Formula: `Hours` c-5_4FjR5EGL · `Month Key` c-r6mg7bcg0t · `Hours Before` c-W0eeBbYTHT ·
`Weekend?` c-Hh5ssXjxkY · `Duplicate?` c-49vZuzn8xG · `In Horizon` c-IJbPP277Z4 ·
`K` c-rcQCkDVv0q · `LY Accrued` c-RSxI_qDPFh · `Min Prefix` c-ZE3Wp_zatE ·
`LY Used Before` c-dQe-bpd9IS · `LY Hours` c-3uDmTG-pf0 · `AL Hours` c-NzKFm94Jpm ·
`Status` c-oppIC7DICn

Views: `Table` (default; sort date asc; hides the 7 intermediates) ·
`Calendar` `v-ZNmMoWFdue`.

### `Projection Months` — `grid-VjZcZQ_ZHj` (36 static rows, Jan 2026 – Dec 2028)

Stored: `Year` c-R7hdF0fW5W · `Month #` c-oLlE_ZFMzc · `Month` c-rkNKwcSfZF

Formula: `Sort Key` c-IkOkK-r3Ea · `Label` c-L7TC9FpzJh (display) ·
`Prev Sort Key` c-GFRWUCUkVw · `Is Actual` c-sj09867zKV · `K` c-hP7wTOFTkg ·
`Days Off` c-bbZgYWtaq5 · `Planned Hours` c-DxTRIh14Y7 · `Hours Needed` c-fsOnHLRttd ·
`Hours Cum` c-yDYjaI4Aqm · `LY End` c-S1yHspDM6U · `LY Used Cum` c-vxbCVVy9iq ·
`AL End` c-YE0bGXe-K5 · `LY Avail` c-iZa9YrnbKS · `LY Used` c-wQcpgtstVq ·
`AL Avail` c-VU3uYleZJ0 · `AL Used` c-13pqm4ug1Y · `PT End` c-8OMJe0uriR ·
`PH End` c-QVL89gw-vJ · `HI End` c-O-vqIFNDPi · `FL End` c-hhUMYEtQk_ ·
`Over-planned` c-q4Mlg-HFPE · `Reconcile` c-0GrbcdBvri

Views, both filtered `Is Actual or K <= 12`, sorted by `Sort Key` asc:
- `Table` (default) — hides 10 intermediates. **No conditional formatting**;
  `Over-planned` is a checkbox column, deliberately not a red row.
- `Timesheet values` `v-d6G_oi9VKY` — shows only `Label`, `LY Used`, `AL Used`,
  `Hours Needed`, `Is Actual`. This is what the user reads when filing a timesheet.

**The filter hides 18 of 36 rows: July 2027 – December 2028.** It is display-only —
hidden months still compute and are still subtracted. But a day booked past the
window vanishes from both views silently. Widen the filter when planning that far out.

## Canvas formulas (on `canvas-I6Q9Skge0B`)

Define once, reference by name from both tables. Never inline these lookups.

```
LastActualSK  f-POhAN4-6Rz  = WithName([Leave balances].Filter(SSMOS > 0), a,
                                If(a.Count() = 0, 0,
                                   a.ForEach(CurrentValue.Year * 100 + CurrentValue.[Month #]).Max()))
SeedIndex     f-KEAoCHiLV1  = RoundDown(LastActualSK / 100) * 12
                              + (LastActualSK - RoundDown(LastActualSK / 100) * 100)
ALSeed        f-J2y8mStcsU  = WithName([Leave balances].Filter(Category.ToText() = "AL"
                                and Year * 100 + [Month #] = LastActualSK), a,
                                If(a.Count() = 0, 0, a.First().End))
LYSeed        f--P8IHDnnPe  = (same, "LY")
TargetEmployee f-g_zjG9trGN = [Leave balances].First().Employee
ReportedAsOf  f-pLv5RI6OKC  = [Leave balances].First().[Last Updated]
```

## Business rules

- 8 hours per day off. `Hours override` handles partial days; blank means 8.
- Accrue **+15 AL and +5 LY** every month.
- **Spend LY before AL.** PT / PH / HI / FL are reserves — carried flat, never
  auto-allocated. The user overrides by hand if they want to spend one.
- Year rollover: everything carries, no cap, no reset, no expiry.
- Timesheets lag ~2 months (July usage appears after ~Aug 23). So for any month
  Tempo hasn't posted, `Projected time off` is the *only* record of that usage.
  Days in already-posted months must **not** be subtracted again.

## The math

Monthly balance is a Lindley recursion `LY End(k) = Max(0, LY End(k-1) + 5 − Hours(k))`.
It **cannot** be written recursively in Coda (see Constraints), so `LY End` uses the
unrolled closed form — a max over suffix sums:

```
LY End(k) = Max( 0,
                 LYSeed + 5k − HC(k),
                 max over j<k of [ 5(k−j) − (HC(k) − HC(j)) ] )
LY Used Cum(k) = LYSeed + 5k − LY End(k)
AL End(k)      = ALSeed + 15k − (HC(k) − LY Used Cum(k))
```
where `HC` = `Hours Cum` and `K` = months since the seed month.

The per-day split in `Projected time off` needs the same answer but **may not read
`Projection Months`** (see Constraints), so it uses the **dual** — a min over prefixes:

```
LY used before row t = Hours Before(t) + Min( LYSeed, min over rows r<t of [A(r) − H(r)] )
   where A = LY Accrued = LYSeed + 5K,  H = Hours Before + Hours
LY Hours(t) = Max(0, Min(Hours(t), A(t) − LY used before t))
AL Hours(t) = Hours(t) − LY Hours(t)
```

`Hours Before` is cumulative **across all months** in the horizon, not per-month —
LY carries over, so a per-month reset silently under-counts. Ties on identical
dates break by `RowId`; without that, duplicate dates collide on the same ordinal
and the per-date view disagrees with the monthly rollup.

## Coda constraints — all found the hard way

**1. No column cycles.** `AL Begin = previous row's AL End` is a cycle among
`{AL Begin, AL Avail, AL End}`. Coda rejects it **silently** — it blanks the column
*and every column it consumed*, with no error surfaced. Hence the closed form.
The usual `RunActions(ForEach(Sequence(...), ModifyRows(...)))` button workaround
does **not** help: Coda evaluates all arguments against a pre-batch snapshot, so
one click advances the chain by one month.

**2. Cross-table dependencies are tracked per *table*, not per column.**
`Projection Months` aggregates `Projected time off`, therefore `Projected time off`
can never read *anything* from `Projection Months` — doing so blanks the whole
table. Hence the dual formulation above.

**3. `thisRow` is shadowed inside `ForEach` / `Filter`.** Bind what you need with
`WithName` *before* entering the loop, or the column silently evaluates to blank.
This is the single most common way to break these formulas.

**4. Naming.** Square brackets in a table name make it unreferenceable from a
formula (`[[Input] Projected time off]` won't parse). Renaming a table's **default
view** renames the base table; renaming the **page** does not (`Tempo records` still
holds a table called `Leave balances`). Existing formulas survive renames — Coda
binds by ID — but anything you later type by name breaks.

**5. `Max()` / `Min()` on an empty list is a hard error**, not 0. Guard with
`Count() = 0`. (`Sum()` on empty correctly returns 0.)

**6. `.ToText()` takes no format tokens.** `.ToText("yyyy-MM-dd")` errors. Build
date strings from `Month()` / `Year()`.

**7. `table_create` may coerce `num` columns into select lists.** Check the response
and fix with `table_columns_manage` `update`.

**8. `formula_execute` can return stale values immediately after a write.** Re-run
before concluding something is broken.

## Verification probes

Run these after any change. Copy-paste into `formula_execute` on `coda://docs/OxYiewNUHt`.

**Health / seeds:**
```
Concatenate("ptoRows=", [Projected time off].Count(), " months=", [Projection Months].Count(),
  " lastActual=", LastActualSK, " alSeed=", ALSeed, " lySeed=", LYSeed,
  " overPlanned=", [Projection Months].Filter([Over-planned]).Count())
```

**Invariant 1 — per-date totals must equal the monthly rollup** (two independent
derivations; disagreement means drift):
```
[Projection Months].Filter(K > 0 and K <= 12).ForEach(WithName(CurrentValue.[Sort Key], sk,
  Concatenate(CurrentValue.Label, " monthly=", CurrentValue.[LY Used], "/", CurrentValue.[AL Used],
    " perDate=", [Projected time off].Filter([Month Key] = sk).[LY Hours].Sum(), "/",
    [Projected time off].Filter([Month Key] = sk).[AL Hours].Sum())))
```

**Invariant 2 — the gap from Tempo's naive projection equals planned hours:**
```
Concatenate("gap=",
  ([Leave balances].Filter(Category.ToText()="AL" and Year=2026 and [Month #]=12).First().[Proj. End]
   + [Leave balances].Filter(Category.ToText()="LY" and Year=2026 and [Month #]=12).First().[Proj. End])
  - ([Projection Months].Filter([Sort Key]=202612).First().[AL End]
     + [Projection Months].Filter([Sort Key]=202612).First().[LY End]),
  " planned=", [Projected time off].Filter([Month Key] > 202606 and [Month Key] <= 202612).Hours.Sum())
```

**Invariant 3 — 2026 actuals reproduce** (historical, never changes): Jan 2026 =
5 LY + 19 AL, Feb 2026 = 5 LY + 3 AL. Both are mid-day splits and both back-test
the LY-before-AL rule.

**Invariant 4 — `Reconcile` is blank or "OK posted" on every row.** A MISMATCH
means Tempo closed a month before the timesheet posted, so planned days stopped
being subtracted for a month that was never charged.

Invariants 1–4 hold regardless of what is planned, so they don't go stale when
the user books a trip. Prefer them over any hard-coded numbers.

## Current state (2026-07-25)

Last posted month June 2026 (`LastActualSK` 202606); seeds AL 202, LY 0.
28 planned days / 224h: 4 Jul 2026, 4 Aug 2026 ("Home"), 20 May 31 – Jun 25 2027
("World Cup 2027"). Nothing over-planned (min AL End 166). Latest planned day is
**K=12, the last month the view filter shows**.

Snapshot — goes stale as soon as travel is booked; use the invariants instead:

| Month | LY Avail | LY Used | LY End | AL Avail | AL Used | AL End |
|---|---|---|---|---|---|---|
| Jul 2026 | 5 | 5 | 0 | 217 | 27 | 190 |
| Aug 2026 | 5 | 5 | 0 | 205 | 27 | 178 |
| Dec 2026 | 20 | 0 | 20 | 238 | 0 | 238 |
| Jun 2027 | 42 | 42 | 0 | 328 | 110 | 218 |

## Known limits

- `Projection Months` has static rows only through **Dec 2028**. Add rows before 2029;
  dates past the horizon get `Status` = "Outside projection horizon".
- Single employee. Lookups filter on `TargetEmployee`, which is just the first
  employee in `Leave balances`.
- Year rollover assumes no cap / reset / expiry — unverified against actual policy.
- `Notes` is the user's; calculated status lives in `Status` because canvas columns
  can't hold formulas.
