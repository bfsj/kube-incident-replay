import unittest
from replay import ROOT, reference, snapshot


class KindCaptures(unittest.TestCase):
    def test_regressions_from_live_pods(self):
        for pod, label in {"heap": "oom", "health": "liveness", "fetch": "image_pull",
                           "queue": "scheduling"}.items():
            with self.subTest(pod=pod):
                case = snapshot(ROOT / "examples" / "kind-signals" / (pod + ".json"))
                result, _ = reference(case)
                self.assertEqual(result["diagnosis"], label)
                self.assertTrue(result["citations"])
