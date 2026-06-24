# -*- coding: utf-8 -*-
"""Runtime helper tests for the live frontend bridge."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python_wrapper.live_agent_server import (  # noqa: E402
    AnalyzeRequest,
    _classify_entry_route,
    _installed_skill_inventory,
    _is_direct_response_query,
    _llm_plan_provider,
    _normalize_time_range,
    _run_analysis,
    _react_trace,
)
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

    def test_meta_help_query_does_not_start_orchestration(self) -> None:
        self.assertTrue(_is_direct_response_query("你能做什么？"))
        self.assertTrue(_is_direct_response_query("你能帮我什么"))
        self.assertTrue(_is_direct_response_query("你可以帮我什么"))
        self.assertTrue(_is_direct_response_query("你能给我什么帮助"))
        self.assertTrue(_is_direct_response_query("这个智能体怎么用"))
        self.assertTrue(_is_direct_response_query("你是干嘛的"))
        self.assertTrue(_is_direct_response_query("你好"))
        self.assertFalse(_is_direct_response_query("分析比亚迪最近12个月市场策略"))
        self.assertFalse(_is_direct_response_query("你能帮我分析比亚迪最近12个月市场策略吗"))

        direct_route = _classify_entry_route("你能帮我什么")
        analysis_route = _classify_entry_route("你能帮我分析比亚迪最近12个月市场策略吗")
        self.assertEqual(direct_route["route"], "capability_help")
        self.assertEqual(analysis_route["route"], "market_analysis")
        self.assertIn("帮我", "".join(direct_route["help_hits"]))
        self.assertIn("分析", analysis_route["analysis_hits"])
        self.assertIn("比亚迪", analysis_route["domain_hits"])

        result = _run_analysis(AnalyzeRequest(question="你能帮我什么"))

        self.assertEqual(result["analysis_type"], "capability_help")
        self.assertEqual(result["cycles_used"], 0)
        self.assertEqual(result["stop_reason"], "capability_help_no_market_orchestration")
        self.assertIn("我能做什么", result["report"])
        self.assertNotIn("七步法业务战略分析报告", result["report"])
        self.assertEqual(result["execution_trace"][0]["detail"]["route"], "capability_help")

    def test_skill_inventory_route_returns_actual_skills(self) -> None:
        route = _classify_entry_route("你有哪些skill")
        self.assertEqual(route["route"], "skill_inventory")
        self.assertTrue(_is_direct_response_query("你有哪些skill"))

        skills = _installed_skill_inventory()
        skill_names = {item["name"] for item in skills}
        self.assertIn("automotive-strategy-analysis", skill_names)

        result = _run_analysis(AnalyzeRequest(question="你有哪些skill"))
        self.assertEqual(result["analysis_type"], "skill_inventory")
        self.assertEqual(result["cycles_used"], 0)
        self.assertIn("当前可用 Skills", result["report"])
        self.assertIn("automotive-strategy-analysis", result["report"])
        self.assertEqual(result["skill_trace"], [])

    def test_user_insight_route_does_not_enter_market_analysis(self) -> None:
        route = _classify_entry_route("帮我做一下用户洞察和目标客群画像")
        self.assertEqual(route["route"], "user_insight")
        self.assertTrue(_is_direct_response_query("帮我做一下用户洞察和目标客群画像"))

        result = _run_analysis(AnalyzeRequest(question="帮我做一下用户洞察和目标客群画像"))
        self.assertEqual(result["analysis_type"], "user_insight")
        self.assertEqual(result["cycles_used"], 0)
        self.assertIn("不会误进入市场战略分析链路", result["report"])

    def test_general_chat_route_uses_direct_response_without_market_tools(self) -> None:
        route = _classify_entry_route("今天天气不错，聊两句")
        self.assertEqual(route["route"], "general_chat")

        result = _run_analysis(AnalyzeRequest(question="今天天气不错，聊两句"))
        self.assertEqual(result["analysis_type"], "general_chat")
        self.assertEqual(result["cycles_used"], 0)
        self.assertEqual(result["skill_trace"], [])
        self.assertNotIn("七步法业务战略分析报告", result["report"])

    def test_llm_plan_provider_validates_tool_steps(self) -> None:
        import os
        from unittest.mock import patch

        context = {
            "raw_query": "分析15-20万插混SUV机会",
            "task_type": "opportunity_assessment",
            "time_range": "最近12个月",
            "entities": ["15-20万", "插混", "SUV"],
            "analysis_plan": {},
            "completed_steps": [],
            "evidence_gaps": [],
        }
        fake_response = {
            "ok": True,
            "text": '{"steps":["targeted-sql-pack:market_metrics","unknown-tool:bad","rag:validation"]}',
        }
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            with patch("python_wrapper.live_agent_server._call_openai_compatible_chat", return_value=fake_response):
                steps = _llm_plan_provider(context)

        self.assertIn("targeted-sql-pack:market_metrics", steps)
        self.assertIn("rag:validation", steps)
        self.assertIn("analysis-framework:automotive_strategy_seven_stage", steps)
        self.assertIn("report-generator-agent:quality_review", steps)
        self.assertNotIn("unknown-tool:bad", steps)

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
