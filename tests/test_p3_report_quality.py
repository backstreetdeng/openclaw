# -*- coding: utf-8 -*-
"""P3 report quality system tests.

These tests keep the quality system inside strategy-orchestrator. They avoid
market DB/RAG dependencies by injecting deterministic fake tools.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORCH_ROOT = ROOT / "agents" / "strategy-orchestrator"
if str(ORCH_ROOT) not in sys.path:
    sys.path.insert(0, str(ORCH_ROOT))

from evidence.evidence_ledger import Evidence, EvidenceLedger  # noqa: E402
from executors.orchestrator import StrategyOrchestrator  # noqa: E402
from protocols.task_protocol import create_task_from_user_query  # noqa: E402
from quality.quality_gate import get_quality_gate  # noqa: E402


class P3ReportQualityTest(unittest.TestCase):
    def test_confidence_uses_p3_four_factor_model(self) -> None:
        ledger = EvidenceLedger()
        ledger.add_evidence(
            source="nl2sql-pg",
            tool="market_db",
            claim="比亚迪销量与份额",
            content="比亚迪最近12个月销量3,000,000辆，份额25%",
            time_range="最近12个月",
            data_caliber="乘用车结构化销量数据库口径",
            metrics=["销量", "份额", "趋势", "车型", "动力", "价格"],
            coverage_dimensions=["时间范围", "口径"],
            coverage_score=0.9,
            source_credibility=0.88,
            confidence=0.86,
        )
        ledger.add_evidence(
            source="rag",
            tool="vector_retriever",
            claim="比亚迪战略背景",
            content="行业报告显示比亚迪持续强化成本与产品矩阵优势",
            time_range="用户问题时间范围: 最近12个月；文档发布日期以元数据为准",
            data_caliber="向量检索文档摘要口径",
            coverage_dimensions=["行业报告", "趋势解释"],
            coverage_score=0.7,
            source_credibility=0.72,
            confidence=0.72,
        )

        confidence, details = ledger.calculate_overall_confidence()

        self.assertGreater(confidence, 0.6)
        for key in (
            "data_coverage_factor",
            "rag_coverage_factor",
            "source_credibility_factor",
            "conflict_factor",
            "model",
        ):
            self.assertIn(key, details)

    def test_quality_gate_requires_ledger_caliber_and_confidence_factors(self) -> None:
        result = {
            "user_intent": {
                "raw_query": "分析比亚迪最近12个月市场策略",
                "time_range": "最近12个月",
                "entities": ["比亚迪"],
            },
            "answer": "分析范围: 最近12个月\n涉及对象: 比亚迪\n证据账本: E1",
            "facts": [
                {
                    "claim": "比亚迪销量与份额",
                    "content": "销量3,000,000辆，份额25%",
                    "source": "nl2sql-pg",
                    "time_range": "最近12个月",
                    "data_caliber": "乘用车结构化销量数据库口径",
                    "confidence": 0.86,
                    "evidence": {"evidence_id": "E1"},
                }
            ],
            "inferences": [
                {
                    "claim": "份额防守是核心问题",
                    "source": "analysis-framework",
                    "confidence": 0.65,
                    "evidence": {"evidence_id": "E1"},
                }
            ],
            "confidence": 0.74,
            "confidence_details": {
                "data_coverage_factor": 0.9,
                "rag_coverage_factor": 0.65,
                "source_credibility_factor": 0.8,
                "conflict_factor": 1.0,
            },
            "evidence_sources": [
                {
                    "source": "nl2sql-pg",
                    "tool": "market_db",
                    "claim": "比亚迪销量与份额",
                    "time_range": "最近12个月",
                    "data_caliber": "乘用车结构化销量数据库口径",
                },
                {
                    "source": "rag",
                    "tool": "vector_retriever",
                    "claim": "比亚迪战略背景",
                    "time_range": "用户问题时间范围: 最近12个月；文档发布日期以元数据为准",
                    "data_caliber": "向量检索文档摘要口径",
                },
            ],
            "evidence_ledger": {
                "summary": {"overall_confidence": 0.74},
                "evidences": [{"evidence_id": "E1"}],
            },
            "missing_or_uncertain": [],
            "next_steps": ["补充同价位竞品月度份额变化"],
        }

        passed, checks = get_quality_gate().run_all(result)
        failed = [item.check_name for item in checks if not item.passed]

        self.assertTrue(passed, failed)

    def test_orchestrator_result_carries_p3_quality_payload(self) -> None:
        orchestrator = StrategyOrchestrator()

        def fake_nl2sql(param, task, state):
            return {
                "evidence": Evidence(
                    source="nl2sql-pg",
                    tool="fake_market_db",
                    claim="结构化数据查询: 比亚迪销量与份额",
                    content="比亚迪最近12个月销量3,000,000辆，份额25%",
                    time_range=task.user_intent.time_range,
                    data_caliber="乘用车结构化销量数据库口径",
                    metrics=["销量", "份额", "趋势", "车型", "动力", "价格"],
                    coverage_dimensions=["时间范围", "口径"],
                    coverage_score=0.9,
                    source_credibility=0.88,
                    confidence=0.86,
                )
            }

        def fake_rag(param, task, state):
            return {
                "evidence": Evidence(
                    source="rag",
                    tool="fake_vector_retriever",
                    claim="RAG 检索: 比亚迪战略背景",
                    content="行业报告显示比亚迪持续强化成本与产品矩阵优势",
                    time_range=f"用户问题时间范围: {task.user_intent.time_range}；文档发布日期以元数据为准",
                    data_caliber="向量检索文档摘要口径",
                    coverage_dimensions=["行业报告", "趋势解释"],
                    coverage_score=0.7,
                    source_credibility=0.72,
                    confidence=0.72,
                )
            }

        def fake_framework(param, task, state):
            return {
                "evidence": Evidence(
                    source="analysis-framework",
                    tool=param,
                    claim="框架分析: 竞争矩阵",
                    content="基于已入账证据，份额防守和主销车型稳定性是核心判断",
                    time_range=task.user_intent.time_range,
                    data_caliber="基于已入账证据的分析框架推断",
                    coverage_dimensions=["推断", "战略框架"],
                    coverage_score=0.6,
                    source_credibility=0.60,
                    confidence=0.65,
                )
            }

        orchestrator.register_tool("nl2sql-pg", fake_nl2sql)
        orchestrator.register_tool("rag", fake_rag)
        orchestrator.register_tool("analysis-framework", fake_framework)

        task = create_task_from_user_query(
            "分析比亚迪最近12个月市场策略",
            time_range="最近12个月",
            entities=["比亚迪"],
        )
        result = orchestrator.execute(task).to_dict()

        self.assertIn("evidence_ledger", result)
        self.assertIn("quality_summary", result)
        self.assertIn("quality_passed", result)
        self.assertTrue(result["quality_passed"], result.get("failed_quality_checks"))
        self.assertIn("data_coverage_factor", result["confidence_details"])
        self.assertIn("证据账本", result["answer"])
        self.assertIn("口径", result["answer"])

    def test_tavily_web_search_enters_evidence_ledger_with_quality_metadata(self) -> None:
        orchestrator = StrategyOrchestrator()

        def fake_nl2sql(param, task, state):
            return {
                "evidence": Evidence(
                    source="nl2sql-pg",
                    tool="fake_market_db",
                    claim="结构化数据查询: 比亚迪市场机会",
                    content="比亚迪最近12个月销量3,000,000辆，份额25%",
                    time_range=task.user_intent.time_range,
                    data_caliber="乘用车结构化销量数据库口径",
                    metrics=["销量", "份额", "趋势", "车型", "动力", "价格"],
                    coverage_dimensions=["时间范围", "口径"],
                    coverage_score=0.9,
                    source_credibility=0.88,
                    confidence=0.86,
                )
            }

        def fake_rag(param, task, state):
            return {
                "evidence": Evidence(
                    source="rag",
                    tool="fake_vector_retriever",
                    claim="RAG 检索: 比亚迪战略背景",
                    content="行业报告显示比亚迪持续强化成本与产品矩阵优势",
                    time_range=f"用户问题时间范围: {task.user_intent.time_range}；文档发布日期以元数据为准",
                    data_caliber="向量检索文档摘要口径",
                    coverage_dimensions=["行业报告", "趋势解释"],
                    coverage_score=0.7,
                    source_credibility=0.72,
                    confidence=0.72,
                )
            }

        def fake_framework(param, task, state):
            return {
                "evidence": Evidence(
                    source="analysis-framework",
                    tool=param,
                    claim="框架分析: SWOT",
                    content="基于已入账证据生成机会判断",
                    time_range=task.user_intent.time_range,
                    data_caliber="基于已入账证据的分析框架推断",
                    coverage_dimensions=["推断", "战略框架"],
                    coverage_score=0.6,
                    source_credibility=0.60,
                    confidence=0.65,
                )
            }

        def fake_tavily(query, max_results=6):
            return {
                "query": query,
                "answer": "比亚迪近期市场份额和出口策略受到关注。",
                "results": [
                    {
                        "title": "2026年比亚迪销量与市场份额分析",
                        "url": "https://www.autohome.com.cn/news/2026/06/byd-market.html",
                        "content": "2026年6月，比亚迪销量、交付和市场份额继续受到行业关注。",
                    },
                    {
                        "title": "比亚迪股票预测讨论",
                        "url": "https://xueqiu.com/example/byd",
                        "content": "低质量股票预测内容。",
                    },
                ],
            }

        orchestrator.register_tool("nl2sql-pg", fake_nl2sql)
        orchestrator.register_tool("rag", fake_rag)
        orchestrator.register_tool("analysis-framework", fake_framework)
        orchestrator._run_tavily_search = fake_tavily  # type: ignore[method-assign]

        task = create_task_from_user_query(
            "评估比亚迪最近12个月市场机会",
            time_range="最近12个月",
            entities=["比亚迪"],
        )
        result = orchestrator.execute(task).to_dict()
        web_evidence = [
            item for item in result["evidence_ledger"]["evidences"]
            if item.get("source") == "web-search"
        ]

        self.assertTrue(web_evidence)
        item = web_evidence[0]
        self.assertEqual(item["source_url"], "https://www.autohome.com.cn/news/2026/06/byd-market.html")
        self.assertIn("2026", item["source_date"])
        self.assertGreaterEqual(item["coverage_score"], 0.5)
        self.assertIn("source_grade=A", item["content"])
        self.assertIn("rejection_reason=accepted", item["content"])
        self.assertIn("剔除结果", " ".join(item.get("limitations") or []))
        self.assertIn("web-search", {src.get("source") for src in result["evidence_sources"]})


if __name__ == "__main__":
    unittest.main()
