from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cfo_panel.settings import get_editable_env_values, save_editable_env_values


class SettingsTests(unittest.TestCase):
    def test_save_and_load_editable_env_values_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            env_path = temp_path / ".env"
            example_path = temp_path / ".env.example"
            example_path.write_text(
                "CFO_PANEL_BIGQUERY_PROJECT=demo-project\n"
                "CFO_PANEL_BIGQUERY_LOCATION=US\n"
                "CFO_PANEL_PREFER_MARTS=true\n",
                encoding="utf-8",
            )

            save_editable_env_values(
                {
                    "CFO_PANEL_BIGQUERY_PROJECT": "real-project",
                    "CFO_PANEL_MART_DATASET": "finance_mart",
                    "GOOGLE_APPLICATION_CREDENTIALS": "/tmp/service account.json",
                    "CFO_PANEL_PREFER_MARTS": False,
                },
                env_path=env_path,
                example_path=example_path,
            )

            values = get_editable_env_values(env_path=env_path, example_path=example_path)
            written = env_path.read_text(encoding="utf-8")

            self.assertEqual(values["CFO_PANEL_BIGQUERY_PROJECT"], "real-project")
            self.assertEqual(values["CFO_PANEL_MART_DATASET"], "finance_mart")
            self.assertEqual(
                values["GOOGLE_APPLICATION_CREDENTIALS"],
                "/tmp/service account.json",
            )
            self.assertEqual(values["CFO_PANEL_PREFER_MARTS"], "false")
            self.assertIn('GOOGLE_APPLICATION_CREDENTIALS="/tmp/service account.json"', written)


if __name__ == "__main__":
    unittest.main()
