"""Wait for decisive Kubernetes evidence, then preserve one capture per fault."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from capture import collect
from replay import reference

cases = {"heap": "oom", "health": "liveness", "fetch": "image_pull", "queue": "scheduling"}
out = Path("captures")
out.mkdir(exist_ok=True)
deadline = time.monotonic() + 300
while cases and time.monotonic() < deadline:
    for pod, expected in list(cases.items()):
        case = collect("kind-replay", "incident-lab", pod)
        (out / (pod + ".json")).write_text(json.dumps(case, indent=2))
        result, _ = reference(case)
        if result["diagnosis"] == expected:
            print(pod, result, flush=True)
            del cases[pod]
    if cases:
        time.sleep(2)
if cases:
    raise SystemExit(f"Missing expected signals for {cases}")
