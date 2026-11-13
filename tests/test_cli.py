import tempfile
import unittest
from pathlib import Path

from ledger_suite.__main__ import _audit_unity_root, _estimate_cloud


class CliTests(unittest.TestCase):
    def test_cloud_estimate_includes_storage_in_hourly_total(self):
        estimate = _estimate_cloud(15, 0.5, 14, 60)

        self.assertEqual(estimate["monthly_hours"], 65.0)
        self.assertEqual(estimate["hourly_provider_total_monthly"], 46.5)
        self.assertEqual(estimate["lower_cost_option"], "hourly")

    def test_cloud_estimate_rejects_non_finite_inputs(self):
        with self.assertRaises(ValueError):
            _estimate_cloud(float("nan"), 0.5, 14, 60)

    def test_unity_root_audit_checks_layout_and_editor_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Assets").mkdir()
            (root / "Packages").mkdir()
            (root / "Packages" / "manifest.json").write_text("{}", encoding="utf-8")
            (root / "ProjectSettings").mkdir()
            (root / "ProjectSettings" / "ProjectVersion.txt").write_text(
                "m_EditorVersion: 2022.3.22f1\n", encoding="utf-8"
            )

            result = _audit_unity_root(root)

        self.assertTrue(all(check["ok"] for check in result["checks"]))
        self.assertTrue(result["version_ok"])


if __name__ == "__main__":
    unittest.main()
