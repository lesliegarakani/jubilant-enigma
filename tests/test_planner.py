import json
import tempfile
import unittest
from pathlib import Path

from src.teks_ai_planner import (
    generate_plans,
    load_standards,
    load_student_evidence,
    predict_next_grade_readiness,
)


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.standards = load_standards("data/sample_teks.json")
        self.rows = load_student_evidence("data/sample_students_reading.csv")

    def test_predict_readiness_in_range(self):
        s1_rows = [r for r in self.rows if r.student_id == "S001"]
        readiness = predict_next_grade_readiness(s1_rows)
        self.assertGreaterEqual(readiness, 0.0)
        self.assertLessEqual(readiness, 1.0)

    def test_generate_plans_contains_students(self):
        report = generate_plans(self.standards, self.rows, grade=3, subject="Reading")
        self.assertEqual(report["grade"], 3)
        self.assertEqual(report["subject"], "Reading")
        self.assertEqual(len(report["student_plans"]), 2)

    def test_json_output_shape(self):
        report = generate_plans(self.standards, self.rows, grade=3, subject="Reading")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "plans.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))

        self.assertIn("student_plans", loaded)
        self.assertIn("predicted_next_grade_readiness", loaded["student_plans"][0])


if __name__ == "__main__":
    unittest.main()
