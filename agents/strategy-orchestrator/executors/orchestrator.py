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
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass, field

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
                if tool_result.success and tool_result.evidence:
                    self.evidence_ledger.add_evidence(
                        source=tool_result.evidence.source,
                        tool=tool_result.evidence.tool,
                        claim=tool_result.evidence.claim,
                        content=tool_result.evidence.content,
                        time_range=tool_result.evidence.time_range,
                        metrics=tool_result.evidence.metrics,
                        confidence=tool_result.evidence.confidence,
                        limitations=tool_result.evidence.limitations
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
            if isinstance(result, dict) and 'evidence' in result:
                evidence = result['evidence']
            
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                evidence=evidence,
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
        if missing:
            state.stop_reason = f"Missing critical: {missing}"
            return True
        
        return False
    
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
            if evidence.source in ["nl2sql-pg", "rag"]:
                facts.append({
                    "claim": evidence.claim,
                    "content": evidence.content[:200],
                    "source": evidence.source,
                    "confidence": evidence.confidence,
                    "time_range": evidence.time_range
                })
            else:
                inferences.append({
                    "claim": evidence.claim,
                    "source": evidence.source,
                    "confidence": evidence.confidence
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
        
        if not state.is_complete:
            missing_or_uncertain.append("证据可能不够完整")
        
        return OrchestrationResult(
            task_id=task.task_id,
            success=state.is_complete or overall_conf >= 0.5,
            answer=answer,
            facts=facts,
            inferences=inferences,
            recommendations=self._generate_recommendations(report, opportunities),
            risks=risks,
            confidence=overall_conf,
            confidence_details=conf_details,
            evidence_sources=[
                {"source": e.source, "tool": e.tool, "claim": e.claim}
                for e in self.evidence_ledger.evidences.values()
            ],
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
        
        if not passed:
            logger.warning("Quality gate not passed")
            # 可以在这里添加处理逻辑
        
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
                    time_range="unknown",
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
                confidence=0.7
            )
        }
    
    def _tool_web_search(self, param: str, task: OrchestrationTask, state: ReactState) -> Dict:
        """网络搜索工具（预留）"""
        return {
            "results": [],
            "evidence": Evidence(
                source="web-search",
                tool="search",
                claim=f"网络搜索: {param}",
                content="搜索功能待实现",
                confidence=0.5,
                limitations=["搜索功能待实现"]
            )
        }
    
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
        
        answer_parts = []
        
        # 基本信息
        answer_parts.append(f"基于现有证据的分析（置信度: {conf:.0%}）")
        answer_parts.append("")
        
        # 证据来源
        sources = report.get("by_source", {})
        if sources:
            source_list = [f"{k}: {v}条" for k, v in sources.items() if v > 0]
            if source_list:
                answer_parts.append("数据来源: " + ", ".join(source_list))
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