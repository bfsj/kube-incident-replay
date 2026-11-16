"""Measure a fixed-age cohort, including inconclusive captures in the denominator."""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from capture import collect
from paired import variants, EXPECTED
from triage import triage

def kubectl(*args, payload=None):
    return subprocess.run(["kubectl","--context","kind-replay","-n","incident-lab",*args],
                          input=payload,text=True,capture_output=True,check=True).stdout

template = json.loads(kubectl("create","--dry-run=client","-f","lab/incidents.yaml","-o","json"))
pods = []
truth = {}
for rep in range(7):
    for example in template["items"]:
        pod=json.loads(json.dumps(example))
        name=pod["metadata"]["name"]
        key=f"{name}-{rep}"
        truth[key]=EXPECTED[name]
        pod["metadata"]["name"]=key
        containers=pod["spec"]["containers"]
        if name=="heap":
            containers[0]["resources"]["limits"]["memory"]=f"{32+rep*4}Mi"
        elif name=="queue":
            containers[0]["resources"]["requests"]["cpu"]=str(1000+rep*20)
        elif name=="health":
            containers[0]["livenessProbe"]["periodSeconds"]=2+rep%3
        elif name=="fetch":
            containers[0]["image"]=f"registry.invalid/incident-demo/missing:v{rep}"
        pods.append(pod)
kubectl("create","-f","-",payload=json.dumps({"apiVersion":"v1","kind":"List","items":pods}))
time.sleep(90)
inventory=json.loads(kubectl("get","pods","-o","json"))["items"]
uids={p["metadata"]["name"]:p["metadata"]["uid"] for p in inventory}
assert set(uids)==set(truth) and len(set(uids.values()))==28
rows=[]
for key,expected in truth.items():
    case=collect("kind-replay","incident-lab",key)
    full,masked=(triage(v,max_reads=len(case["records"])) for v in variants(case).values())
    rows.append(dict(pod=key,uid=uids[key],expected=expected,full=full["diagnosis"],
                     masked=masked["diagnosis"],citations=full["citations"],
                     full_reads=len(full["trace"]),masked_reads=len(masked["trace"])))
Path("cohort.json").write_text(json.dumps(rows))
print("FINAL_AGENT="+json.dumps(rows))
