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


if __name__ == "__main__":
    unittest.main()
