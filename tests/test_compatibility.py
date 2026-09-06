import io
import tempfile
import unittest
from contextlib import chdir, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from ruamel.yaml import YAML

from make_shifttable import Scheduling
from read_data import data_preprocessor


class DependencyCompatibilityTests(unittest.TestCase):
    def test_sample_yaml_files_are_valid(self):
        root = Path(__file__).resolve().parents[1]
        for filename in ["model.yaml", "sheet_structure.yaml", "schedule.yaml"]:
            with self.subTest(filename=filename):
                self.assertIsInstance(YAML().load(root / filename), dict)

    def test_preprocessing_keeps_latest_response_and_sets_attributes(self):
        data = pd.DataFrame(
            [
                ["test@example.com", "test", ""],
                ["alice@example.com", "Alice (old)", "old comment"],
                ["bob@other.com", "Bob", ""],
                ["alice@example.com", "Alice", "latest comment"],
            ],
            columns=["メールアドレス", "名前", "コメント"],
        )
        with tempfile.TemporaryDirectory() as directory, chdir(directory):
            result = data_preprocessor(
                data, {"shiftername": "B", "comment": "C"}, "example.com"
            )
            self.assertEqual(result["名前"].tolist(), ["Bob", "Alice"])
            self.assertEqual(result["attribute"].tolist(), [0, 1])
            self.assertEqual(
                Path("comments.txt").read_text(), "name: Alice\nlatest comment\n\n"
            )

    def test_ng_slots_solver_and_spreadsheet_serialization(self):
        model = {
            "continuous_shift": True,
            "maxshiftnumber_perday": 1,
            "maxshiftnumber": 1,
            "atleastnumber": 0,
            "limitsameworknum": 1,
            "need": [],
            "avoid": [],
            "avoidtime": [],
            "limitnumber": [],
        }
        sheets = {
            "Input": {"sheets": [{"shiftername": "B", "timeslots": ["C"]}]},
            "Output": {
                "name": "Test",
                "sheets": [{"name": "Shifts"}, {"name": "People"}],
            },
        }
        schedule = {
            "timeslots": ["morning"],
            "shiftworks": ["reception"],
            "schedule": [
                {
                    "date": "Monday",
                    "site": "Hall",
                    "contents": [{"time": "morning", "work": ["reception"]}],
                }
            ],
        }
        with (
            tempfile.TemporaryDirectory() as directory,
            chdir(directory),
            patch.object(Scheduling, "_Scheduling__list_pa", []),
            patch.object(Scheduling, "_Scheduling__list_dts", []),
            patch("make_shifttable.gspread.service_account") as service_account,
        ):
            yaml = YAML()
            for filename, value in [
                ("model.yaml", model),
                ("sheet_structure.yaml", sheets),
                ("schedule.yaml", schedule),
            ]:
                yaml.dump(value, Path(filename))
            Path("json").mkdir()
            Path("json/test.json").write_text("{}")
            pd.DataFrame(
                [
                    ["alice@example.com", "Alice", "Monday", 0],
                    ["bob@example.com", "Bob", None, 1],
                ],
                columns=["メールアドレス", "名前", "morning", "attribute"],
            ).to_csv("data.csv", index=False)

            scheduling = Scheduling()
            self.assertEqual(
                scheduling.GetNGList(), [("Alice", 0, "Monday", "morning", "reception")]
            )
            output = io.StringIO()
            with redirect_stdout(output):
                scheduling.SolveProblem()
            self.assertIn(
                "optimality = Optimal, target value = 1.0", output.getvalue()
            )
            scheduling.SetResult()
            self.assertEqual(scheduling._Scheduling__table1_array[2][2], "Bob")
            people = {row[0]: row[1] for row in scheduling._Scheduling__table2_array[2:]}
            self.assertEqual(people, {"Alice": "x", "Bob": "reception"})

            # Exercise gspread-dataframe against the updated pandas without network access.
            spreadsheet = service_account.return_value.open.return_value
            worksheet = spreadsheet.worksheet.return_value
            worksheet.row_count = 100
            worksheet.col_count = 26
            scheduling.SendOutputSpreadSheet()
            self.assertEqual(worksheet.update_cells.call_count, 2)
            values = [cell.value for cell in worksheet.update_cells.call_args.args[0]]
            self.assertIn("reception", values)
            self.assertIn("x", values)


if __name__ == "__main__":
    unittest.main()
