"""
Strategy Orchestrator - 自主编排执行器

ReAct 循环实现：
- Plan: 理解问题，拆解任务，选择工具
- Act: 调用能力
- Observe: 读取结果
- Reflect: 判断是否足够
- Re-plan: 调整或终止
"""

import json
import logging
import importlib.util
import re
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

# 导入协议和组件
import sys
import os

# 尝试导入（如果不存在则创建 mock）
try:
    from .protocols.task_protocol import (
        OrchestrationTask,
        OrchestrationResult,
        TaskType,
        OutputFormat,
        create_task_from_user_query
    )
    from .evidence.evidence_ledger import (
        EvidenceLedger,
        Evidence,
        get_evidence_ledger,
        reset_evidence_ledger
    )
    from .quality.quality_gate import (
        QualityGate,
        get_quality_gate,
        generate_quality_report
    )
    from .quality.rollback_handler import (
        RollbackHandler,
        FailureContext,
        FailureType,
        detect_failure_type,
        get_rollback_handler
    )
except ImportError as e:
    # 如果在 OpenClaw workspace 中，添加路径
    workspace_path = r"C:\Users\11489\.openclaw\workspace-market\agents\strategy-orchestrator"
    if workspace_path not in sys.path:
        sys.path.insert(0, workspace_path)
    
    from protocols.task_protocol import (
        OrchestrationTask,
        OrchestrationResult,
        TaskType,
        OutputFormat,
        create_task_from_user_query
    )
    from evidence.evidence_ledger import (
        EvidenceLedger,
        Evidence,
        get_evidence_ledger,
        reset_evidence_ledger
    )
    from quality.quality_gate import (
        QualityGate,
        get_quality_gate,
        generate_quality_report
    )
    from quality.rollback_handler import (
        RollbackHandler,
        FailureContext,
        FailureType,
        detect_failure_type,
        get_rollback_handler
    )


logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    success: bool
    result: Any = None
    error: str = None
    execution_time: float = 0.0
    evidence: Evidence = None
    evidences: List[Evidence] = field(default_factory=list)


@dataclass
class ReactState:
    """ReAct 循环状态"""
    cycle: int = 0
    current_plan: List[str] = field(default_factory=list)
    completed_steps: List[str] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)
    is_complete: bool = False
    stop_reason: str = ""
    should_stop: bool = False


class StrategyOrchestrator:
    """
    战略编排器
    
    核心职责：
    1. 接收主 Agent 的任务
    2. 执行 ReAct 循环
    3. 维护证据账本
    4. 控制质量门禁
    5. 处理回退逻辑
    """
    
    def __init__(self):
        self.evidence_ledger = get_evidence_ledger()
        self.quality_gate = get_quality_gate()
        self.rollback_handler = get_rollback_handler()
        
        # 工具注册表
        self._tools: Dict[str, Callable] = {}
        self._register_default_tools()
    
    @property
    def tool_registry(self):
        return self
    
    def register_tool(self, name, tool_func):
        self._tools[name] = tool_func
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 这里注册实际可用的工具
        # 在实际运行时会通过配置注入
        
        # 结构化数据查询
        self._tools["nl2sql-pg"] = self._tool_nl2sql
        
        # RAG 检索
        self._tools["pg-vector-search"] = self._tool_rag_retrieve
        self._tools["rag"] = self._tool_rag_retrieve
        
        # 分析框架
        self._tools["analysis-framework"] = self._tool_analysis_framework
        self._tools["pest"] = self._tool_pest
        self._tools["swot"] = self._tool_swot
        self._tools["porter"] = self._tool_porter
        self._tools["4p"] = self._tool_4p
        
        # 报告生成
        self._tools["report-generator"] = self._tool_report_generate
        self._tools["report-agent"] = self._tool_report_generate
        
        # 搜索
        self._tools["web-search"] = self._tool_web_search
    
    def register_tool(self, name: str, tool_func: Callable):
        """注册工具"""
        self._tools[name] = tool_func
    
    def execute(self, task: OrchestrationTask) -> OrchestrationResult:
        """
        执行编排任务
        
        Main entry point for 主 Agent
        """
        logger.info(f"Starting orchestration for task: {task.task_id}")
        
        # 重置证据账本（新任务）
        reset_evidence_ledger()
        self.evidence_ledger = get_evidence_ledger()
        
        # 初始化 ReAct 状态
        state = ReactState()
        
        # 执行 ReAct 循环
        result = self._run_react_loop(task, state)
        
        # 质量检查
        result = self._apply_quality_gate(result)
        
        logger.info(f"Orchestration complete: {result.task_id}, cycles={result.cycles_used}")
        
        return result
    
    def _run_react_loop(
        self,
        task: OrchestrationTask,
        state: ReactState
    ) -> OrchestrationResult:
        """
        执行 ReAct 循环
        
        循环直到：
        1. 达到最大循环次数
        2. 证据足够
        3. 需要向用户追问
        4. 所有工具都失败
        """
        max_cycles = task.max_react_cycles
        
        while state.cycle < max_cycles and not state.should_stop:
            state.cycle += 1
            logger.info(f"Cycle {state.cycle}/{max_cycles}")
            
            # ===== Plan =====
            plan = self._plan(task, state)
            state.current_plan = plan
            logger.info(f"Plan: {plan}")
            
            # ===== Act =====
            for step in plan:
                if state.should_stop:
                    break
                
                tool_result = self._execute_step(step, task, state)
                state.tool_results.append(tool_result)
                
                # 记录证据
                evidences_to_add = list(tool_result.evidences or [])
                if tool_result.evidence:
                    evidences_to_add.append(tool_result.evidence)
                for evidence in evidences_to_add:
                    self.evidence_ledger.add_evidence(
                        source=evidence.source,
                        tool=evidence.tool,
                        claim=evidence.claim,
                        content=evidence.content,
                        time_range=evidence.time_range,
                        metrics=evidence.metrics,
                        data_caliber=evidence.data_caliber,
                        source_url=evidence.source_url,
                        source_date=evidence.source_date,
                        source_credibility=evidence.source_credibility,
                        coverage_dimensions=evidence.coverage_dimensions,
                        coverage_score=evidence.coverage_score,
                        confidence=evidence.confidence,
                        limitations=evidence.limitations
                    )
                
                # 记录已完成步骤
                state.completed_steps.append(step)
                
                # 检查是否应该停止
                if self._check_stop_conditions(task, state):
                    state.should_stop = True
                    break
            
            # ===== Observe & Reflect =====
            self._observe_and_reflect(task, state)
            
            # ===== Re-plan =====
            if not state.should_stop:
                self._replan(task, state)
        
        # ===== 构建结果 =====
        return self._build_result(task, state)
    
    def _plan(
        self,
        task: OrchestrationTask,
        state: ReactState
    ) -> List[str]:
        """
        Plan 阶段：理解问题，拆解任务，选择工具
        """
        plan = []
        task_type = task.task_type
        user_intent = task.user_intent
        
        # 根据任务类型决定需要哪些证据
        if task_type == TaskType.MARKET_TREND:
            # 市场趋势：需要结构化数据 + RAG 上下文
            plan = ["nl2sql-pg:get_market_trend", "rag:get_market_reports"]
            if not user_intent.constraints or "no-framework" not in user_intent.constraints:
                plan.append("analysis-framework:trend_analysis")
        
        elif task_type == TaskType.COMPETITOR_ANALYSIS:
            # 竞品分析：需要结构化数据 + RAG + 框架
            plan = ["nl2sql-pg:get_sales_by_brand", "rag:get_competitor_info"]
            if not user_intent.constraints or "no-framework" not in user_intent.constraints:
                plan.append("analysis-framework:competitive_matrix")
        
        elif task_type == TaskType.POLICY_IMPACT:
            # 政策影响：RAG 为主
            plan = ["rag:get_policies", "nl2sql-pg:get_market_data_for_policy"]
            if not user_intent.constraints or "no-framework" not in user_intent.constraints:
                plan.append("analysis-framework:pest_political")
        
        elif task_type == TaskType.OPPORTUNITY_ASSESSMENT:
            # 机会评估：多源 + SWOT + TAM
            plan = ["nl2sql-pg:get_market_size", "rag:get_market_reports", "web-search:get_trends"]
            if not user_intent.constraints or "no-framework" not in user_intent.constraints:
                plan.append("analysis-framework:swot")
        
        elif task_type == TaskType.COMPREHENSIVE_RESEARCH:
            # 综合研究：全量
            plan = [
                "nl2sql-pg:get_full_market_data",
                "rag:get_all_relevant_docs",
                "analysis-framework:comprehensive"
            ]
        
        elif task_type == TaskType.SIMPLE_QUERY:
            # 简单查询：只取结构化数据
            plan = ["nl2sql-pg:get_data"]
        
        else:
            # 未知类型：保守策略
            plan = ["nl2sql-pg:get_basic_data", "rag:get_context"]
        
        return plan
    
    def _execute_step(
        self,
        step: str,
        task: OrchestrationTask,
        state: ReactState
    ) -> ToolResult:
        """
        Act 阶段：执行单个步骤
        """
        import time
        start_time = time.time()
        
        # 解析步骤 (tool:param)
        if ":" in step:
            tool_name, param = step.split(":", 1)
        else:
            tool_name, param = step, ""
        
        # 获取工具
        tool_func = self._tools.get(tool_name)
        
        if not tool_func:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool not found: {tool_name}",
                execution_time=time.time() - start_time
            )
        
        try:
            # 调用工具
            result = tool_func(param, task, state)
            
            # 从结果中提取 evidence
            evidence = None
            evidences = []
            if isinstance(result, dict) and 'evidence' in result:
                evidence = result['evidence']
            if isinstance(result, dict) and 'evidences' in result:
                evidences = result.get('evidences') or []
            
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                evidence=evidence,
                evidences=evidences,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            # 捕获异常，返回失败
            failure_type = detect_failure_type(e, tool_name)
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _observe_and_reflect(
        self,
        task: OrchestrationTask,
        state: ReactState
    ):
        """
        Observe & Reflect 阶段：判断证据是否足够
        """
        # 统计成功/失败
        success_count = sum(1 for r in state.tool_results if r.success)
        total_count = len(state.tool_results)
        
        # 获取证据账本状态
        overall_conf, conf_details = self.evidence_ledger.calculate_overall_confidence()
        
        logger.info(f"Evidence status: {success_count}/{total_count} tools succeeded")
        logger.info(f"Overall confidence: {overall_conf}")
        
        # 检查冲突
        conflicts = self.evidence_ledger.get_conflicts()
        if conflicts:
            logger.warning(f"Found {len(conflicts)} evidence conflicts")
        
        # 判断是否足够
        # 标准：
        # 1. 至少有 2 个工具成功
        # 2. 置信度 >= 0.6
        # 3. 没有高严重性冲突
        
        has_high_conflict = any(c.get("severity") == "high" for c in conflicts)
        
        if success_count >= 2 and overall_conf >= 0.6 and not has_high_conflict:
            state.is_complete = True
            state.should_stop = True
            state.stop_reason = "Sufficient evidence collected"
            logger.info("Evidence sufficient, marking complete")
        
        # 检查是否需要追问用户
        missing = self._check_missing_critical_evidence(task, state)
        if missing:
            state.stop_reason = f"Missing critical info: {missing}"
            logger.warning(f"Missing critical evidence: {missing}")
    
    def _replan(
        self,
        task: OrchestrationTask,
        state: ReactState
    ):
        """
        Re-plan 阶段：调整计划
        """
        # 如果有失败的步骤，尝试回退
        failed_results = [r for r in state.tool_results if not r.success]
        
        if failed_results:
            last_failure = failed_results[-1]
            
            # 获取回退策略
            failure_context = FailureContext(
                failure_type=detect_failure_type(Exception(last_failure.error or ""), last_failure.tool_name),
                original_operation=last_failure.tool_name,
                error_message=last_failure.error or "Unknown error",
                evidence_so_far=self.evidence_ledger.generate_report(),
                user_intent=task.user_intent.to_dict() if task.user_intent else {},
                retry_count=len(failed_results) - 1
            )
            
            fallback = self.rollback_handler.get_fallback(
                failure_context.failure_type,
                failure_context
            )
            
            # 如果需要停止，设置停止标志
            if self.rollback_handler.should_stop(failure_context):
                state.should_stop = True
                state.stop_reason = "All fallback strategies exhausted"
                return
            
            # 否则记录回退动作
            logger.info(f"Fallback action: {fallback.action_type}")
    
    def _check_stop_conditions(
        self,
        task: OrchestrationTask,
        state: ReactState
    ) -> bool:
        """检查停止条件"""
        # 循环次数用完
        if state.cycle >= task.max_react_cycles:
            state.stop_reason = "Max cycles reached"
            return True
        
        # 证据已足够
        if state.is_complete:
            state.stop_reason = "Evidence sufficient"
            return True
        
        # 检查缺失关键信息
        missing = self._check_missing_critical_evidence(task, state)
        if missing and not self._has_pending_structured_step(state):
            state.stop_reason = f"Missing critical: {missing}"
            return True
        
        return False

    def _has_pending_structured_step(self, state: ReactState) -> bool:
        """判断当前计划里是否还有未执行的结构化数据步骤。"""
        completed = set(state.completed_steps)
        return any(
            step not in completed and "nl2sql" in step
            for step in state.current_plan
        )
    
    def _check_missing_critical_evidence(
        self,
        task: OrchestrationTask,
        state: ReactState
    ) -> Optional[str]:
        """检查缺失的关键证据"""
        # 如果用户问题涉及具体品牌/车型但没有结构化数据
        entities = task.user_intent.entities if task.user_intent else []
        has_structured = any("nl2sql" in r.tool_name and r.success for r in state.tool_results)
        
        if entities and not has_structured:
            return "Brand/model data required but not available"
        
        return None
    
    def _build_result(
        self,
        task: OrchestrationTask,
        state: ReactState
    ) -> OrchestrationResult:
        """构建最终结果"""
        # 从证据账本生成结果
        report = self.evidence_ledger.generate_report()
        
        # 构建 facts 和 inferences
        facts = []
        inferences = []
        
        for evidence in self.evidence_ledger.evidences.values():
            evidence_ref = {
                "evidence_id": evidence.evidence_id,
                "source": evidence.source,
                "tool": evidence.tool,
                "claim": evidence.claim,
                "confidence": evidence.confidence,
                "time_range": evidence.time_range,
                "data_caliber": evidence.data_caliber,
            }
            if evidence.source in ["nl2sql-pg", "rag"]:
                facts.append({
                    "claim": evidence.claim,
                    "content": evidence.content[:200],
                    "source": evidence.source,
                    "confidence": evidence.confidence,
                    "time_range": evidence.time_range,
                    "data_caliber": evidence.data_caliber,
                    "evidence": evidence_ref
                })
            else:
                inferences.append({
                    "claim": evidence.claim,
                    "source": evidence.source,
                    "confidence": evidence.confidence,
                    "evidence": evidence_ref
                })
        
        # 识别机会和风险
        opportunities = self._identify_opportunities(report)
        risks = self._identify_risks(report)
        
        # 置信度
        overall_conf, conf_details = self.evidence_ledger.calculate_overall_confidence()
        
        # 构建 answer
        answer = self._build_answer(task, report, opportunities, risks)
        
        # 冲突
        conflicts = self.evidence_ledger.get_conflicts()
        missing_or_uncertain = []
        
        if conflicts:
            missing_or_uncertain.append(f"存在 {len(conflicts)} 项证据冲突")
        
        if overall_conf < 0.7:
            missing_or_uncertain.append("总体置信度低于70%，需要补充更高质量证据后再用于决策")

        if not state.is_complete:
            missing_or_uncertain.append("证据可能不够完整")
        
        return OrchestrationResult(
            task_id=task.task_id,
            success=state.is_complete or overall_conf >= 0.5,
            user_intent=task.user_intent.to_dict() if task.user_intent else {},
            answer=answer,
            facts=facts,
            inferences=inferences,
            recommendations=self._generate_recommendations(report, opportunities),
            risks=risks,
            confidence=overall_conf,
            confidence_details=conf_details,
            evidence_sources=[
                {
                    "evidence_id": e.evidence_id,
                    "source": e.source,
                    "tool": e.tool,
                    "claim": e.claim,
                    "time_range": e.time_range,
                    "data_caliber": e.data_caliber,
                    "source_url": e.source_url,
                    "source_date": e.source_date,
                    "confidence": e.confidence,
                }
                for e in self.evidence_ledger.evidences.values()
            ],
            evidence_ledger=report,
            missing_or_uncertain=missing_or_uncertain,
            next_steps=self._generate_next_steps(task, state),
            errors=[r.error for r in state.tool_results if not r.success and r.error],
            stop_reason=state.stop_reason,
            cycles_used=state.cycle
        )
    
    def _apply_quality_gate(self, result: OrchestrationResult) -> OrchestrationResult:
        """应用质量门禁"""
        result_dict = result.to_dict()
        passed, checks = self.quality_gate.run_all(result_dict)
        failed_checks = [
            {
                "check": item.check_name,
                "level": getattr(item.level, "value", str(item.level)),
                "message": item.message,
                "suggestions": item.suggestions,
            }
            for item in checks
            if not item.passed
        ]

        result.quality_passed = passed
        result.failed_quality_checks = failed_checks
        result.quality_summary = {
            "quality_passed": passed,
            "total_checks": len(checks),
            "passed_checks": sum(1 for item in checks if item.passed),
            "failed_checks": failed_checks,
        }
        
        if not passed:
            logger.warning("Quality gate not passed")
        
        return result
    
    # ===== 工具实现 =====
    
    def _tool_nl2sql(self, param: str, task: OrchestrationTask, state: ReactState) -> Dict:
        """结构化数据查询工具"""
        try:
            # 导入实际的数据库查询模块
            sys.path.insert(0, r"E:\AI\data\envs\car_agent_env\ai-decision\rag-engine")
            from market_strategy.knowledge_base import MarketKnowledgeBase
            
            kb = MarketKnowledgeBase()
            
            # 根据参数决定查询类型
            if "brand" in param.lower():
                data = kb.get_sales_by_brand(
                    time_range=task.user_intent.time_range if task.user_intent else "最近12个月",
                    top_n=20
                )
            elif "trend" in param.lower():
                data = kb.get_sales_trend()
            elif "overview" in param.lower() or "market" in param.lower():
                data = kb.get_market_overview(
                    time_range=task.user_intent.time_range if task.user_intent else "最近12个月"
                )
            else:
                data = kb.get_data_summary()
            
            kb.close()
            
            # 返回证据
            return {
                "data": data,
                "evidence": Evidence(
                    source="nl2sql-pg",
                    tool="knowledge_base",
                    claim=f"结构化数据查询: {param}",
                    content=str(data)[:500],
                    time_range=task.user_intent.time_range if task.user_intent else "最近12个月",
                    data_caliber="结构化销量/份额数据库口径，以 MarketKnowledgeBase 返回字段为准",
                    source_credibility=0.85,
                    coverage_dimensions=["销量", "份额", "增速", "时间范围", "口径"],
                    coverage_score=0.75,
                    confidence=0.85,
                    metrics=["销量", "份额", "增速"]
                )
            }
        
        except Exception as e:
            logger.error(f"nl2sql tool failed: {e}")
            raise
    
    def _tool_rag_retrieve(self, param: str, task: OrchestrationTask, state: ReactState) -> Dict:
        """RAG 检索工具"""
        try:
            sys.path.insert(0, r"E:\AI\data\envs\car_agent_env\ai-decision\rag-engine")
            from retrieval.retriever import retrieve
            
            query = task.user_intent.raw_query if task.user_intent else param
            results = retrieve(query, top_k=5)
            
            # 构建证据
            contents = [r["document"][:200] for r in results]
            evidence_content = "; ".join(contents)
            
            return {
                "results": results,
                "evidence": Evidence(
                    source="rag",
                    tool="vector_retriever",
                    claim=f"RAG 检索: {query[:50]}",
                    content=evidence_content,
                    time_range=f"用户问题时间范围: {task.user_intent.time_range if task.user_intent else '未指定'}；文档发布日期以元数据为准",
                    data_caliber="向量检索文档摘要口径，非结构化统计口径",
                    source_credibility=0.70,
                    coverage_dimensions=["行业报告", "政策背景", "趋势解释"],
                    coverage_score=0.60 if results else 0.20,
                    confidence=0.7,
                    limitations=["仅返回已有文档"]
                )
            }
        
        except Exception as e:
            logger.error(f"RAG tool failed: {e}")
            raise
    
    def _tool_analysis_framework(self, param: str, task: OrchestrationTask, state: ReactState) -> Dict:
        """分析框架工具"""
        # 简化实现
        return {
            "framework": param,
            "evidence": Evidence(
                source="analysis-framework",
                tool=param,
                claim=f"框架分析: {param}",
                content="框架分析已完成",
                data_caliber="基于已入账证据的分析框架推断，非原始数据来源",
                source_credibility=0.60,
                coverage_dimensions=["推断", "战略框架"],
                coverage_score=0.50,
                confidence=0.6
            )
        }
    
    def _tool_pest(self, param: str, task: OrchestrationTask, state: ReactState) -> Dict:
        return self._tool_analysis_framework("pest", task, state)
    
    def _tool_swot(self, param: str, task: OrchestrationTask, state: ReactState) -> Dict:
        return self._tool_analysis_framework("swot", task, state)
    
    def _tool_porter(self, param: str, task: OrchestrationTask, state: ReactState) -> Dict:
        return self._tool_analysis_framework("porter", task, state)
    
    def _tool_4p(self, param: str, task: OrchestrationTask, state: ReactState) -> Dict:
        return self._tool_analysis_framework("4p", task, state)
    
    def _tool_report_generate(self, param: str, task: OrchestrationTask, state: ReactState) -> Dict:
        """报告生成工具"""
        report = self._generate_markdown_report(task, state)
        return {
            "report": report,
            "evidence": Evidence(
                source="report-generator",
                tool="report",
                claim="报告已生成",
                content=report[:200],
                data_caliber="基于证据账本的报告生成结果，非新增事实来源",
                source_credibility=0.55,
                coverage_dimensions=["报告"],
                coverage_score=0.50,
                confidence=0.7
            )
        }
    
    def _tool_web_search(self, param: str, task: OrchestrationTask, state: ReactState) -> Dict:
        """Tavily 网络搜索工具。"""
        query = self._build_tavily_query(param, task)
        try:
            raw = self._run_tavily_search(query=query, max_results=6)
        except Exception as exc:
            fallback = Evidence(
                source="web-search",
                tool="tavily-search",
                claim=f"Tavily 检索失败: {query[:80]}",
                content=str(exc),
                time_range="实时外部检索；未获取到可用结果",
                data_caliber="Tavily 外部网页检索口径；本次调用失败",
                source_credibility=0.20,
                coverage_dimensions=["外部补证"],
                coverage_score=0.05,
                confidence=0.2,
                limitations=[f"Tavily 调用失败: {exc}"]
            )
            return {
                "success": False,
                "query": query,
                "results": [],
                "rejected": [],
                "evidences": [fallback],
                "error": str(exc),
            }

        filtered = self._filter_tavily_results(raw, task)
        evidences = self._build_tavily_evidences(query, filtered, task)
        if not evidences:
            rejected_summary = "; ".join(
                f"{item.get('reason')}:{item.get('title') or item.get('url')}"
                for item in filtered.get("rejected", [])[:5]
            ) or "Tavily 未返回合格网页证据"
            evidences = [
                Evidence(
                    source="web-search",
                    tool="tavily-search",
                    claim=f"Tavily 外部补证无合格结果: {query[:80]}",
                    content=rejected_summary,
                    time_range="实时外部检索；无合格结果",
                    data_caliber="Tavily 外部网页检索口径；低质量或实体不匹配结果已剔除",
                    source_credibility=0.25,
                    coverage_dimensions=["外部补证"],
                    coverage_score=0.10,
                    confidence=0.25,
                    limitations=["无合格 Tavily 结果", rejected_summary[:180]]
                )
            ]

        return {
            "success": True,
            "query": query,
            "raw_count": filtered.get("raw_count", 0),
            "results": filtered.get("accepted", []),
            "rejected": filtered.get("rejected", []),
            "rejected_count": len(filtered.get("rejected", [])),
            "evidences": evidences,
        }

    def _run_tavily_search(self, query: str, max_results: int = 6) -> Dict[str, Any]:
        """调用本地 tavily-search skill。"""
        workspace_root = Path(__file__).resolve().parents[3]
        tavily_script = workspace_root / "skills" / "tavily-search" / "scripts" / "tavily_search.py"
        if not tavily_script.exists():
            raise RuntimeError(f"tavily_search.py not found: {tavily_script}")

        spec = importlib.util.spec_from_file_location("workspace_tavily_search", tavily_script)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load tavily_search.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.tavily_search(
            query=query,
            max_results=max(1, min(max_results, 10)),
            include_answer=True,
            search_depth="basic",
        )

    def _build_tavily_query(self, param: str, task: OrchestrationTask) -> str:
        intent = task.user_intent
        raw_query = intent.raw_query if intent else ""
        time_range = intent.time_range if intent else ""
        entities = " ".join(intent.entities or []) if intent else ""
        topic = param.replace("_", " ") if param else "market strategy"
        terms = "销量 交付 市场份额 竞品 战略 政策"
        return " ".join(part for part in [entities, raw_query, time_range, topic, terms] if part)

    def _filter_tavily_results(self, raw: Dict[str, Any], task: OrchestrationTask) -> Dict[str, Any]:
        rows = raw.get("results") or []
        entities = task.user_intent.entities if task.user_intent else []
        accepted = []
        rejected = []
        for item in rows:
            normalized = self._normalize_tavily_item(item)
            haystack = " ".join([
                normalized.get("title", ""),
                normalized.get("url", ""),
                normalized.get("snippet", ""),
            ])
            source_grade = self._source_grade(normalized.get("url", ""), normalized.get("title", ""))
            entity_ok = True if not entities else self._contains_any(haystack, entities)
            if source_grade == "C":
                reason = "low_quality_source"
            elif not entity_ok:
                reason = "entity_mismatch"
            else:
                reason = ""

            normalized["source_grade"] = source_grade
            normalized["source_date"] = self._infer_source_date(
                normalized.get("title", ""),
                normalized.get("snippet", ""),
                normalized.get("url", ""),
            )
            normalized["coverage_score"] = self._web_coverage_score(normalized, task, entity_ok)
            normalized["source_credibility"] = self._source_credibility_from_grade(source_grade)

            if reason:
                rejected_item = dict(normalized)
                rejected_item["rejection_reason"] = reason
                rejected.append(rejected_item)
            else:
                normalized["rejection_reason"] = ""
                accepted.append(normalized)

        return {
            "raw_count": len(rows),
            "accepted": accepted,
            "rejected": rejected,
            "answer": raw.get("answer"),
        }

    def _normalize_tavily_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": str(item.get("title") or ""),
            "url": str(item.get("url") or item.get("link") or ""),
            "snippet": str(item.get("snippet") or item.get("content") or ""),
        }

    def _build_tavily_evidences(
        self,
        query: str,
        filtered: Dict[str, Any],
        task: OrchestrationTask
    ) -> List[Evidence]:
        evidences = []
        time_range = task.user_intent.time_range if task.user_intent else "实时外部检索"
        rejected_summary = self._rejected_summary(filtered.get("rejected", []))
        for item in filtered.get("accepted", [])[:5]:
            grade = item.get("source_grade") or "B"
            coverage_score = item.get("coverage_score", 0.5)
            credibility = item.get("source_credibility", 0.55)
            limitations = []
            if rejected_summary:
                limitations.append(f"剔除结果: {rejected_summary[:180]}")
            if item.get("source_date") == "unknown":
                limitations.append("未识别到来源日期")
            evidences.append(
                Evidence(
                    source="web-search",
                    tool="tavily-search",
                    claim=f"Tavily 外部补证: {item.get('title') or query[:80]}",
                    content=(
                        f"title={item.get('title')}; url={item.get('url')}; "
                        f"date={item.get('source_date')}; source_grade={grade}; "
                        f"rejection_reason={item.get('rejection_reason', '') or 'accepted'}; "
                        f"snippet={item.get('snippet')[:500]}"
                    ),
                    time_range=f"{time_range}; source_date={item.get('source_date')}",
                    data_caliber="Tavily 外部网页检索口径；按实体匹配和来源等级过滤",
                    source_url=item.get("url", ""),
                    source_date=item.get("source_date", ""),
                    source_credibility=credibility,
                    coverage_dimensions=["外部补证", "URL", "来源日期", "来源等级", "剔除原因"],
                    coverage_score=coverage_score,
                    confidence=round(min(0.85, 0.35 * credibility + 0.45 * coverage_score + 0.20), 3),
                    limitations=limitations,
                )
            )
        return evidences

    def _source_grade(self, url: str, title: str = "") -> str:
        probe = f"{url} {title}".lower()
        high_quality_domains = [
            "caam.org.cn",
            "cpcaauto.com",
            "gov.cn",
            "miit.gov.cn",
            "xinhuanet.com",
            "reuters.com",
            "autohome.com.cn",
            "yiche.com",
            "d1ev.com",
            "gasgoo.com",
            "stcn.com",
            "bydglobal.com",
            "tesla.cn",
            "mi.com",
        ]
        low_quality_domains = [
            "guba.eastmoney.com",
            "xueqiu.com",
            "stock",
            "forecast",
        ]
        if any(domain in probe for domain in high_quality_domains):
            return "A"
        if any(domain in probe for domain in low_quality_domains):
            return "C"
        return "B"

    def _source_credibility_from_grade(self, grade: str) -> float:
        return {"A": 0.85, "B": 0.62, "C": 0.30}.get(grade, 0.50)

    def _infer_source_date(self, *parts: Any) -> str:
        text = " ".join(str(part or "") for part in parts)
        match = re.search(r"20\d{2}(?:[-/.年]\d{1,2}(?:[-/.月]\d{1,2}日?)?)?", text)
        if not match:
            return "unknown"
        return (
            match.group(0)
            .replace("年", "-")
            .replace("月", "-")
            .replace("日", "")
            .replace("/", "-")
            .replace(".", "-")
        )

    def _contains_any(self, text: str, needles: List[str]) -> bool:
        text_lower = (text or "").lower()
        for needle in needles or []:
            if not needle:
                continue
            if needle.isascii():
                if re.search(rf"(?<![A-Za-z0-9]){re.escape(needle.lower())}(?![A-Za-z0-9])", text_lower):
                    return True
            elif needle in text:
                return True
        return False

    def _web_coverage_score(self, item: Dict[str, Any], task: OrchestrationTask, entity_ok: bool) -> float:
        haystack = " ".join([item.get("title", ""), item.get("snippet", ""), item.get("url", "")])
        theme_terms = ["销量", "交付", "市场", "份额", "竞品", "价格", "政策", "战略", "出口", "渠道"]
        theme_hits = sum(1 for term in theme_terms if term in haystack)
        score = 0.25 + min(0.35, theme_hits * 0.07)
        if entity_ok:
            score += 0.20
        if item.get("source_date") and item.get("source_date") != "unknown":
            score += 0.10
        if item.get("source_grade") == "A":
            score += 0.10
        return round(max(0.05, min(1.0, score)), 3)

    def _rejected_summary(self, rejected: List[Dict[str, Any]]) -> str:
        if not rejected:
            return ""
        parts = []
        for item in rejected[:5]:
            label = item.get("title") or item.get("url") or "untitled"
            parts.append(f"{item.get('rejection_reason')}:{label[:60]}")
        return "; ".join(parts)
    
    # ===== 辅助方法 =====
    
    def _identify_opportunities(self, report: Dict) -> List[Dict]:
        """识别机会点"""
        opportunities = []
        # 简化实现，实际应该基于证据分析
        return opportunities
    
    def _identify_risks(self, report: Dict) -> List[Dict]:
        """识别风险"""
        risks = []
        # 检查冲突
        conflicts = self.evidence_ledger.get_conflicts()
        if conflicts:
            risks.append({
                "item": "存在证据冲突",
                "probability": "中",
                "impact": "中",
                "mitigation": "需要交叉验证"
            })
        return risks
    
    def _generate_recommendations(self, report: Dict, opportunities: List[Dict]) -> List[str]:
        """生成建议"""
        recs = []
        if opportunities:
            recs.append("建议深入分析识别的机会点")
        recs.append("建议收集更多结构化数据以提高置信度")
        return recs
    
    def _generate_next_steps(self, task: OrchestrationTask, state: ReactState) -> List[str]:
        """生成下一步"""
        steps = []
        if not state.is_complete:
            steps.append("补充更多证据")
        steps.append("建议进行深度竞品分析")
        steps.append("建议引入政策数据分析")
        return steps
    
    def _build_answer(
        self,
        task: OrchestrationTask,
        report: Dict,
        opportunities: List[Dict],
        risks: List[Dict]
    ) -> str:
        """构建自然语言答案"""
        conf = report.get("summary", {}).get("overall_confidence", 0)
        intent = task.user_intent
        time_range = intent.time_range if intent else "unknown"
        entities = intent.entities if intent else []
        
        answer_parts = []
        
        # 基本信息
        answer_parts.append(f"基于现有证据的分析（置信度: {conf:.0%}）")
        answer_parts.append(f"分析范围: {time_range}")
        if entities:
            answer_parts.append("涉及对象: " + "、".join(entities))
        answer_parts.append("")
        
        # 证据来源
        sources = report.get("by_source", {})
        if sources:
            source_list = [f"{k}: {v}条" for k, v in sources.items() if v > 0]
            if source_list:
                answer_parts.append("数据来源: " + ", ".join(source_list))
                answer_parts.append("")

        confidence_details = report.get("summary", {}).get("confidence_details", {})
        if confidence_details:
            answer_parts.append("置信度计算:")
            answer_parts.append(
                "- 数据覆盖={data:.0%}，RAG覆盖={rag:.0%}，来源可信度={source:.0%}，冲突系数={conflict:.0%}".format(
                    data=confidence_details.get("data_coverage_factor", 0),
                    rag=confidence_details.get("rag_coverage_factor", 0),
                    source=confidence_details.get("source_credibility_factor", 0),
                    conflict=confidence_details.get("conflict_factor", 0),
                )
            )
            answer_parts.append("")

        evidences = report.get("evidences", [])
        fact_evidences = [
            e for e in evidences
            if e.get("source") in ["nl2sql-pg", "rag"]
        ]
        inference_evidences = [
            e for e in evidences
            if e.get("source") not in ["nl2sql-pg", "rag"]
        ]

        if fact_evidences:
            answer_parts.append("事实依据:")
            for evidence in fact_evidences[:4]:
                content = self._summarize_evidence_content(evidence.get("content", ""))
                answer_parts.append(
                    f"- [{evidence.get('source')}] {evidence.get('claim')}: {content}"
                )
                answer_parts.append(
                    f"  口径: {evidence.get('data_caliber', 'unknown')}；时间范围: {evidence.get('time_range', 'unknown')}"
                )
            answer_parts.append("")

        if inference_evidences:
            answer_parts.append("分析判断:")
            for evidence in inference_evidences[:4]:
                answer_parts.append(
                    f"- [{evidence.get('source')}] {evidence.get('claim')} "
                    f"(置信度 {evidence.get('confidence', 0):.0%})"
                )
            answer_parts.append("")

        if evidences:
            answer_parts.append("证据账本:")
            for idx, evidence in enumerate(evidences[:8], 1):
                answer_parts.append(
                    f"- E{idx} | {evidence.get('source')} | {evidence.get('claim')} | "
                    f"置信度 {evidence.get('confidence', 0):.0%} | "
                    f"口径 {evidence.get('data_caliber', 'unknown')} | "
                    f"时间 {evidence.get('time_range', 'unknown')}"
                )
            if len(evidences) > 8:
                answer_parts.append(f"- 另有 {len(evidences) - 8} 条证据见 evidence_ledger 字段")
            answer_parts.append("")
        
        # 机会和风险
        if opportunities:
            answer_parts.append("识别到的机会:")
            for opp in opportunities:
                answer_parts.append(f"- {opp.get('item', 'N/A')}")
            answer_parts.append("")
        
        if risks:
            answer_parts.append("风险提示:")
            for risk in risks:
                answer_parts.append(f"- {risk.get('item', 'N/A')}: {risk.get('mitigation', '')}")
            answer_parts.append("")
        
        return "\n".join(answer_parts)

    def _summarize_evidence_content(self, content: str, max_len: int = 160) -> str:
        """压缩证据内容，避免答案只展示原始长 JSON/表格。"""
        if not content:
            return "无摘要"
        structured_summary = self._summarize_structured_content(content)
        if structured_summary:
            return structured_summary
        compact = " ".join(str(content).split())
        if len(compact) <= max_len:
            return compact
        return compact[:max_len].rstrip() + "..."

    def _summarize_structured_content(self, content: str) -> str:
        """为常见 SQL 结果生成紧凑摘要。"""
        import re

        text = str(content)

        brand_rows = re.findall(
            r"'brand': '([^']+)', 'sales': (\d+), 'model_count': (\d+), 'share': ([\d.]+)",
            text
        )
        if brand_rows:
            items = []
            for brand, sales, model_count, share in brand_rows[:3]:
                items.append(
                    f"{brand}销量{int(sales):,}辆、份额{float(share):.2f}%、车型{model_count}款"
                )
            return "；".join(items)

        total_sales = re.search(r"'total_sales': (\d+)", text)
        avg_monthly = re.search(r"'avg_monthly_sales': Decimal\('([^']+)'\)", text)
        brand_count = re.search(r"'brand_count': (\d+)", text)
        model_count = re.search(r"'model_count': (\d+)", text)
        if total_sales:
            parts = [f"总销量{int(total_sales.group(1)):,}辆"]
            if avg_monthly:
                parts.append(f"月均销量{float(avg_monthly.group(1)):,.0f}辆")
            if brand_count:
                parts.append(f"覆盖品牌{brand_count.group(1)}个")
            if model_count:
                parts.append(f"覆盖车型{model_count.group(1)}个")
            return "，".join(parts)

        return ""
    
    def _generate_markdown_report(
        self,
        task: OrchestrationTask,
        state: ReactState
    ) -> str:
        """生成 Markdown 报告"""
        report = self.evidence_ledger.generate_report()
        
        lines = [
            f"# 市场战略分析报告",
            f"",
            f"**任务ID**: {task.task_id}",
            f"**生成时间**: {datetime.now().isoformat()}",
            f"**置信度**: {report['summary']['overall_confidence']:.0%}",
            f"",
            f"## 分析概要",
            f"",
        ]
        
        # 数据来源
        lines.append("### 数据来源")
        for source, count in report.get("by_source", {}).items():
            if count > 0:
                lines.append(f"- {source}: {count}条证据")
        lines.append("")
        
        # 证据冲突
        conflicts = report.get("conflicts", [])
        if conflicts:
            lines.append("### 证据冲突")
            for c in conflicts:
                lines.append(f"- [{c['severity']}] {c['conflict_type']}: {c['claim_a']} vs {c['claim_b']}")
            lines.append("")
        
        # 下一步
        lines.append("## 下一步建议")
        for step in self._generate_next_steps(task, state):
            lines.append(f"- {step}")
        
        return "\n".join(lines)


def create_orchestrator() -> StrategyOrchestrator:
    """创建编排器实例"""
    return StrategyOrchestrator()


def orchestrate_task(
    query: str,
    time_range: str = "最近12个月",
    entities: List[str] = None,
    target_output: OutputFormat = OutputFormat.NATURAL_LANGUAGE
) -> OrchestrationResult:
    """
    便捷函数：直接编排用户查询
    
    主 Agent 调用此函数
    """
    # 创建任务
    task = create_task_from_user_query(
        query=query,
        target_output=target_output,
        time_range=time_range,
        entities=entities
    )
    
    # 执行编排
    orchestrator = create_orchestrator()
    result = orchestrator.execute(task)
    
    return result
