"""Score unmodified kubectl-ai with the same full snapshots and Ollama model."""
import json
import os
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
labels = json.loads((root / "fixtures/labels.json").read_text())
choices = "oom, liveness, image_pull, scheduling, insufficient"
rows = []
for case_id, (expected, _) in labels.items():
    case = (root / "fixtures" / (case_id + ".json")).read_text()
    prompt = ("Classify this frozen pod incident using only the supplied evidence. "
              f"Allowed labels: {choices}. If evidence is inconclusive choose insufficient. "
              "Return one line: FINAL=<label>.\n" + case)
    cmd = ["docker", "run", "--rm", "--read-only", "--tmpfs", "/tmp:rw,mode=1777",
           "--cap-drop=ALL", "--security-opt=no-new-privileges", "--user", "65534:65534",
           "--network", "container:replay-model", "-e", "HOME=/tmp",
           "-v", f"{root / 'upstream/kubectl-ai'}:/usr/local/bin/kubectl-ai:ro",
           "debian:bookworm-slim", "kubectl-ai", "--quiet", "--llm-provider=ollama",
           "--model", os.environ["MODEL_NAME"], "--max-iterations=4", prompt]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
    match = re.findall(r"(?im)^\s*FINAL\s*=\s*(oom|liveness|image_pull|scheduling|insufficient)\s*[.]?\s*$",
                       run.stdout.replace("**", ""))
    label = match[-1].lower() if match else None
    rows.append({"case": case_id, "label": label, "correct": label == expected,
                 "exit_code": run.returncode, "output": (run.stdout + run.stderr)[-2500:]})
print(json.dumps(rows, indent=2))
if all(row["exit_code"] != 0 for row in rows):
    raise SystemExit("kubectl-ai failed to run")
