"""Read-only MCP adapter for kubectl-ai and other MCP clients."""
import argparse
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from replay import evidence, inventory, snapshot


def make_server(case):
    server = FastMCP("incident-replay")

    @server.tool()
    def list_evidence() -> dict:
        """List the reported symptom and frozen evidence identifiers."""
        return {"symptom": case["symptom"], "records": inventory(case)}

    @server.tool()
    def read_evidence(record_id: str) -> dict:
        """Read one frozen record by its exact evidence identifier."""
        try:
            return evidence(case, record_id)
        except StopIteration:
            raise ValueError("Unknown evidence ID") from None

    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    make_server(snapshot(parser.parse_args().snapshot)).run(transport="stdio")
