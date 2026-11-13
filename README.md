# The Metaverse Builder's Ledger

### Software Suite · Operating Procedures & Tutorials

> **Plan clearly. Build deliberately. Keep the ledger close.**
>
> A local-first operations suite for virtual-world projects: browser dashboard,
> Python CLI, SQLite storage, and an optional Unity / UdonSharp spatial-audio
> component.

**Python 3.10+** · **No third-party dependencies** · **SQLite** · **Local-first**

[Quick start](#quick-start) · [Standard operating procedure](#4-standard-operating-procedure) ·
[Dashboard tutorials](#5-dashboard-tutorials) · [CLI tutorials](#6-cli-tutorials) ·
[Unity companion](#7-optional-unity-and-udonsharp-companion) ·
[Troubleshooting](#11-troubleshooting)

<details>
<summary><strong>Contents</strong></summary>

- [Purpose, scope, and principles](#1-purpose-scope-and-operating-principles)
- [Prerequisites and installation](#2-prerequisites-and-installation)
- [First-run setup](#3-first-run-setup)
- [Standard operating procedure](#4-standard-operating-procedure)
- [Dashboard tutorials](#5-dashboard-tutorials)
- [CLI tutorials](#6-cli-tutorials)
- [Unity / UdonSharp companion](#7-optional-unity-and-udonsharp-companion)
- [HTTP API reference](#8-local-http-api-reference)
- [Metric definitions](#9-metric-definitions-and-interpretation)
- [Backup, restore, and data handling](#10-database-backup-restore-and-data-handling)
- [Troubleshooting](#11-troubleshooting)
- [Security and deployment boundaries](#12-security-and-deployment-boundaries)
- [Development and QA](#13-development-and-contribution-checks)

</details>

## Quick start

After installing the command on Linux (steps below), run:

```sh
ledger-suite serve
```

Open <http://127.0.0.1:8000>. Keep the terminal running while you use the
dashboard; press **Ctrl+C** to stop the server. Windows users can use
`py -3 -m ledger_suite serve` from the repository checkout.

> [!IMPORTANT]
> The server is unauthenticated and is intended for trusted localhost use.
> Keep the default loopback binding; do not expose it to a public or shared
> network.

---

## 1. Purpose, scope, and operating principles

Use the Ledger to maintain an operator-entered record of:

- project budgets and compute / infrastructure expenses;
- production milestones, assignments, and release records;
- staff, scheduled and completed shifts, tips, revenue, and fees;
- asset ownership, creator attribution, and license notes;
- spatial-audio near/far zone settings.

The Ledger does **not** connect to VRChat, Discord, Patreon, a payment
processor, cloud-compute vendors, Unity build services, or external identity
systems. It does not publish worlds, pay staff, verify licenses, enforce
moderation, or determine platform trust ranks. Treat every value as a
bookkeeping record entered and verified by an operator.

### Operating principles

1. Keep the server on loopback and the database on a trusted local machine.
2. Record income and expenses from authoritative statements, receipts, and
   provider invoices; do not treat manuscript examples as current prices.
3. Keep financial, staff, and asset-credit entries accurate and attributable.
4. Back up the database before maintenance and verify a restore periodically.
5. Record a release only after completing the applicable external build and
   device checks.

## 2. Prerequisites and installation

### Requirements

- Python 3.10 or later.
- SQLite support in Python (included with standard Python distributions).
- A modern browser.
- No third-party runtime packages, database server, frontend build, API key,
  or network service are required.

### Install on Linux with pipx

The package is OS-independent: any Linux distribution with Python 3.10 or
later, SQLite support, and either `pipx` or Python `venv`/`pip` can install it.
No Debian, RPM, or distribution-specific build is required. Install Python and
`pipx` using your distribution's package manager; package names and commands
vary between distributions.

`pipx` installs the command in an isolated environment and avoids modifying
system-managed Python packages. Once `pipx` is available, use the same steps
on Ubuntu, Fedora, Arch, openSUSE, Debian, or another distribution:

```sh
pipx ensurepath
```

Open a new terminal after following the PATH instructions printed by
`pipx ensurepath`. Change to the checked-out repository and install:

```sh
cd /path/to/THE-METAVERSE-BUILDER-S-LEDGER
pipx install .
ledger-suite --help
ledger-suite serve
```

Open <http://127.0.0.1:8000>. The installed command can be run from any
directory. It uses `~/.ledger-suite/ledger.sqlite3` by default; select a
different database with `ledger-suite serve --db /path/to/ledger.sqlite3`.

To install an updated checkout, run `pipx install --force .` from the repository
root. To remove the application without removing its ledger data, run:

```sh
pipx uninstall metaverse-builders-ledger
```

### Install with a virtual environment

Use this distribution-neutral alternative if `pipx` is unavailable. Python's
`venv` module and `pip` must be installed for your Python interpreter:

```sh
cd /path/to/THE-METAVERSE-BUILDER-S-LEDGER
python3 -m venv ~/.local/share/ledger-suite/venv
~/.local/share/ledger-suite/venv/bin/python -m pip install .
~/.local/share/ledger-suite/venv/bin/ledger-suite serve
```

The app is installed into the isolated virtual environment, not into the
operating system's Python. To update it, run this from the repository root:

```sh
~/.local/share/ledger-suite/venv/bin/python -m pip install --upgrade .
```

To use it from any terminal, add
`~/.local/share/ledger-suite/venv/bin` to your `PATH` or invoke the full path.
Removing the virtual environment does not remove the ledger database.

The application has no third-party runtime dependencies. Installation requires
access to a Python package index the first time, so the build backend can be
installed or retrieved from cache. Check the Python, SQLite, and virtual
environment prerequisites with:

```sh
python3 --version
python3 -c 'import sqlite3, venv; print("SQLite and venv are available")'
```

### Start from the repository

Running directly from source is also supported. Change to the repository
root—the directory containing `ledger_suite/`—and use:

**Linux / macOS**

```sh
python3 --version
python3 -m ledger_suite --help
python3 -m ledger_suite serve
```

**Windows PowerShell**

```powershell
py -3 --version
py -3 -m ledger_suite --help
py -3 -m ledger_suite serve
```

Open <http://127.0.0.1:8000>. Keep the terminal open while using the app.
Press **Ctrl+C** in that terminal to stop it cleanly.

By default, the database is stored at `~/.ledger-suite/ledger.sqlite3` (the
current user's home directory). The server creates the directory and database
on first start. Supply `--db` to choose another path:

```sh
python3 -m ledger_suite serve --db ./data/ledger.sqlite3
```

The relative database path is resolved from the current working directory.
Keep the database outside a public web root and include it in your normal
protected backup routine.

### Optional isolated Python environment

The app has no third-party Python dependencies. A virtual environment is
optional:

```sh
python3 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\Activate.ps1
python -m ledger_suite serve
```

If PowerShell prevents environment activation, either use the permitted
activation policy for your machine or invoke `.venv\Scripts\python.exe`
directly. Do not install packages just to run this project.

## 3. First-run setup

1. Start the server and open the local address.
2. Go to **Projects & costs** and create one project for each distinct world,
   venue, or product that needs its own budget and work records.
3. Choose a clear, stable project name. Set the platform and monthly budget.
   The default platform is VRChat; the budget is an operator-entered amount.
4. Record recurring services and one-time purchases in **Expense ledger**.
   Use one consistent currency (the interface displays USD).
5. Go to **Production** and create tasks with the six work tracks:
   spatial architecture, 3D environment art, shaders & UI, UdonSharp systems,
   lighting & performance, and release & group ops.
6. Add contributors under **Team & revenue**, then use their roster entries
   when recording shifts.
7. Record revenue and fees from statements, and register third-party or
   contributor-created assets with a clear license/source note.
8. Add release records and audio zones as needed.
9. Run **World tools** CLI checks outside the browser when working with actual
   Unity project files.
10. Create and verify a database backup before relying on the Ledger for
    operational records.

There are no demo records. Empty dashboards on a new database are expected.

> **Recommended setup order:** Project → Expenses → Tasks → Contributors →
> Shifts & revenue → Asset credits → Releases → Audio zones.

## 4. Standard operating procedure

### Daily or per work session

1. Start the app using the same database path used previously.
2. Review **Overview** for open work, recurring spend, and project budget
   utilization.
3. Add or update production tasks. Use `todo`, `in_progress`, `blocked`, and
   `done` consistently; record the actual contributor and due date where known.
4. Register assets as they enter the project. Capture creator and license
   details at intake rather than trying to reconstruct them at release time.
5. Record planned shifts before an event when useful. After the event, record
   actual hours, tips, and mark the shift `completed`.
6. Add revenue only after checking the source statement. Enter gross income
   and transaction/platform fees separately.
7. Stop the server with Ctrl+C when finished, especially on a shared or
   portable workstation.

### Weekly review

1. Review blocked and overdue tasks with their assignees.
2. Reconcile planned shifts against completed shifts; correct operational
   records before reporting results.
3. Check all uncredited assets and resolve attribution before publishing or
   distributing a build.
4. Review expenses against invoices and identify missing recurring services.
5. Confirm the next PC and Quest / Android release gates with actual target
   builds and devices.
6. Make a database backup and confirm that the backup file exists and is
   readable.

### Month-end close

1. Choose a reporting cutoff and reconcile the Ledger against bank,
   subscription, payment, and provider statements.
2. Record each income source as gross revenue and each associated fee in the
   fee field. Do not enter net income as gross and then subtract the fee again.
3. Confirm shift hours, hourly rates, and tips against approved event records.
4. Review the four illustrative allocation weights shown in the app:
   infrastructure reserve 20%, core engineering 30%, environment art 25%,
   and live operations 25%. They total 100%, but are only a reference model;
   use your signed agreements and actual approved policy for payments.
5. Compare expense run rate with the current project budget. Explain any
   overrun or out-of-period entry in your accounting records.
6. Export or copy the month-end summary into the organization's approved
   reporting system. The app itself currently has no CSV/PDF export or
   accounting integration.
7. Back up the database and retain it according to your organization's
   financial and privacy retention rules.

> **Month-end reminder:** The displayed revenue is net of recorded fees, not
> profit. Reconcile against source statements and your accounting system.

### Release / publish procedure

1. Create a production task for each required PC, Quest, and cross-platform
   validation step.
2. Audit the Unity project root with the CLI (see Tutorial 8).
3. Validate SDK/package versions, compile and build in Unity, and test the
   target build on the relevant platform. The Ledger does not perform those
   build or device tests.
4. Check asset credits and license terms, Udon references, performance,
   audio-zone distances, and the project's own moderation and access policies.
5. Create or update a release record with version, target, status, and notes.
   Mark it `published` only after the external publishing process succeeds.
6. Preserve build logs and approval evidence in your project's normal release
   storage; the release record is not a build artifact or proof of upload.

## 5. Dashboard tutorials

### Tutorial 1 — Create a project and establish its budget

1. Select **Projects & costs**.
2. Under **New project**, enter a project name, platform, monthly budget, and
   status.
3. Select **Create project**.
4. Confirm it appears under **Active projects** and on the Overview.
5. Enter related expenses separately. A project budget is a target, not a
   transaction or a hard spending limit.

### Tutorial 2 — Record compute and other expenses

1. In **Record an expense**, select the project.
2. Enter the vendor, category, amount, billing cycle, date, and optional notes.
3. Choose `monthly`, `annual`, or `one_time`. Enter the whole invoice amount
   for annual costs; the summary divides annual amounts by 12.
4. Select **Add expense** and verify it appears in the expense ledger.
5. Use one-time for purchases that should not count toward the recurring
   monthly run rate.

The run-rate summary includes all recorded monthly charges plus one-twelfth
of annual charges. One-time expenses are excluded. Expense dates do not filter
this run-rate total. Confirm current provider prices and billing terms before
using an estimate for a purchasing decision.

### Tutorial 3 — Plan and update production tasks

1. In **Production**, select a project and enter a task title.
2. Choose the most relevant production track, add an assignee, due date, and
   concise acceptance criteria in the description.
3. Create the task, then use its status selector in the work table to move it
   through `todo`, `in_progress`, `blocked`, and `done`.
4. Put the blocker and next action in the task description or your external
   team notes. The task status alone is not a dependency-management workflow.

### Tutorial 4 — Add contributors, shifts, and tips

1. In **Team & revenue**, add each contributor with a display name, role,
   hourly rate, and active state.
2. Add a shift with project, contributor, date, hours, tips, and status.
3. Leave an upcoming shift `planned`; after confirming attendance and actual
   time, update or re-enter the correct details as `completed`.
4. Review completed-shift cost in the summary.

Staff costs in the month-to-date summary are calculated from completed shifts
dated from the first of the current month through today:
`hours × roster hourly rate + tips`. Planned shifts are excluded. Inactive
contributors remain in historical records, but only active contributors are
offered in the shift-entry selector.

### Tutorial 5 — Record revenue and understand allocations

1. Add a revenue entry for each source and project.
2. Enter gross receipts, fees, and the statement date. Use notes to reference a
   statement or payout batch without entering sensitive account credentials.
3. Confirm the displayed net for the entry is `gross - fees`.
4. Review the month-to-date net revenue on Overview and the reference
   allocation weights under Team & revenue.

Month-to-date net revenue includes entries dated in the current calendar month
through today. It is not profit: the summary does not subtract staff costs,
expenses, taxes, refunds, or other liabilities. Allocation percentages are
informational only; the app does not calculate individual payouts.

### Tutorial 6 — Keep asset credits and release history

1. Open **Assets & releases** and register the asset name, creator, production
   track, and license/source.
2. Set **Credited** to **No** only when credit is genuinely unresolved; follow
   up before distribution.
3. Create a release record with the version, target, status, and verification
   notes. Use PC VR, Quest / Android, or Cross-platform.
4. Keep evidence of license permissions and publishing approvals in your
   project's controlled document store, not merely in a short ledger note.

### Tutorial 7 — Configure spatial-audio reference zones

1. Open **World tools** and add a zone with a project and unique name.
2. Enter a positive near distance and a far distance greater than the near
   distance, in meters.
3. Add attenuation or placement notes. Save and review the zone in the table.
4. Apply the values in Unity with the optional component in Tutorial 10.
5. Test in-world on the intended platforms; a stored zone is documentation,
   not an acoustic simulation or a substitute for listening tests.

## 6. CLI tutorials

Run CLI commands from the repository root. Add `python` instead of `python3`
on Windows where appropriate.

### Tutorial 8 — Audit a Unity project root

```sh
python3 -m ledger_suite audit-unity "/path/to/UnityProject"
```

The read-only audit checks for:

- `Assets/`;
- `Packages/manifest.json`;
- `ProjectSettings/ProjectVersion.txt`;
- the editor version string `2022.3.22f1` in `ProjectVersion.txt`.

It prints JSON. Exit status 0 means these checks pass; exit status 1 means at
least one is missing or the editor version differs. This is a narrow structure
check: it does not parse the package manifest, validate packages, detect every
possible nested-root mistake, open Unity, compile scripts, or confirm that a
project builds.

### Tutorial 9 — Compare hourly GPU and flat-rate compute

```sh
python3 -m ledger_suite estimate-cloud 15 \
  --hourly-rate 0.50 \
  --storage 14 \
  --flat-rate 60
```

The example assumes 15 active hours per week, an hourly compute rate of $0.50,
$14/month storage, and a $60/month flat rate. The CLI uses 52 weeks per year:

`monthly hours = weekly hours × 52 / 12`

`hourly monthly total = monthly hours × hourly rate + monthly storage`

It prints the components, the lower modeled-cost option, and the monthly
difference. At a tie it reports `flat_rate`. It does not include taxes,
egress, setup time, minimum usage, service limits, currency conversion, or
provider-specific pricing details. Check a current provider quote before
committing funds.

### Tutorial 10 — Read a summary from the CLI

```sh
python3 -m ledger_suite report
```

This opens (and initializes, if needed) the default database and prints the
same summary data used by the dashboard. To use a non-default database, pass
its path:

```sh
python3 -m ledger_suite report --db ./data/ledger.sqlite3
```

Use the same `--db` path for the server and report command or they will show
different ledgers.

### Tutorial 11 — Run the automated QA suite

```sh
python3 -m unittest discover -s tests -v
node --check ledger_suite/web/app.js
git diff --check
```

The tests use temporary databases and a loopback HTTP server. They do not
require an external VRChat SDK, Unity installation, cloud account, or live
payment credentials.

## 7. Optional Unity and UdonSharp companion

The component is at
[`Unity/Assets/LedgerSuite/Runtime/ResonanceAudioZone.cs`](Unity/Assets/LedgerSuite/Runtime/ResonanceAudioZone.cs);
setup notes are in
[`Unity/Assets/LedgerSuite/README.md`](Unity/Assets/LedgerSuite/README.md).

### Tutorial 12 — Add an audio zone component to an existing Unity project

1. Confirm the consuming project uses a compatible Unity version and has the
   VRChat SDK and UdonSharp installed.
2. Copy the `Unity/Assets/LedgerSuite/Runtime/ResonanceAudioZone.cs` file into
   the consuming project's `Assets/` directory. Do not copy it over existing
   project files.
3. Let Unity compile. Resolve any version or namespace conflicts using the
   consuming project's package setup; SDK packages are not bundled here.
4. Add the UdonSharp behaviour to the GameObject that owns the 3D `AudioSource`.
5. Assign that `AudioSource` to **Target Audio Source** in the Inspector.
6. Set **Near Distance** and **Far Distance** from the corresponding Ledger
   audio-zone record. The far distance must exceed the near distance.
7. Confirm the AudioSource is configured for 3D spatial audio, test in the
   Unity scene and in a representative VRChat build, and tune by listening.

At `Start`, the component checks the reference and distance values, then sets
`AudioSource.minDistance` and `AudioSource.maxDistance`. It does not set a
VRChat spatial-audio component, attenuation curve, occlusion, low-pass filter,
network state, player tracking, moderation, or access control. Invalid
configuration produces a Unity warning and leaves the AudioSource unchanged.

## 8. Local HTTP API reference

The browser uses a small JSON API on the same origin. It is intended for local
development and trusted localhost use, not as a remotely hosted service.
Request bodies must be valid JSON and are limited to 1,000,000 bytes.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/summary` | Summary metrics and project budget utilization |
| `GET` | `/api/projects`, `/api/expenses`, `/api/tasks`, `/api/staff`, `/api/shifts`, `/api/revenue`, `/api/assets`, `/api/releases`, `/api/audio_zones` | List a resource |
| `POST` | `/api/projects`, `/api/expenses`, `/api/tasks`, `/api/staff`, `/api/shifts`, `/api/revenue`, `/api/assets`, `/api/releases`, `/api/audio_zones` | Create a record |
| `PATCH` | `/api/tasks/{id}` | Update a task's status, assignee, or due date |

Example:

```sh
curl -sS http://127.0.0.1:8000/api/summary

curl -sS -X POST http://127.0.0.1:8000/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"name":"Orbspace Citadel","platform":"VRChat","monthly_budget":180}'
```

Amounts are supplied as decimal currency values with no more than two decimal
places. Dates use `YYYY-MM-DD`. Resource IDs are generated by the server.

> **API boundary:** There is no authentication, user/role model,
pagination, filtering, CSV import/export, update endpoint for most resources,
or delete endpoint. The browser only updates task fields through the task
status selector. Validate entries before submission and make backups. Do not
expose this API to the internet or an untrusted LAN.

## 9. Metric definitions and interpretation

| Metric | Definition |
| --- | --- |
| Active projects | Projects whose status is not `archived` |
| Open work items | Tasks in `todo`, `in_progress`, or `blocked` |
| Monthly recurring cost | All monthly expenses plus one-twelfth of annual expenses; excludes one-time expenses |
| Project monthly cost | Same recurring-cost normalization grouped by each non-archived project |
| Month-to-date net revenue | Gross less fees for revenue entries dated from this month's first day through today |
| Month-to-date staff cost | Completed shift hours × current roster hourly rate, plus tips, within this month through today |
| Uncredited assets | Asset entries with `credited` set to false |

Expense dates are recorded but do not constrain the recurring-cost totals.
Archived projects are excluded from the per-project budget list; the top-level
recurring expense metric includes every expense entry. The dashboard compares
recurring expense costs against the project budget; it does not include staff
costs in that progress bar. These figures are operational summaries, not
accounting statements, tax calculations, or a full profit-and-loss report.

## 10. Database backup, restore, and data handling

The database contains project names, staff details, task assignments, income,
expenses, tips, and asset-credit records. Restrict access to the operating
system account and backups. Do not enter passwords, payment-card information,
private access tokens, or unnecessary personal data in notes.

### Backup with Python's SQLite backup API

This method is suitable while the app is running and produces a consistent
SQLite backup. Substitute the actual database path if using `--db`.

```sh
python3 -c "from pathlib import Path; import sqlite3; src=sqlite3.connect(Path.home()/'.ledger-suite/ledger.sqlite3'); dst=sqlite3.connect(Path.home()/'ledger-backup.sqlite3'); src.backup(dst); dst.close(); src.close()"
```

On Windows PowerShell, use:

```powershell
py -3 -c "import sqlite3; src=sqlite3.connect(r'$env:USERPROFILE\.ledger-suite\ledger.sqlite3'); dst=sqlite3.connect(r'$env:USERPROFILE\ledger-backup.sqlite3'); src.backup(dst); dst.close(); src.close()"
```

Choose a protected backup location with adequate access controls. Verify the
backup can be opened:

```sh
python3 -c "import sqlite3; c=sqlite3.connect('/path/to/ledger-backup.sqlite3'); print(c.execute('PRAGMA integrity_check').fetchone()[0]); c.close()"
```

The expected result is `ok`. A backup is not verified until this check passes.
Keep separate, versioned backups according to your retention policy.

### Restore a backup

1. Stop the Ledger server with Ctrl+C.
2. Make a separate copy of the current database in case rollback is needed.
3. Copy the verified backup to the exact database path used by `serve`.
4. Start the app with that path and inspect projects, expenses, and a CLI
   summary before resuming normal operation.
5. Keep the pre-restore copy until the restored data is confirmed.

Never replace or delete a database while the server is writing to it.

## 11. Troubleshooting

| Symptom | Checks / action |
| --- | --- |
| `No module named ledger_suite` | Run the command from the repository root; verify the `ledger_suite/` directory is present. |
| Address/port is already in use | Start on another port, for example `python3 -m ledger_suite serve --port 8080`, then open `http://127.0.0.1:8080`. |
| Dashboard loads but data does not | Check the server terminal for errors; verify browser and server use the same host/port and that the selected database is writable. |
| Data appears to be missing | Check whether the app was started with a different `--db` path or under a different operating-system account. |
| A form rejects an entry | Check required fields, non-negative amounts with at most two decimals, valid enum values, date format, and that selected projects/contributors exist. |
| Cloud estimate differs from a quote | Confirm compute hours, hourly rate, storage, billing period, taxes, egress, and service limits; the CLI only computes the documented formula. |
| Unity audit exits with status 1 | Review each JSON check. The audited path must be the project root and include the expected folders/files and editor version. |
| UdonSharp component does not apply distances | Confirm it compiled, is attached to an enabled behaviour, has an assigned 3D AudioSource, and uses `farDistance > nearDistance`; inspect Unity warnings. |
| Need to correct or remove a saved record | The current UI has no general edit/delete workflow. Stop before making more dependent records; back up the DB and follow a controlled, tested database-maintenance process rather than editing a live database. |

## 12. Security and deployment boundaries

> [!WARNING]
> This is a local bookkeeping tool, not a secured multi-user service. Do not
> expose its unauthenticated server or API to a network.

- The server binds to `127.0.0.1` by default. Keep this default.
- There is no authentication or authorization. Do not set `--host 0.0.0.0`,
  put the app behind a public tunnel, or expose it to a shared network.
- The SQLite database is unencrypted by this application. Use operating-system
  file permissions and encrypted storage/backups where appropriate.
- The API provides no CSRF/authentication model because it is designed for
  localhost operation. Do not treat it as safe for untrusted users.
- Protect backups like the source database, and avoid sensitive personal data
  in free-text fields.
- The Unity companion is a convenience for local audio attenuation settings;
  client-side Udon code is not trusted server-side security.

If multi-user collaboration, remote hosting, authentication, payment
processing, platform APIs, or production CI/CD is required, design and review
those features as a separate deployment with appropriate security controls.

## 13. Development and contribution checks

Before submitting changes, run:

```sh
python3 -m unittest discover -s tests -v
node --check ledger_suite/web/app.js
git diff --check
```

The server and UI use Python and browser built-ins; tests use temporary
databases and local loopback networking. Keep test data isolated from the
default user database. Unity companion compilation requires a separate Unity
project with the relevant SDK/UdonSharp packages installed.

The accompanying manuscript is the source reference for the suite's operating
domains and example assumptions. Verify provider prices, platform
requirements, SDK versions, and all financial decisions against current
primary sources before relying on them.
