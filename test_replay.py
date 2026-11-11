import unittest
from replay import ROOT, diagnose, evaluate, snapshot


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.case = snapshot(ROOT / "fixtures/restart-01.json")

    def test_ablation(self):
        rows = evaluate("reference")
        correct = [r["scope"] for r in rows if r["correct"]]
        self.assertEqual(correct.count("first-record"), 2)
        self.assertEqual(correct.count("all-records"), 6)

    def test_model_loop(self):
        replies = iter([{"read": "E2"}, {"diagnosis": "oom", "citations": ["E2"]}])
        result, reads = diagnose(self.case, lambda _: next(replies))
        self.assertEqual((result["diagnosis"], reads), ("oom", 1))

    def test_unread_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            diagnose(self.case, lambda _: {"diagnosis": "oom", "citations": ["E2"]})

    def test_baseline_cannot_read_hidden_record(self):
        with self.assertRaises(ValueError):
            diagnose(self.case, lambda _: {"read": "E2"}, first_only=True)

    def test_repeated_read_is_bounded(self):
        with self.assertRaises(ValueError):
            diagnose(self.case, lambda _: {"read": "E1"})
