"""Score complete/masked pairs from one independently generated kind batch."""
import argparse
import json
import statistics
from pathlib import Path

from replay import diagnose, model_reply, reference, snapshot
from triage import triage

EXPECTED = {"heap": "oom", "health": "liveness", "fetch": "image_pull", "queue": "scheduling"}


def variants(case):
    # Preserve availability and record IDs. Keep the Pod phase on the masked side.
    masked = [{**r, "text": r["text"] if r["source"] == "pod.phase" else "[unavailable]"}
              for r in case["records"]]
    return {"full": case, "masked": {**case, "records": masked}}


def score(directory, use_model):
    rows = []
    engines = ["model-v1", "model-with-gate", "source-order"] if use_model else ["source-order"]
    for name, expected in EXPECTED.items():
        original = snapshot(directory / (name + ".json"))
        oracle, _ = reference(original)
        if oracle["diagnosis"] != expected:
            raise ValueError(f"Capture {name} lacks independent evidence for the injected fault")
        for variant, case in variants(original).items():
            for engine in engines:
                calls = 0
                revealed = set()

                def reply(messages):
                    nonlocal calls
                    calls += 1
                    # The legacy driver sends successfully read records on the next model turn.
                    for msg in messages:
                        if msg["role"] == "user":
                            value = json.loads(msg["content"])
                            if isinstance(value, dict) and {"id", "source", "text"} <= value.keys():
                                revealed.add(value["id"])
                    return model_reply(messages)

                try:
                    if engine == "model-v1":
                        result, reads = diagnose(case, reply)
                    else:
                        result = triage(case, reply if engine == "model-with-gate" else None,
                                        max_reads=len(case["records"]))
                        reads = len(result["trace"])
                    supported_hit = (result["diagnosis"] == expected and
                                     bool(set(result["citations"]) & set(oracle["citations"])))
                    correct = supported_hit if variant == "full" else result["diagnosis"] == "insufficient"
                    row = {**result, "correct": correct}
                except (ValueError, KeyError, IndexError, TypeError) as exc:
                    reads = len(revealed)
                    row = {"error": str(exc), "correct": False}
                rows.append(dict(case=name, variant=variant, engine=engine, reads=reads,
                                 model_calls=calls, **row))
    summary = {}
    for engine in engines:
        group = [r for r in rows if r["engine"] == engine]
        masked = [r for r in group if r["variant"] == "masked"]
        summary[engine] = {
            "pairs": len(EXPECTED),
            "paired_success": sum(all(r["correct"] for r in group if r["case"] == name)
                                  for name in EXPECTED),
            "full_supported": sum(r["correct"] for r in group if r["variant"] == "full"),
            "masked_abstained": sum(r["correct"] for r in masked),
            "masked_unsupported": sum(r.get("diagnosis") not in (None, "insufficient") for r in masked),
            "invalid_trials": sum("error" in r for r in group),
            "mean_reads": statistics.mean(r["reads"] for r in group),
            "mean_model_calls": statistics.mean(r["model_calls"] for r in group),
        }
    return {"summary": summary, "trials": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", action="store_true")
    args = parser.parse_args()
    print(json.dumps(score(args.directory, args.model), indent=2))
