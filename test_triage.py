import unittest

from paired import score, variants
from replay import ROOT, snapshot
from triage import supported, triage


class TriageTests(unittest.TestCase):
    def test_reviewed_batch(self):
        report = score(ROOT / "examples/kind-signals", use_model=False)
        self.assertEqual(report["summary"]["source-order"]["paired_success"], 4)

    def test_citation_and_abstention(self):
        complete = snapshot(ROOT / "fixtures/restart-01.json")
        result = triage(complete, lambda _: {"read": "does-not-exist"})
        self.assertEqual(result["citations"], ["E2"])
        self.assertEqual(result["trace"][0]["planner"], "invalid-choice-fallback")
        masked = triage(variants(complete)["masked"])
        self.assertEqual(masked["diagnosis"], "insufficient")
        self.assertIn("termination", masked["next_check"])

    def test_conflict_and_read_budget(self):
        case = snapshot(ROOT / "fixtures/restart-01.json")
        case["records"].append({"id": "E3", "source": "event",
                                "text": "failed liveness probe, will be restarted"})
        self.assertIn("conflicting", triage(case)["next_check"])
        self.assertIn("budget", triage(case, max_reads=1)["next_check"])

    def test_negative_and_wrong_source(self):
        for source, text in [("event", "not OOMKilled"), ("log", "reason=OOMKilled"),
                             ("container.status", "previous reason=OOMKilled was ruled out"),
                             ("event", '{"reason":"Unhealthy","message":"Readiness probe failed"}')]:
            with self.subTest(text=text):
                self.assertFalse(supported({"source": source, "text": text}))
