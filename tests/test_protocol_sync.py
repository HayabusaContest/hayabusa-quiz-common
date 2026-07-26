"""プロトコル正典 protocol/protocol.json と、各実装の定数が一致するかを検査する。

横並び clone(common / server / agent が同じ親ディレクトリ)を前提に:
  - agent の protocol.py(Request / ViewType / Mode / PASS / PROTOCOL_VERSION)
  - server の protocol.go(const 文字列)
が正典と食い違っていないことを確認する。実装が見つからない環境では該当テストを skip。

実行: cd hayabusa-quiz-common && python -m unittest discover -s tests
"""
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

COMMON = Path(__file__).resolve().parent.parent
SPEC = json.loads((COMMON / "protocol" / "protocol.json").read_text(encoding="utf-8"))
AGENT_PROTOCOL = COMMON.parent / "hayabusa-quiz-agent" / "protocol.py"
SERVER_PROTOCOL = COMMON.parent / "hayabusa-quiz-server" / "protocol.go"

REQ = set(SPEC["requests"])
VIEWS = set(SPEC["view_events"])
MODES = set(SPEC["modes"])
PASS = SPEC["reply_keywords"]["pass"]
VERSION = SPEC["protocol_version"]


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("agent_protocol", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["agent_protocol"] = mod  # dataclass 定義に必要(module を sys.modules へ)
    spec.loader.exec_module(mod)
    return mod


class TestAgentProtocol(unittest.TestCase):
    @unittest.skipUnless(AGENT_PROTOCOL.exists(), "agent protocol.py not found (side-by-side clone required)")
    def test_agent_matches_spec(self):
        m = _load(AGENT_PROTOCOL)
        self.assertEqual({r.value for r in m.Request}, REQ, "Request の集合が protocol.json と不一致")
        self.assertEqual({v.value for v in m.ViewType}, VIEWS, "ViewType の集合が protocol.json と不一致")
        self.assertEqual({x.value for x in m.Mode}, MODES, "Mode の集合が protocol.json と不一致")
        self.assertEqual(m.PASS, PASS, "PASS キーワード不一致")
        self.assertEqual(m.PROTOCOL_VERSION, VERSION, "PROTOCOL_VERSION 不一致")


class TestServerProtocol(unittest.TestCase):
    @unittest.skipUnless(SERVER_PROTOCOL.exists(), "server protocol.go not found (side-by-side clone required)")
    def test_server_matches_spec(self):
        text = SERVER_PROTOCOL.read_text(encoding="utf-8")
        consts = set(re.findall(r'=\s*"([^"]+)"', text))  # const 文字列値の集合
        for name in REQ:
            self.assertIn(name, consts, f"server protocol.go に request 定数 {name!r} が無い")
        for name in VIEWS:
            self.assertIn(name, consts, f"server protocol.go に view 定数 {name!r} が無い")
        for name in MODES:
            self.assertIn(name, consts, f"server protocol.go に mode 定数 {name!r} が無い")
        self.assertIn(PASS, consts, "server protocol.go に pass キーワードが無い")
        self.assertIn(VERSION, consts, "server protocol.go に PROTOCOL_VERSION が無い")


if __name__ == "__main__":
    unittest.main()
