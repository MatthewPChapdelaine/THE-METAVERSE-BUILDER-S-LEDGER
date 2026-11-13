import argparse
import json
import logging
import math
from pathlib import Path

from .server import serve
from .store import LedgerStore


def _default_database():
    return Path.home() / ".ledger-suite" / "ledger.sqlite3"


def _audit_unity_root(root):
    root = Path(root).expanduser()
    checks = [
        ("Assets/", (root / "Assets").is_dir()),
        ("Packages/manifest.json", (root / "Packages" / "manifest.json").is_file()),
        (
            "ProjectSettings/ProjectVersion.txt",
            (root / "ProjectSettings" / "ProjectVersion.txt").is_file(),
        ),
    ]
    version_path = root / "ProjectSettings" / "ProjectVersion.txt"
    expected_version = "2022.3.22f1"
    version = None
    if version_path.is_file():
        for line in version_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("m_EditorVersion:"):
                version = line.partition(":")[2].strip()
                break
    result = {
        "root": str(root.resolve()),
        "checks": [{"item": name, "ok": ok} for name, ok in checks],
        "editor_version": version,
        "expected_editor_version": expected_version,
        "version_ok": version == expected_version if version else False,
    }
    return result


def _estimate_cloud(weekly_hours, hourly_rate, storage, flat_rate):
    values = (weekly_hours, hourly_rate, storage, flat_rate)
    if not all(math.isfinite(value) and value >= 0 for value in values):
        raise ValueError("all costs and usage values must be non-negative")
    monthly_hours = weekly_hours * 52 / 12
    hourly_total = storage + monthly_hours * hourly_rate
    return {
        "monthly_hours": round(monthly_hours, 2),
        "hourly_compute_monthly": round(monthly_hours * hourly_rate, 2),
        "persistent_storage_monthly": round(storage, 2),
        "hourly_provider_total_monthly": round(hourly_total, 2),
        "flat_rate_monthly": round(flat_rate, 2),
        "lower_cost_option": "hourly" if hourly_total < flat_rate else "flat_rate",
        "difference_monthly": round(abs(hourly_total - flat_rate), 2),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ledger-suite",
        description="Local-first operating tools for virtual-world projects.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    serve_parser = commands.add_parser("serve", help="start the local web application")
    serve_parser.add_argument("--db", type=Path, default=_default_database())
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)

    audit_parser = commands.add_parser("audit-unity", help="check a Unity project root")
    audit_parser.add_argument("path", type=Path)

    estimate_parser = commands.add_parser("estimate-cloud", help="compare hourly and flat-rate compute")
    estimate_parser.add_argument("weekly_hours", type=float)
    estimate_parser.add_argument("--hourly-rate", type=float, required=True)
    estimate_parser.add_argument("--storage", type=float, default=0)
    estimate_parser.add_argument("--flat-rate", type=float, default=60)

    report_parser = commands.add_parser("report", help="print a summary of the local ledger")
    report_parser.add_argument("--db", type=Path, default=_default_database())

    args = parser.parse_args(argv)
    if args.command == "serve":
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
        serve(args.db, args.host, args.port)
        return 0
    if args.command == "audit-unity":
        result = _audit_unity_root(args.path)
        print(json.dumps(result, indent=2))
        return 0 if all(check["ok"] for check in result["checks"]) and result["version_ok"] else 1
    if args.command == "estimate-cloud":
        print(json.dumps(_estimate_cloud(
            args.weekly_hours, args.hourly_rate, args.storage, args.flat_rate
        ), indent=2))
        return 0
    if args.command == "report":
        print(json.dumps(LedgerStore(args.db).summary(), indent=2))
        return 0
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
