# -*- coding: utf-8 -*-
"""Runtime helper tests for the live frontend bridge."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python_wrapper.live_agent_server import _normalize_time_range, _react_trace  # noqa: E402
from executors.orchestrator import create_orchestrator  # noqa: E402
from evidence.evidence_ledger import Evidence  # noqa: E402
from protocols.task_protocol import OutputFormat, TaskType, create_task_from_user_query  # noqa: E402


class LiveBridgeRuntimeTest(unittest.TestCase):
    def test_question_year_overrides_default_time_input(self) -> None:
        self.assertEqual(
            _normalize_time_range(
                "分析 2026 年中国新能源乘用车市场竞争格局",
                "最近12个月",
            ),
            "2026年",
        )

    def test_react_trace_exposes_plan_act_reflect_quality(self) -> None:
        trace = _react_trace(
            {
                "quality_passed": False,
                "failed_quality_checks": [{"check": "report_business_readability"}],
                "raw": {
                    "analysis_plan": {
                        "market_scope": "新能源乘用车",
                        "time_range": "2026年",
                        "target_brand": None,
                        "price_band": None,
                    },
                    "evidence_sources": [
                        {
                            "source": "nl2sql-pg",
                            "tool": "targeted_sql_pack",
                            "claim": "market overview",
                            "confidence": 0.8,
                        }
                    ],
                    "reflection": {
                        "overall_confidence": 0.7,
                        "evidence_gaps": ["rag"],
                        "conflicts": [],
                        "stagnation_count": 0,
                    },
                    "replan_history": [],
                },
            }
        )

        phases = [item["phase"] for item in trace]
        self.assertIn("Plan", phases)
        self.assertIn("Act", phases)
        self.assertIn("Reflect", phases)
        self.assertIn("Quality", phases)
        self.assertIn("2026年", trace[0]["summary"])

    def test_orchestrator_emits_live_react_events(self) -> None:
        events = []
        orchestrator = create_orchestrator(event_callback=events.append)

        def fake_tool(param, task, state):
            return {
                "evidences": [
                    Evidence(
                        source="test-source",
                        tool="fake-tool",
                        claim=f"fake evidence for {param}",
                        content="structured result",
                        time_range="test",
                        data_caliber="unit-test",
                        confidence=0.8,
                        coverage_score=0.8,
                    )
                ]
            }

        orchestrator.register_tool("targeted-sql-pack", fake_tool)
        orchestrator.register_tool("nl2sql-pg", fake_tool)
        task = create_task_from_user_query(
            "查询测试销量",
            target_output=OutputFormat.NATURAL_LANGUAGE,
            time_range="最近1个月",
            entities=[],
        )
        task.task_type = TaskType.SIMPLE_QUERY
        task.max_react_cycles = 1

        result = orchestrator.execute(task)

        self.assertEqual(result.cycles_used, 1)
        phases = [item["phase"] for item in events]
        self.assertIn("Plan", phases)
        self.assertIn("Act", phases)
        self.assertIn("Observe", phases)
        self.assertIn("Evidence", phases)
        self.assertIn("Reflect", phases)


if __name__ == "__main__":
    unittest.main()
