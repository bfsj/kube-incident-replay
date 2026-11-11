# Kube Incident Replay

Give a diagnostic agent the same frozen incident twice. First expose only a symptom, then let it fetch events and termination records by ID. Compare its root cause, citations and willingness to stop when evidence is missing.

[Local model benchmark](https://github.com/bfsj/kube-incident-replay/actions/workflows/model.yml) · [MCP transport tests](https://github.com/bfsj/kube-incident-replay/actions/workflows/replay.yml)

## Run the example

```sh
python replay.py
python -m unittest -v
```

Python 3.10+ is sufficient for the deterministic reference. Six labeled synthetic snapshots cover OOM, liveness restart, image pull, scheduling and two underdetermined restarts. The readiness-only event is a deliberate distractor. The reference policy gets **2/6** correct with just the first record and **6/6** with all records. This checks the fixture wiring. Use the model workflow for actual model scores.

## Run an LLM

Start an Ollama server and pull a model, or use an OpenAI-compatible chat endpoint that supports JSON mode. On a POSIX shell:

```sh
ollama pull qwen2.5:1.5b
MODEL_NAME=qwen2.5:1.5b python replay.py --engine model
```

For other endpoints set MODEL_BASE_URL and optionally MODEL_API_KEY. Each trial has a bounded read/finish loop. The model sees only the symptom, a list of available record IDs and the records it requests. The evaluation labels stay outside the conversation. Invalid tool requests and unread citations fail a trial. Each row reports correctness, evidence reads and whether it cited an annotated decisive record. Citation membership alone cannot prove semantic entailment. The two scopes use the same model and prompt.

## Replay in kubectl-ai

Install the adapter in a virtual environment with `python -m pip install -r requirements.txt`. Add the following entry to the servers list in your kubectl-ai MCP configuration, replacing all three paths with absolute paths. Start `kubectl-ai --mcp-client` and ask: “Use list_evidence and read_evidence to diagnose the snapshot. Cite record IDs.”

```yaml
servers:
  - name: incident-replay
    command: /absolute/path/to/.venv/bin/python
    args: [/absolute/path/to/server.py, /absolute/path/to/fixtures/restart-01.json]
```

The adapter exposes exactly two read-only tools for a single frozen snapshot. kubectl-ai also supplies its own built-in tools; use the standalone replay driver above for controlled benchmark comparisons. [Upstream kubectl-ai documentation](https://github.com/GoogleCloudPlatform/kubectl-ai#mcp-client-mode)

## Capture another incident

```sh
python capture.py --context kind-demo --namespace demo --pod checkout --out checkout.json
```

Capture reads pod status and Kubernetes Events filtered by pod UID. Event messages and termination state can contain internal details. Review a snapshot before sharing. Point the adapter at the saved file to replay it after the cluster has gone away.

## Maintaining the corpus

Give each case stable record IDs. Store the expected label and decisive evidence IDs in fixtures/labels.json. Include an ambiguous or misleading case when adding a new diagnosis. Run the same model and both evidence scopes, then inspect every changed prediction. Synthetic fixtures provide regression coverage; estimating real incident accuracy requires separately labeled field captures.
