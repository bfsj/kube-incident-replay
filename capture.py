"""Capture one named pod and its UID-scoped events; omit logs, env and secrets."""
import argparse
import json
import subprocess
from pathlib import Path


def collect(context, namespace, pod):
    def get(*args):
        out = subprocess.check_output(["kubectl", "--context", context, "-n", namespace,
                                       "get", *args, "-o", "json"], text=True, timeout=20)
        return json.loads(out)
    obj = get("pod", pod)
    status = obj.get("status", {})
    uid = obj["metadata"]["uid"]
    events = get("events", "--field-selector", "involvedObject.uid=" + uid)
    records = []

    def add(source, value):
        records.append({"id": f"E{len(records) + 1}", "source": source,
                        "text": json.dumps(value, ensure_ascii=False)})

    add("pod.phase", status.get("phase"))
    for item in status.get("containerStatuses", []):
        add("container.status", {k: item.get(k) for k in ("name", "state", "lastState", "restartCount")})
    for event in sorted(events.get("items", []), key=lambda e: e["metadata"]["creationTimestamp"]):
        add("event", {"reason": event.get("reason"), "message": event.get("message")})
    return {"symptom": "Investigate pod health", "records": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("context", "namespace", "pod"):
        parser.add_argument("--" + flag, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = collect(args.context, args.namespace, args.pod)
    with args.out.open("x", encoding="utf8") as stream:
        json.dump(data, stream, indent=2)
