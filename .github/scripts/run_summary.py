from pathlib import Path
import json
import os

report = json.loads(Path("paired-report.json").read_text())["summary"]
with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf8") as out:
    print("### Paired incident evaluation", file=out)
    print("| Engine | Passed pairs | Unsupported diagnoses on masked cases | Invalid trials | Mean reads | Mean model calls |", file=out)
    print("|---|---:|---:|---:|---:|---:|", file=out)
    for name, row in report.items():
        print(f"| {name} | {row['paired_success']}/{row['pairs']} | {row['masked_unsupported']} "
              f"| {row['invalid_trials']} | {row['mean_reads']:.2f} | {row['mean_model_calls']:.2f} |", file=out)

for name in ("source-order", "model-with-gate"):
    row = report[name]
    if row["pairs"] == 0 or row["paired_success"] != row["pairs"] or row["invalid_trials"]:
        raise SystemExit(f"{name}: inspect failed pairs in paired-report.json")
