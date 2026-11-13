import sqlite3
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4


class ValidationError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


_PROJECT_FIELDS = {
    "name": "text",
    "platform": "text",
    "monthly_budget": "money",
    "status": "project_status",
}
_RESOURCE_FIELDS = {
    "projects": _PROJECT_FIELDS,
    "expenses": {
        "project_id": "project_id",
        "vendor": "text",
        "category": "text",
        "amount": "money",
        "billing_cycle": "billing_cycle",
        "date": "date",
        "notes": "optional_text",
    },
    "tasks": {
        "project_id": "project_id",
        "title": "text",
        "track": "text",
        "assignee": "optional_text",
        "status": "task_status",
        "due_date": "optional_date",
        "description": "optional_text",
    },
    "staff": {
        "display_name": "text",
        "role": "text",
        "rate_per_hour": "money",
        "active": "boolean",
    },
    "shifts": {
        "project_id": "project_id",
        "staff_id": "staff_id",
        "date": "date",
        "hours": "hours",
        "tips": "money",
        "status": "shift_status",
    },
    "revenue": {
        "project_id": "project_id",
        "source": "text",
        "gross": "money",
        "fees": "money",
        "date": "date",
        "notes": "optional_text",
    },
    "assets": {
        "project_id": "project_id",
        "name": "text",
        "creator": "text",
        "track": "text",
        "license": "text",
        "credited": "boolean",
    },
    "releases": {
        "project_id": "project_id",
        "version": "text",
        "target": "text",
        "status": "release_status",
        "notes": "optional_text",
    },
    "audio_zones": {
        "project_id": "project_id",
        "name": "text",
        "near_distance": "positive_number",
        "far_distance": "positive_number",
        "strategy": "optional_text",
    },
}

_ENUMS = {
    "project_status": {"planning", "active", "paused", "archived"},
    "billing_cycle": {"monthly", "annual", "one_time"},
    "task_status": {"todo", "in_progress", "done", "blocked"},
    "shift_status": {"planned", "completed"},
    "release_status": {"planned", "building", "ready", "published", "blocked"},
}

_SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'VRChat',
    monthly_budget_cents INTEGER NOT NULL DEFAULT 0 CHECK (monthly_budget_cents >= 0),
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS expenses (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    vendor TEXT NOT NULL,
    category TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    billing_cycle TEXT NOT NULL,
    date TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    track TEXT NOT NULL,
    assignee TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'todo',
    due_date TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS staff (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL,
    rate_per_hour_cents INTEGER NOT NULL DEFAULT 0 CHECK (rate_per_hour_cents >= 0),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS shifts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    staff_id TEXT NOT NULL REFERENCES staff(id) ON DELETE RESTRICT,
    date TEXT NOT NULL,
    hours REAL NOT NULL CHECK (hours > 0),
    tips_cents INTEGER NOT NULL DEFAULT 0 CHECK (tips_cents >= 0),
    status TEXT NOT NULL DEFAULT 'planned',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS revenue (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    gross_cents INTEGER NOT NULL CHECK (gross_cents >= 0),
    fees_cents INTEGER NOT NULL DEFAULT 0 CHECK (fees_cents >= 0),
    date TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    creator TEXT NOT NULL,
    track TEXT NOT NULL,
    license TEXT NOT NULL,
    credited INTEGER NOT NULL DEFAULT 1 CHECK (credited IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS releases (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    target TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audio_zones (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    near_distance REAL NOT NULL CHECK (near_distance > 0),
    far_distance REAL NOT NULL CHECK (far_distance > near_distance),
    strategy TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_expenses_project_date ON expenses(project_id, date);
CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX IF NOT EXISTS idx_revenue_project_date ON revenue(project_id, date);
"""


def _money_to_cents(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError("amount must be a valid non-negative monetary value") from None
    if not amount.is_finite() or amount < 0:
        raise ValidationError("amount must be a valid non-negative monetary value")
    if amount > Decimal("1000000000"):
        raise ValidationError("amount must not exceed 1,000,000,000")
    try:
        rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValidationError("amount must be a valid non-negative monetary value") from None
    if rounded != amount:
        raise ValidationError("amount may have at most two decimal places")
    return int(rounded * 100)


def _required_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} is required")
    if len(value.strip()) > 500:
        raise ValidationError(f"{field} must be 500 characters or fewer")
    return value.strip()


def _convert(value, kind, field):
    if kind == "text":
        return _required_text(value, field)
    if kind == "optional_text":
        if value is None:
            return ""
        if not isinstance(value, str) or len(value) > 4000:
            raise ValidationError(f"{field} must be text of 4000 characters or fewer")
        return value.strip()
    if kind == "money":
        return _money_to_cents(value)
    if kind == "boolean":
        if isinstance(value, bool):
            return int(value)
        if value == "true":
            return 1
        if value == "false":
            return 0
        if value in (0, 1):
            return int(value)
        raise ValidationError(f"{field} must be true or false")
    if kind in _ENUMS:
        if not isinstance(value, str) or value not in _ENUMS[kind]:
            raise ValidationError(f"{field} must be one of: {', '.join(sorted(_ENUMS[kind]))}")
        return value
    if kind in ("date", "optional_date"):
        if kind == "optional_date" and (value is None or value == ""):
            return ""
        try:
            return date.fromisoformat(value).isoformat()
        except (TypeError, ValueError):
            raise ValidationError(f"{field} must be a date in YYYY-MM-DD format") from None
    if kind == "hours":
        try:
            hours = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValidationError("hours must be greater than zero") from None
        if not hours.is_finite() or hours <= 0 or hours > 24:
            raise ValidationError("hours must be greater than zero and at most 24")
        converted = float(hours)
        if converted <= 0:
            raise ValidationError("hours must be greater than zero and at most 24")
        return converted
    if kind == "positive_number":
        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValidationError(f"{field} must be greater than zero") from None
        if not number.is_finite() or number <= 0 or number > 10000:
            raise ValidationError(f"{field} must be greater than zero and at most 10000")
        converted = float(number)
        if converted <= 0:
            raise ValidationError(f"{field} must be greater than zero and at most 10000")
        return converted
    raise AssertionError(f"Unknown field type: {kind}")


class LedgerStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(_SCHEMA)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _format(resource, row):
        item = dict(row)
        for field in ("monthly_budget", "amount", "rate_per_hour", "tips", "gross", "fees"):
            cents_field = {
                "monthly_budget": "monthly_budget_cents",
                "amount": "amount_cents",
                "rate_per_hour": "rate_per_hour_cents",
                "tips": "tips_cents",
                "gross": "gross_cents",
                "fees": "fees_cents",
            }[field]
            if cents_field in item:
                item[field] = item.pop(cents_field) / 100
        for field in ("active", "credited"):
            if field in item:
                item[field] = bool(item[field])
        return item

    def list(self, resource):
        if resource not in _RESOURCE_FIELDS:
            raise ValidationError("unknown resource")
        ordering = "created_at DESC"
        with self.connect() as connection:
            rows = connection.execute(f"SELECT * FROM {resource} ORDER BY {ordering}").fetchall()
        return [self._format(resource, row) for row in rows]

    def create(self, resource, payload):
        fields = _RESOURCE_FIELDS.get(resource)
        if fields is None:
            raise ValidationError("unknown resource")
        if not isinstance(payload, dict):
            raise ValidationError("request body must be a JSON object")
        unknown = set(payload) - set(fields)
        if unknown:
            raise ValidationError(f"unknown field(s): {', '.join(sorted(unknown))}")
        required = {
            "projects": {"name"},
            "expenses": {"project_id", "vendor", "category", "amount", "billing_cycle"},
            "tasks": {"project_id", "title", "track"},
            "staff": {"display_name", "role"},
            "shifts": {"project_id", "staff_id", "date", "hours"},
            "revenue": {"project_id", "source", "gross", "date"},
            "assets": {"project_id", "name", "creator", "track", "license"},
            "releases": {"project_id", "version", "target"},
            "audio_zones": {"project_id", "name", "near_distance", "far_distance"},
        }[resource]
        missing = required - payload.keys()
        if missing:
            raise ValidationError(f"missing required field(s): {', '.join(sorted(missing))}")

        values = {}
        for field, value in payload.items():
            kind = fields[field]
            if kind in ("project_id", "staff_id"):
                values[field] = _required_text(value, field)
            else:
                values[field] = _convert(value, kind, field)

        if resource == "projects":
            values.setdefault("platform", "VRChat")
            values.setdefault("monthly_budget", 0)
            values.setdefault("status", "active")
        elif resource == "expenses":
            values.setdefault("date", date.today().isoformat())
            values.setdefault("notes", "")
        elif resource == "tasks":
            values.setdefault("assignee", "")
            values.setdefault("status", "todo")
            values.setdefault("due_date", "")
            values.setdefault("description", "")
        elif resource == "staff":
            values.setdefault("rate_per_hour", 0)
            values.setdefault("active", 1)
        elif resource == "shifts":
            values.setdefault("tips", 0)
            values.setdefault("status", "planned")
        elif resource == "revenue":
            values.setdefault("fees", 0)
            values.setdefault("notes", "")
        elif resource == "assets":
            values.setdefault("credited", 1)
        elif resource == "releases":
            values.setdefault("status", "planned")
            values.setdefault("notes", "")
        elif resource == "audio_zones":
            values.setdefault("strategy", "")

        if resource == "audio_zones" and values["far_distance"] <= values["near_distance"]:
            raise ValidationError("far_distance must be greater than near_distance")

        column_map = {
            "monthly_budget": "monthly_budget_cents",
            "amount": "amount_cents",
            "rate_per_hour": "rate_per_hour_cents",
            "tips": "tips_cents",
            "gross": "gross_cents",
            "fees": "fees_cents",
        }
        columns = [column_map.get(field, field) for field in values]
        stored_values = [values[field] for field in values]
        identifier = str(uuid4())
        with self.connect() as connection:
            connection.execute(
                f"INSERT INTO {resource} (id, {', '.join(columns)}) "
                f"VALUES (?, {', '.join('?' for _ in columns)})",
                [identifier, *stored_values],
            )
            row = connection.execute(
                f"SELECT * FROM {resource} WHERE id = ?", (identifier,)
            ).fetchone()
        return self._format(resource, row)

    def update_task(self, identifier, payload):
        fields = {"status": "task_status", "assignee": "optional_text", "due_date": "optional_date"}
        if not isinstance(payload, dict) or not payload:
            raise ValidationError("request body must contain task fields to update")
        unknown = set(payload) - set(fields)
        if unknown:
            raise ValidationError(f"tasks cannot update field(s): {', '.join(sorted(unknown))}")
        values = {key: _convert(value, fields[key], key) for key, value in payload.items()}
        with self.connect() as connection:
            cursor = connection.execute(
                f"UPDATE tasks SET {', '.join(f'{key} = ?' for key in values)} WHERE id = ?",
                [*values.values(), identifier],
            )
            if cursor.rowcount == 0:
                raise NotFoundError("task not found")
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (identifier,)).fetchone()
        return self._format("tasks", row)

    def summary(self):
        today = date.today()
        month_start = today.replace(day=1).isoformat()
        with self.connect() as connection:
            project_count = connection.execute(
                "SELECT COUNT(*) FROM projects WHERE status != 'archived'"
            ).fetchone()[0]
            open_tasks = connection.execute(
                "SELECT COUNT(*) FROM tasks WHERE status IN ('todo', 'in_progress', 'blocked')"
            ).fetchone()[0]
            monthly_expenses = connection.execute(
                """SELECT COALESCE(SUM(
                    CASE billing_cycle
                      WHEN 'monthly' THEN amount_cents
                      WHEN 'annual' THEN ROUND(amount_cents / 12.0)
                      ELSE 0
                    END
                ), 0) FROM expenses"""
            ).fetchone()[0]
            monthly_revenue = connection.execute(
                """SELECT COALESCE(SUM(gross_cents - fees_cents), 0) FROM revenue
                   WHERE date >= ? AND date <= ?""",
                (month_start, today.isoformat()),
            ).fetchone()[0]
            shift_cost = connection.execute(
                """SELECT COALESCE(SUM(s.hours * st.rate_per_hour_cents + s.tips_cents), 0)
                   FROM shifts s JOIN staff st ON st.id = s.staff_id
                   WHERE s.status = 'completed' AND s.date >= ? AND s.date <= ?""",
                (month_start, today.isoformat()),
            ).fetchone()[0]
            uncredited_assets = connection.execute(
                "SELECT COUNT(*) FROM assets WHERE credited = 0"
            ).fetchone()[0]
            by_project = connection.execute(
                """SELECT p.id, p.name, p.monthly_budget_cents,
                   COALESCE(SUM(CASE
                     WHEN e.billing_cycle = 'monthly' THEN e.amount_cents
                     WHEN e.billing_cycle = 'annual' THEN ROUND(e.amount_cents / 12.0)
                     ELSE 0 END), 0) AS monthly_cost_cents
                   FROM projects p LEFT JOIN expenses e ON e.project_id = p.id
                   WHERE p.status != 'archived'
                   GROUP BY p.id ORDER BY p.name COLLATE NOCASE"""
            ).fetchall()
        return {
            "projects": project_count,
            "open_tasks": open_tasks,
            "monthly_recurring_cost": monthly_expenses / 100,
            "month_to_date_net_revenue": monthly_revenue / 100,
            "month_to_date_staff_cost": shift_cost / 100,
            "uncredited_assets": uncredited_assets,
            "revenue_allocation_percent": {
                "infrastructure_reserve": 20,
                "core_engineering": 30,
                "environment_art": 25,
                "live_operations": 25,
            },
            "projects_by_budget": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "monthly_budget": row["monthly_budget_cents"] / 100,
                    "monthly_cost": row["monthly_cost_cents"] / 100,
                }
                for row in by_project
            ],
        }
