# -*- coding: utf-8 -*-
"""Architecture boundary tests for the frontend live bridge.

The live bridge is allowed to normalize request metadata and relay to
strategy-orchestrator. It must not become the market-analysis brain again.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIVE_SERVER = ROOT / "python_wrapper" / "live_agent_server.py"


def _source() -> str:
    return LIVE_SERVER.read_text(encoding="utf-8")


def _function_calls(function_name: str) -> set[str]:
    tree = ast.parse(_source())
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    if isinstance(func, ast.Name):
                        calls.add(func.id)
                    elif isinstance(func, ast.Attribute):
                        calls.add(func.attr)
            break
    return calls


class BridgeBoundaryTest(unittest.TestCase):
    def test_live_bridge_relays_to_strategy_orchestrator(self) -> None:
        src = _source()
        calls = _function_calls("_run_analysis")

        self.assertIn("_run_orchestrated_analysis", calls)
        self.assertIn(
            "from executors.orchestrator import create_orchestrator",
            src,
        )
        self.assertNotIn("market_strategy.orchestrator_integration", src)
        self.assertIn("sse_relay_to_strategy_orchestrator", src)

    def test_live_bridge_does_not_embed_business_tool_chain(self) -> None:
        src = _source()
        forbidden_tokens = [
            "LocalSkillBridge",
            "seven_step_report_engine",
            "build_analysis_plan",
            "run_structured_market_queries",
            "filter_rag_results",
            "filter_tavily_results",
            "build_evidence_store",
            "build_seven_step_report",
            "build_insight_cards",
        ]

        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(
                    token,
                    src,
                    f"live bridge must not own business analysis logic: {token}",
                )

    def test_run_analysis_does_not_directly_call_market_tools(self) -> None:
        calls = _function_calls("_run_analysis")
        forbidden_calls = {
            "run_structured_market_queries",
            "filter_rag_results",
            "filter_tavily_results",
            "build_evidence_store",
            "build_seven_step_report",
            "build_insight_cards",
        }

        self.assertFalse(calls & forbidden_calls)


if __name__ == "__main__":
    unittest.main()
