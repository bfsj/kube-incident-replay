import sys
import unittest

from replay import ROOT

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    ClientSession = None


@unittest.skipIf(ClientSession is None, "Install requirements.txt for MCP transport")
class TransportTest(unittest.IsolatedAsyncioTestCase):
    async def test_real_stdio_roundtrip(self):
        spec = StdioServerParameters(command=sys.executable, args=[
            str(ROOT / "server.py"), str(ROOT / "fixtures/restart-01.json")])
        async with stdio_client(spec) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                listing = await session.call_tool("list_evidence", {})
                self.assertIn("E2", listing.content[0].text)
                record = await session.call_tool("read_evidence", {"record_id": "E2"})
                self.assertIn("OOMKilled", record.content[0].text)
                diagnosis = await session.call_tool("triage_snapshot", {})
                self.assertFalse(diagnosis.isError)
                self.assertIn("oom", diagnosis.content[0].text)
                invalid = await session.call_tool("read_evidence", {"record_id": "../labels.json"})
                self.assertTrue(invalid.isError)
