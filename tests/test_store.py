import tempfile
import unittest
from datetime import date
from pathlib import Path

from ledger_suite.store import LedgerStore, NotFoundError, ValidationError


class LedgerStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = LedgerStore(Path(self.temp_dir.name) / "ledger.sqlite3")
        self.project = self.store.create("projects", {"name": "Test world", "monthly_budget": "180"})

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_annual_cost_contributes_rounded_monthly_run_rate(self):
        self.store.create("expenses", {
            "project_id": self.project["id"],
            "vendor": "GPU host",
            "category": "compute",
            "amount": "100",
            "billing_cycle": "annual",
        })

        summary = self.store.summary()

        self.assertEqual(summary["monthly_recurring_cost"], 8.33)
        self.assertEqual(summary["projects_by_budget"][0]["monthly_cost"], 8.33)

    def test_task_status_update_only_allows_operational_fields(self):
        task = self.store.create("tasks", {
            "project_id": self.project["id"],
            "title": "Build Quest version",
            "track": "Release & group ops",
        })

        updated = self.store.update_task(task["id"], {"status": "in_progress"})

        self.assertEqual(updated["status"], "in_progress")
        with self.assertRaises(ValidationError):
            self.store.update_task(task["id"], {"project_id": "other-project"})
        with self.assertRaises(NotFoundError):
            self.store.update_task("missing", {"status": "done"})

    def test_staff_shift_revenue_and_attribution_are_summarized(self):
        staff = self.store.create("staff", {
            "display_name": "Ari",
            "role": "Moderator",
            "rate_per_hour": "20",
            "active": "false",
        })
        self.assertFalse(staff["active"])
        self.store.create("shifts", {
            "project_id": self.project["id"],
            "staff_id": staff["id"],
            "date": date.today().isoformat(),
            "hours": "2.5",
            "tips": "5.25",
            "status": "completed",
        })
        self.store.create("revenue", {
            "project_id": self.project["id"],
            "source": "Membership",
            "gross": "100",
            "fees": "3.25",
            "date": date.today().isoformat(),
        })
        self.store.create("assets", {
            "project_id": self.project["id"],
            "name": "Lobby model",
            "creator": "Sam",
            "track": "Environment art",
            "license": "CC BY 4.0",
            "credited": False,
        })

        summary = self.store.summary()

        self.assertEqual(summary["month_to_date_net_revenue"], 96.75)
        self.assertEqual(summary["month_to_date_staff_cost"], 55.25)
        self.assertEqual(summary["uncredited_assets"], 1)

    def test_future_dated_revenue_is_not_counted_as_month_to_date(self):
        tomorrow = date.fromordinal(date.today().toordinal() + 1).isoformat()
        self.store.create("revenue", {
            "project_id": self.project["id"],
            "source": "Scheduled payout",
            "gross": "50",
            "date": tomorrow,
        })

        self.assertEqual(self.store.summary()["month_to_date_net_revenue"], 0)

    def test_rejects_invalid_money_and_far_audio_boundary(self):
        with self.assertRaises(ValidationError):
            self.store.create("expenses", {
                "project_id": self.project["id"],
                "vendor": "Invalid",
                "category": "compute",
                "amount": "1.001",
                "billing_cycle": "monthly",
            })
        with self.assertRaises(ValidationError):
            self.store.create("expenses", {
                "project_id": self.project["id"],
                "vendor": "Invalid",
                "category": "compute",
                "amount": "0." + "9" * 1000,
                "billing_cycle": "monthly",
            })
        with self.assertRaises(ValidationError):
            self.store.create("audio_zones", {
                "project_id": self.project["id"],
                "name": "Invalid zone",
                "near_distance": 5,
                "far_distance": 5,
            })


if __name__ == "__main__":
    unittest.main()
