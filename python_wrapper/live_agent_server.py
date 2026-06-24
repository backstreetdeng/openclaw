# -*- coding: utf-8 -*-
"""Live frontend bridge for the market strategy agent.

Formal architecture:
- Frontend -> this FastAPI bridge
- this bridge -> strategy-orchestrator ReAct loop
- this bridge streams progress and relays the final result

The bridge must not be the market-analysis brain. It must not sequence SQL,
RAG, Tavily, framework, and report tools by itself.
"""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
import sys
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
RAG_ENGINE_ROOT = Path(r"E:\AI\data\envs\car_agent_env\ai-decision\rag-engine")
STRATEGY_ORCHESTRATOR_ROOT = WORKSPACE_ROOT / "agents" / "strategy-orchestrator"
TEMP_ROOT = WORKSPACE_ROOT / "temp"
TEMP_ROOT.mkdir(exist_ok=True)
ANALYSIS_TIMEOUT_SECONDS = 90
RUNTIME_ERROR_LOG = TEMP_ROOT / "live_agent_server_runtime_error.log"

for path in (str(RAG_ENGINE_ROOT), str(STRATEGY_ORCHESTRATOR_ROOT), str(WORKSPACE_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from executors.orchestrator import create_orchestrator  # noqa: E402
from protocols.task_protocol import create_task_from_user_query  # noqa: E402
from quality.quality_gate import get_quality_gate  # noqa: E402


app = FastAPI(title="Market Strategy Agent Live API", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/temp", StaticFiles(directory=TEMP_ROOT), name="temp")


class AnalyzeRequest(BaseModel):
    question: str
    time_range: Optional[str] = None
    analysis_type: Optional[str] = None
    max_cycles: int = 3


class PPTRequest(BaseModel):
    question: str
    report_content: Optional[str] = None
    analysis_data: Optional[Dict[str, Any]] = None


ENTRY_ROUTE_HELP_MARKERS = (
    "你能帮我", "你可以帮我", "可以帮我", "能为我", "能帮我", "帮我什么", "什么帮助",
    "你能做什么", "你可以做什么", "你会做什么", "你有什么能力", "你有什么用",
    "你能干什么", "你能干啥", "可以干什么", "能干什么", "能干啥",
    "有什么功能", "有哪些功能", "功能介绍", "使用说明", "怎么用", "如何使用",
    "这个页面怎么用", "这个智能体怎么用", "你是谁", "干嘛", "介绍一下", "介绍你自己",
    "帮助", "help", "你好", "您好", "hi", "hello", "hey", "在吗",
)

ENTRY_ROUTE_SKILL_MARKERS = (
    "有哪些skill", "有什么skill", "有哪些技能", "有什么技能", "skill列表", "技能列表",
    "可用skill", "可用技能", "安装了哪些skill", "装了哪些skill", "skills",
)

ENTRY_ROUTE_USER_INSIGHT_MARKERS = (
    "用户洞察", "用户画像", "用户分层", "用户需求", "用户偏好", "用户旅程",
    "人群画像", "客群画像", "消费者洞察", "购车人群", "目标用户", "目标客群",
)

ENTRY_ROUTE_ANALYSIS_MARKERS = (
    "分析", "研究", "评估", "预测", "判断", "对比", "比较", "竞品", "竞争", "格局",
    "市场", "销量", "销售", "份额", "市占", "趋势", "政策", "机会", "风险",
    "价格", "价格带", "定位", "配置", "产品", "渠道", "舆情", "口碑",
    "同比", "环比", "增速", "增长", "下滑", "集中度", "出口", "补贴", "购置税",
    "报告", "策略", "战略", "建议", "复盘", "洞察", "结论", "置信度",
)

ENTRY_ROUTE_DOMAIN_MARKERS = (
    "比亚迪", "特斯拉", "吉利", "小米", "长安", "长城", "广汽", "上汽", "理想",
    "蔚来", "小鹏", "问界", "零跑", "极氪", "埃安", "奇瑞", "哪吒",
    "新能源", "乘用车", "燃油车", "混动", "插混", "纯电", "增程", "suv", "mpv",
    "轿车", "车型", "品牌", "车企", "汽车", "车市", "15-20万", "20万",
)

DIRECT_ROUTES = {"capability_help", "skill_inventory", "general_chat", "user_insight"}
ALLOWED_LLM_PLAN_PREFIXES = {
    "targeted-sql-pack",
    "nl2sql-pg",
    "rag",
    "pg-vector-search",
    "web-search",
    "analysis-framework",
    "competitor-analyst",
    "cost-analyst",
    "report-generator",
    "report-generator-agent",
    "phase-tracker",
}


def _classify_entry_route(question: str) -> Dict[str, Any]:
    """Classify the frontend entry route before any tool orchestration."""
    normalized = re.sub(r"\s+", "", (question or "").strip().lower())
    if not normalized:
        return {
            "route": "general_chat",
            "confidence": 1.0,
            "reason": "empty_question",
            "help_hits": [],
            "skill_hits": [],
            "user_insight_hits": [],
            "analysis_hits": [],
            "domain_hits": [],
        }

    analysis_hits = [marker for marker in ENTRY_ROUTE_ANALYSIS_MARKERS if marker.lower() in normalized]
    domain_hits = [marker for marker in ENTRY_ROUTE_DOMAIN_MARKERS if marker.lower() in normalized]
    help_hits = [marker for marker in ENTRY_ROUTE_HELP_MARKERS if marker.lower() in normalized]
    skill_hits = [marker for marker in ENTRY_ROUTE_SKILL_MARKERS if marker.lower() in normalized]
    user_insight_hits = [marker for marker in ENTRY_ROUTE_USER_INSIGHT_MARKERS if marker.lower() in normalized]

    if skill_hits:
        return {
            "route": "skill_inventory",
            "confidence": min(0.98, 0.8 + 0.04 * len(skill_hits)),
            "reason": "skill_inventory_signal",
            "help_hits": help_hits,
            "skill_hits": skill_hits,
            "user_insight_hits": user_insight_hits,
            "analysis_hits": analysis_hits,
            "domain_hits": domain_hits,
        }

    if user_insight_hits and not domain_hits:
        return {
            "route": "user_insight",
            "confidence": min(0.96, 0.78 + 0.04 * len(user_insight_hits)),
            "reason": "user_insight_signal",
            "help_hits": help_hits,
            "skill_hits": skill_hits,
            "user_insight_hits": user_insight_hits,
            "analysis_hits": analysis_hits,
            "domain_hits": domain_hits,
        }

    # Analysis/domain evidence wins over help phrasing. Example:
    # "你能帮我分析比亚迪最近12个月市场策略吗" must run the orchestrator.
    if analysis_hits or domain_hits:
        return {
            "route": "market_analysis",
            "confidence": min(0.98, 0.72 + 0.05 * (len(analysis_hits) + len(domain_hits))),
            "reason": "market_analysis_signal",
            "help_hits": help_hits,
            "skill_hits": skill_hits,
            "user_insight_hits": user_insight_hits,
            "analysis_hits": analysis_hits,
            "domain_hits": domain_hits,
        }

    if help_hits:
        return {
            "route": "capability_help",
            "confidence": min(0.98, 0.74 + 0.04 * len(help_hits)),
            "reason": "help_or_capability_signal",
            "help_hits": help_hits,
            "skill_hits": skill_hits,
            "user_insight_hits": user_insight_hits,
            "analysis_hits": analysis_hits,
            "domain_hits": domain_hits,
        }

    if len(normalized) <= 8:
        return {
            "route": "general_chat",
            "confidence": 0.62,
            "reason": "short_non_market_query",
            "help_hits": help_hits,
            "skill_hits": skill_hits,
            "user_insight_hits": user_insight_hits,
            "analysis_hits": analysis_hits,
            "domain_hits": domain_hits,
        }

    return {
        "route": "general_chat",
        "confidence": 0.55,
        "reason": "no_market_analysis_signal",
        "help_hits": help_hits,
        "skill_hits": skill_hits,
        "user_insight_hits": user_insight_hits,
        "analysis_hits": analysis_hits,
        "domain_hits": domain_hits,
    }


def _is_direct_response_query(question: str) -> bool:
    """Return True for questions that should be answered without orchestration."""
    return _classify_entry_route(question)["route"] in DIRECT_ROUTES


def _installed_skill_inventory() -> List[Dict[str, str]]:
    """Read the workspace skill inventory from local skill folders."""
    skills_dir = WORKSPACE_ROOT / "skills"
    items: List[Dict[str, str]] = []
    if not skills_dir.exists():
        return items

    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        description = ""
        if skill_md.exists():
            try:
                for line in skill_md.read_text(encoding="utf-8", errors="ignore").splitlines():
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or stripped in {"---"}:
                        continue
                    if stripped.lower().startswith("description:"):
                        description = stripped.split(":", 1)[1].strip().strip('"')
                        break
                    description = stripped[:120]
                    break
            except Exception:
                description = ""
        items.append(
            {
                "name": skill_dir.name,
                "description": description or "本地 skill，详情见 SKILL.md",
                "path": str(skill_md if skill_md.exists() else skill_dir),
            }
        )
    return items


def _call_openai_compatible_chat(messages: Sequence[Dict[str, str]], *, max_tokens: int = 700) -> Dict[str, Any]:
    """Small OpenAI-compatible chat client used only when explicitly configured."""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("MARKET_LLM_API_KEY")
    if not api_key:
        return {"ok": False, "error": "missing OPENAI_API_KEY or MARKET_LLM_API_KEY"}

    base_url = (os.environ.get("OPENAI_BASE_URL") or os.environ.get("MARKET_LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("MARKET_LLM_MODEL") or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
    payload = {
        "model": model,
        "messages": list(messages),
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    timeout = float(os.environ.get("MARKET_LLM_TIMEOUT", "12"))
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        return {"ok": bool(text), "text": text, "model": model, "base_url": base_url}
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        return {"ok": False, "error": str(exc), "model": model, "base_url": base_url}


def _extract_json_object(text: str) -> Dict[str, Any]:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else {}
    except ValueError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return {}
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else {}
        except ValueError:
            return {}


def _validate_llm_plan_steps(steps: Sequence[Any]) -> List[str]:
    valid: List[str] = []
    for raw_step in steps:
        step = str(raw_step or "").strip()
        if not step or ":" not in step:
            continue
        prefix, param = step.split(":", 1)
        prefix = prefix.strip()
        param = param.strip()
        if prefix not in ALLOWED_LLM_PLAN_PREFIXES or not param:
            continue
        normalized = f"{prefix}:{param}"
        if normalized not in valid:
            valid.append(normalized)

    prefixes = {step.split(":", 1)[0] for step in valid}
    if valid and "analysis-framework" not in prefixes:
        valid.append("analysis-framework:automotive_strategy_seven_stage")
    if valid and "report-generator-agent" not in prefixes:
        valid.append("report-generator-agent:quality_review")
    return valid[:8]


def _llm_plan_provider(context: Dict[str, Any]) -> List[str]:
    """Bounded LLM planner for strategy-orchestrator.

    It returns only validated tool steps. If no LLM is configured or parsing
    fails, the orchestrator falls back to the Skill-guided planner.
    """
    if str(os.environ.get("MARKET_LLM_PLANNER", "1")).lower() in {"0", "false", "no", "off"}:
        return []

    allowed = ", ".join(sorted(ALLOWED_LLM_PLAN_PREFIXES))
    messages = [
        {
            "role": "system",
            "content": (
                "你是汽车市场 strategy-orchestrator 的 LLM planner。"
                "只输出 JSON，不要输出解释。JSON schema: "
                '{"steps":["tool:param"],"reason":"...","confidence":0.0}. '
                f"允许的 tool 前缀只有：{allowed}。"
                "必须根据问题和已完成步骤选择下一轮 ReAct 工具；不要编造不存在的工具。"
                "复杂汽车市场问题通常至少需要结构化数据、RAG/外部验证、automotive_strategy_seven_stage 框架和质量复核。"
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "raw_query": context.get("raw_query"),
                    "task_type": context.get("task_type"),
                    "time_range": context.get("time_range"),
                    "entities": context.get("entities"),
                    "analysis_plan": context.get("analysis_plan"),
                    "completed_steps": context.get("completed_steps"),
                    "evidence_gaps": context.get("evidence_gaps"),
                    "stage_contract": [
                        "problem_definition",
                        "path_design",
                        "data_collection",
                        "data_validation",
                        "framework_analysis",
                        "insight_synthesis",
                        "quality_review",
                    ],
                },
                ensure_ascii=False,
            ),
        },
    ]
    response = _call_openai_compatible_chat(messages, max_tokens=500)
    if not response.get("ok"):
        return []
    payload = _extract_json_object(str(response.get("text") or ""))
    return _validate_llm_plan_steps(payload.get("steps") or [])


def _direct_llm_answer(question: str) -> Dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": (
                "你是汽车市场战略分析师的前端对话入口。当前问题没有明确市场分析信号，"
                "请直接回答用户问题。不要调用或声称调用 SQL、RAG、Web 或 strategy-orchestrator。"
            ),
        },
        {"role": "user", "content": question},
    ]
    return _call_openai_compatible_chat(messages, max_tokens=500)


def _direct_response_report(question: str, route_decision: Dict[str, Any]) -> str:
    route = route_decision.get("route")
    if route == "skill_inventory":
        skills = _installed_skill_inventory()
        lines = ["## 当前可用 Skills", ""]
        if not skills:
            lines.append("当前工作空间没有发现 `skills/` 下的本地 skill。")
        else:
            for item in skills:
                lines.append(f"- `{item['name']}`：{item['description']}")
        lines += [
            "",
            "说明：市场战略分析问题会进入 `strategy-orchestrator`，再由它按证据需求调用 SQL、RAG、Web 和专业分析 Skill。",
        ]
        return "\n".join(lines)

    if route == "user_insight":
        return "\n".join(
            [
                "## 用户洞察路由",
                "",
                "这个问题已识别为用户洞察类，不会误进入市场战略分析链路。",
                "",
                "当前工作空间还没有独立的 `user-insight` 专用 skill 或 agent 接入前端，所以本次不会调用 SQL、RAG、Web 或 `automotive-strategy-analysis`。",
                "下一步应接入独立的用户洞察能力，用于处理用户画像、用户分层、偏好、旅程和需求洞察。",
            ]
        )

    if route == "general_chat":
        llm_result = _direct_llm_answer(question)
        if llm_result.get("ok"):
            return str(llm_result["text"]).strip()
        return "\n".join(
            [
                "## 直接对话",
                "",
                "这不是市场分析问题，所以我没有启动 strategy-orchestrator、SQL、RAG 或 Web 检索。",
                "",
                "当前未配置可用的 direct LLM API，因此只能用本地兜底回复：你可以继续直接问我问题；如果是市场战略、竞品、价格带、销量、政策或机会判断，我会进入市场分析链路。",
                "",
                f"LLM 状态：{llm_result.get('error')}",
            ]
        )

    return "\n".join(
        [
            "## 我能做什么",
            "",
            "我是汽车市场战略分析智能体，适合处理需要证据链和结构化判断的市场问题。",
            "",
            "入口路由会先判断问题类型：",
            "- 市场战略、竞品、价格带、销量、政策、机会等问题进入 `strategy-orchestrator`。",
            "- “你有哪些 skill”进入 `skill_inventory`，返回实际 skill 清单。",
            "- 普通对话进入 direct LLM，不调用市场分析工具。",
            "- 用户画像、用户分层、用户需求等进入独立 `user_insight` 路由。",
            "",
            "你可以这样问：",
            "- `分析 2026 年中国新能源乘用车市场竞争格局`",
            "- `对比比亚迪、特斯拉、吉利最近12个月的市场表现`",
            "- `评估15-20万新能源SUV市场机会`",
        ]
    )


def _direct_response_payload(question: str, route_decision: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    route_decision = route_decision or _classify_entry_route(question)
    report = _direct_response_report(question, route_decision)
    return {
        "success": True,
        "question": question,
        "analysis_type": str(route_decision.get("route") or "direct_response"),
        "time_range": "",
        "entities": [],
        "confidence": 1.0,
        "cycles_used": 0,
        "stop_reason": f"{route_decision.get('route')}_no_market_orchestration",
        "sources": [],
        "evidence_count": 0,
        "facts_count": 0,
        "inferences_count": 0,
        "quality_passed": True,
        "failed_quality_checks": [],
        "missing_or_uncertain": [],
        "errors": [],
        "raw": {},
        "execution_trace": [
            {
                "agent": "market_strategy_agent",
                "skill": "entry-route-classifier",
                "action": "classify_and_answer_without_orchestration",
                "status": "done",
                "summary": f"入口路由判断为 {route_decision['route']}，原因：{route_decision['reason']}。未启动市场分析编排、SQL、RAG 或 Web 检索。",
                "detail": route_decision,
            }
        ],
        "skill_trace": [],
        "react_trace": [],
        "execution_time": 0.0,
        "report": report,
    }


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "to_dict"):
        return _jsonable(value.to_dict())
    return str(value)


def _sse(event: str, data: Dict[str, Any]) -> str:
    payload = json.dumps(_jsonable(data), ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _log_runtime_exception(context: str, exc: BaseException) -> str:
    trace = traceback.format_exc()
    message = (
        f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] {context}\n"
        f"{type(exc).__name__}: {exc}\n{trace}\n"
    )
    try:
        RUNTIME_ERROR_LOG.write_text(
            (RUNTIME_ERROR_LOG.read_text(encoding="utf-8", errors="ignore") if RUNTIME_ERROR_LOG.exists() else "")
            + message,
            encoding="utf-8",
        )
    except Exception:
        pass
    return trace


def _infer_analysis_type(question: str) -> str:
    q = question.lower()
    if any(k in question for k in ("政策", "法规", "补贴", "出口", "泰国", "欧盟", "印尼", "沙特")):
        return "policy"
    if any(k in question for k in ("竞品", "竞争", "对比", "品牌", "比亚迪", "特斯拉", "吉利", "小米")):
        return "competitor"
    if any(k in question for k in ("机会", "空间", "增长", "细分", "SUV", "suv", "价格带", "进入")):
        return "opportunity"
    if any(k in question for k in ("趋势", "宏观", "市场", "销量")) or "trend" in q:
        return "market"
    return "comprehensive"


def _infer_entities(question: str) -> List[str]:
    candidates = [
        "比亚迪", "特斯拉", "吉利", "长安", "长城", "广汽", "上汽", "小米",
        "问界", "理想", "蔚来", "小鹏", "零跑", "埃安", "极氪",
        "泰国", "印尼", "欧盟", "沙特", "新能源SUV", "15-20万",
    ]
    return [item for item in candidates if item in question]


def _normalize_time_range(question: str, requested: Optional[str]) -> str:
    year_match = re.search(r"(20\d{2})\s*年", question or "")
    if year_match:
        return f"{year_match.group(1)}年"

    source = f"{question or ''} {requested or ''}"
    if any(k in source for k in ("近半年", "最近半年", "6个月", "六个月")):
        return "最近6个月"
    if any(k in source for k in ("近三个月", "最近3个月", "3个月", "三个月")):
        return "最近3个月"
    if any(k in source for k in ("最近12个月", "近12个月", "12个月", "一年")):
        return "最近12个月"
    return requested or "最近6个月"


def _react_trace(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = result.get("raw") if "raw" in result else result
    raw = raw or {}
    trace: List[Dict[str, Any]] = []

    plan = raw.get("analysis_plan") or {}
    if plan:
        trace.append(
            {
                "phase": "Plan",
                "stage": "stage2",
                "status": "done",
                "summary": (
                    f"统一分析计划：市场={plan.get('market_scope') or '未指定'}；"
                    f"时间={plan.get('time_range') or '未指定'}；"
                    f"品牌={plan.get('target_brand') or '未指定'}；"
                    f"价格带={plan.get('price_band') or '未指定'}"
                ),
                "detail": plan,
            }
        )

    evidence_sources = raw.get("evidence_sources") or []
    for idx, item in enumerate(evidence_sources, 1):
        if not isinstance(item, dict):
            continue
        trace.append(
            {
                "phase": "Act",
                "stage": "stage3",
                "status": "done",
                "summary": (
                    f"{idx}. {item.get('source') or 'evidence'} / {item.get('tool') or 'tool'}："
                    f"{item.get('claim') or '证据入账'}"
                ),
                "detail": {
                    "source": item.get("source"),
                    "tool": item.get("tool"),
                    "confidence": item.get("confidence"),
                    "time_range": item.get("time_range"),
                    "data_caliber": item.get("data_caliber"),
                    "source_grade": item.get("source_grade"),
                },
            }
        )

    reflection = raw.get("reflection") or {}
    if reflection:
        trace.append(
            {
                "phase": "Reflect",
                "stage": "stage4",
                "status": "done",
                "summary": (
                    f"置信度={float(reflection.get('overall_confidence') or 0):.1%}；"
                    f"缺口={len(reflection.get('evidence_gaps') or [])}；"
                    f"冲突={len(reflection.get('conflicts') or [])}；"
                    f"停滞={reflection.get('stagnation_count') or 0}轮"
                ),
                "detail": reflection,
            }
        )

    for idx, item in enumerate(raw.get("replan_history") or [], 1):
        trace.append(
            {
                "phase": "Re-plan",
                "stage": "stage4",
                "status": "done",
                "summary": f"{idx}. {item.get('reason') or 'replan'} → {', '.join(item.get('next_plan') or [])}",
                "detail": item,
            }
        )

    quality = result.get("failed_quality_checks") or raw.get("failed_quality_checks") or []
    trace.append(
        {
            "phase": "Quality",
            "stage": "stage4",
            "status": "done" if result.get("quality_passed") else "warning",
            "summary": (
                "质量门禁通过"
                if result.get("quality_passed")
                else f"质量门禁未通过：{len(quality)}项未满足"
            ),
            "detail": quality,
        }
    )

    return trace


def _source_names(result: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for source in result.get("evidence_sources", []) or []:
        if isinstance(source, dict):
            name = source.get("source") or source.get("tool") or source.get("name")
            if name:
                names.append(str(name))
    return sorted(set(names))


def _quality_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    qg = get_quality_gate()
    passed, checks = qg.run_all(result)
    failed = [
        {
            "check": item.check_name,
            "level": getattr(item.level, "value", str(item.level)),
            "message": item.message,
            "suggestions": item.suggestions,
        }
        for item in checks
        if not item.passed
    ]
    return {"quality_passed": passed, "failed_quality_checks": failed}


def _orchestrator_trace(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    traces = [
        {
            "agent": "market_strategy_agent",
            "skill": "strategy-orchestrator",
            "action": "orchestrate",
            "status": "done" if result.get("success") else "failed",
            "summary": (
                "已调用 strategy-orchestrator ReAct 主循环；"
                f"cycles={result.get('cycles_used', 0)}；stop_reason={result.get('stop_reason') or 'unknown'}"
            ),
        }
    ]
    for source in result.get("evidence_sources", []) or []:
        if not isinstance(source, dict):
            continue
        traces.append(
            {
                "agent": "strategy-orchestrator",
                "skill": source.get("source") or source.get("tool") or "evidence",
                "action": source.get("tool") or "observe",
                "status": "done",
                "summary": source.get("claim") or "证据已进入 orchestrator evidence ledger",
            }
        )
    return traces


def _format_report(question: str, result: Dict[str, Any], quality_passed: bool) -> str:
    if result.get("seven_step_report"):
        return str(result.get("seven_step_report"))

    facts = result.get("facts", []) or []
    inferences = result.get("inferences", []) or []
    uncertainty = result.get("missing_or_uncertain", []) or []
    sources = _source_names(result)
    answer = result.get("answer") or ""

    lines = [
        "# strategy-orchestrator ReAct 分析结果",
        "",
        f"**问题**：{question}",
        f"**执行状态**：{'成功' if result.get('success') else '失败'}",
        f"**质量门禁**：{'通过' if quality_passed else '未通过'}",
        f"**置信度**：{float(result.get('confidence') or 0):.1%}",
        f"**ReAct 循环轮次**：{result.get('cycles_used', 0)}",
        f"**停止原因**：{result.get('stop_reason') or '未知'}",
        f"**证据来源**：{', '.join(sources) if sources else '无'}",
        "",
        "## 事实依据",
    ]

    if facts:
        for item in facts[:8]:
            source = item.get("source") or item.get("tool") or "evidence"
            claim = item.get("claim") or item.get("content") or str(item)
            content = item.get("content")
            suffix = f"：{content}" if content and content != claim else ""
            lines.append(f"- [{source}] {claim}{suffix}")
    else:
        lines.append("- 暂无结构化事实。")

    lines += ["", "## 分析判断"]
    if inferences:
        for item in inferences[:8]:
            source = item.get("source") or item.get("tool") or "analysis"
            claim = item.get("claim") or item.get("content") or str(item)
            confidence = item.get("confidence")
            suffix = f"（置信度 {float(confidence):.0%}）" if isinstance(confidence, (int, float)) else ""
            lines.append(f"- [{source}] {claim}{suffix}")
    else:
        lines.append("- 暂无额外推断。")

    recommendations = result.get("recommendations") or []
    if recommendations:
        lines += ["", "## 建议动作"]
        for item in recommendations[:8]:
            lines.append(f"- {item}")

    risks = result.get("risks") or []
    if risks:
        lines += ["", "## 风险提示"]
        for item in risks[:8]:
            if isinstance(item, dict):
                lines.append(f"- {item.get('item', '')}: {item.get('mitigation', '')}")
            else:
                lines.append(f"- {item}")

    if uncertainty:
        lines += ["", "## 不确定性与缺口"]
        for item in uncertainty[:8]:
            lines.append(f"- {item}")

    if answer:
        lines += ["", "## Orchestrator 原始回答", "", str(answer)]

    next_steps = result.get("next_steps") or []
    if next_steps:
        lines += ["", "## 下一步"]
        for item in next_steps[:8]:
            lines.append(f"- {item}")

    return "\n".join(lines)


def _run_orchestrated_analysis(
    query: str,
    time_range: str,
    entities: List[str],
    analysis_type: str,
    max_cycles: int,
    event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Run strategy-orchestrator, optionally streaming its live ReAct events."""
    task = create_task_from_user_query(
        query=query,
        time_range=time_range,
        entities=entities,
    )
    task.max_react_cycles = max_cycles
    orchestrator = create_orchestrator(
        event_callback=event_callback,
        llm_plan_provider=_llm_plan_provider,
    )
    result = orchestrator.execute(task)
    return {
        "success": result.success,
        "user_intent": result.user_intent,
        "analysis_plan": result.analysis_plan,
        "answer": result.answer,
        "facts": result.facts,
        "inferences": result.inferences,
        "confidence": result.confidence,
        "confidence_details": result.confidence_details,
        "evidence_sources": result.evidence_sources,
        "evidence_ledger": result.evidence_ledger,
        "evidence_store": result.evidence_store,
        "seven_step_report": result.seven_step_report,
        "insight_cards": result.insight_cards,
        "reflection": result.reflection,
        "replan_history": result.replan_history,
        "quality_passed": result.quality_passed,
        "quality_summary": result.quality_summary,
        "failed_quality_checks": result.failed_quality_checks,
        "recommendations": result.recommendations,
        "risks": result.risks,
        "missing_or_uncertain": result.missing_or_uncertain,
        "next_steps": result.next_steps,
        "errors": result.errors,
        "stop_reason": result.stop_reason,
        "cycles_used": result.cycles_used,
    }


def _run_analysis(
    request: AnalyzeRequest,
    event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    question = request.question.strip()
    started = time.time()
    route_decision = _classify_entry_route(question)
    if route_decision["route"] in DIRECT_ROUTES:
        payload = _direct_response_payload(question, route_decision)
        payload["execution_time"] = round(time.time() - started, 2)
        if event_callback:
            event_callback(
                {
                    "phase": "Direct",
                    "stage": "stage1",
                    "status": "done",
                    "summary": f"入口路由判断为 {route_decision['route']}：{route_decision['reason']}。不启动市场分析编排。",
                    "detail": route_decision,
                }
            )
        return payload

    analysis_type = request.analysis_type or _infer_analysis_type(question)
    time_range = _normalize_time_range(question, request.time_range)
    entities = _infer_entities(question)

    result = _run_orchestrated_analysis(
        query=question,
        time_range=time_range,
        entities=entities,
        analysis_type=analysis_type,
        max_cycles=request.max_cycles,
        event_callback=event_callback,
    )
    result = _jsonable(result)
    quality = _quality_summary(result)
    traces = _orchestrator_trace(result)
    wrapped = {
        "success": bool(result.get("success")),
        "question": question,
        "analysis_type": analysis_type,
        "time_range": time_range,
        "entities": entities,
        "confidence": result.get("confidence", 0),
        "cycles_used": result.get("cycles_used", 0),
        "stop_reason": result.get("stop_reason"),
        "sources": _source_names(result),
        "evidence_count": len(result.get("evidence_sources", []) or []),
        "facts_count": len(result.get("facts", []) or []),
        "inferences_count": len(result.get("inferences", []) or []),
        "quality_passed": quality["quality_passed"],
        "failed_quality_checks": quality["failed_quality_checks"],
        "missing_or_uncertain": result.get("missing_or_uncertain", []) or [],
        "errors": result.get("errors", []) or [],
        "raw": result,
        "execution_trace": traces,
        "skill_trace": traces,
        "execution_time": round(time.time() - started, 2),
    }
    wrapped["react_trace"] = _react_trace(wrapped)
    wrapped["report"] = _format_report(question, result, quality["quality_passed"])

    return wrapped


def _db_snapshot() -> Dict[str, Any]:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        from retrieval.vector_store import DB_CONFIG

        conn = psycopg2.connect(**DB_CONFIG, connect_timeout=3, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM documents")
        documents = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM chunks")
        chunks = cur.fetchone()["cnt"]
        cur.close()
        conn.close()
        return {"connected": True, "documents": documents, "chunks": chunks}
    except Exception as exc:
        return {"connected": False, "error": str(exc), "documents": 0, "chunks": 0}


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "name": "Market Strategy Agent Live API",
        "status": "ok",
        "mode": "sse_relay_to_strategy_orchestrator",
        "frontend": "/frontend_demo.html",
        "endpoints": ["/health", "/analyze", "/analyze_sse", "/generate_ppt"],
    }


@app.get("/frontend_demo.html")
async def frontend() -> FileResponse:
    html_path = WORKSPACE_ROOT / "frontend_demo.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="frontend_demo.html not found")
    return FileResponse(html_path, media_type="text/html; charset=utf-8")


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "timestamp": time.time(),
        "mode": "sse_relay_to_strategy_orchestrator",
        "db": _db_snapshot(),
    }


@app.post("/analyze")
async def analyze(request: AnalyzeRequest) -> Dict[str, Any]:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty")
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_run_analysis, request),
            timeout=ANALYSIS_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        _log_runtime_exception("POST /analyze timeout", exc)
        raise HTTPException(
            status_code=504,
            detail=f"analysis timed out after {ANALYSIS_TIMEOUT_SECONDS}s",
        )
    except Exception as exc:
        _log_runtime_exception("POST /analyze failed", exc)
        raise


@app.post("/analyze_sse")
async def analyze_sse(request: AnalyzeRequest) -> StreamingResponse:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty")

    async def stream() -> Iterable[str]:
        question = request.question.strip()
        route_decision = _classify_entry_route(question)
        if route_decision["route"] in DIRECT_ROUTES:
            result = _direct_response_payload(question, route_decision)
            yield _sse(
                "react",
                {
                    "phase": "Direct",
                    "stage": "stage1",
                    "status": "done",
                    "summary": f"入口路由判断为 {route_decision['route']}：{route_decision['reason']}。未启动 SQL/RAG/ReAct 市场分析。",
                    "detail": route_decision,
                },
            )
            yield _sse("complete", result)
            return

        analysis_type = request.analysis_type or _infer_analysis_type(question)
        time_range = _normalize_time_range(question, request.time_range)
        entities = _infer_entities(question)
        start = time.time()

        yield _sse(
            "react",
            {
                "phase": "Route",
                "stage": "stage0",
                "status": "done",
                "summary": f"入口路由判断为市场分析：{route_decision['reason']}。进入 strategy-orchestrator。",
                "detail": route_decision,
            },
        )
        yield _sse(
            "progress",
            {
                "stage": "stage1",
                "stage_name": "接收任务",
                "status": "done",
                "summary": f"桥接层接收问题；analysis_type={analysis_type}；time_range={time_range}；entities={entities}",
            },
        )
        yield _sse(
            "progress",
            {
                "stage": "stage2",
                "stage_name": "转交编排器",
                "status": "running",
                "summary": "正在调用 strategy-orchestrator ReAct 主循环；桥接层不再自行顺序调 SQL/RAG/Tavily。",
            },
        )

        event_queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        live_event_count = 0

        def emit_live_event(event: Dict[str, Any]) -> None:
            loop.call_soon_threadsafe(event_queue.put_nowait, event)

        task = asyncio.create_task(
            asyncio.to_thread(_run_analysis, request, event_callback=emit_live_event)
        )
        beat = 0
        while not task.done():
            elapsed = time.time() - start
            if elapsed > ANALYSIS_TIMEOUT_SECONDS:
                task.cancel()
                yield _sse(
                    "error",
                    {
                        "success": False,
                        "error_type": "TimeoutError",
                        "error": f"analysis timed out after {ANALYSIS_TIMEOUT_SECONDS}s",
                        "execution_time": round(elapsed, 2),
                    },
                )
                return
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=2)
                live_event_count += 1
                yield _sse("react", event)
            except asyncio.TimeoutError:
                beat += 1
                yield _sse(
                    "progress",
                    {
                        "stage": "stage3",
                        "stage_name": "ReAct 编排中",
                        "status": "running",
                        "summary": (
                            "等待当前工具返回；"
                            f"已用 {round(time.time() - start, 1)}s，"
                            f"已收到 {live_event_count} 条实时执行事件。"
                        ),
                        "heartbeat": beat,
                    },
                )

        try:
            while not event_queue.empty():
                live_event_count += 1
                yield _sse("react", event_queue.get_nowait())
            result = await task
            if live_event_count == 0:
                for item in result.get("react_trace") or []:
                    yield _sse("react", item)
            yield _sse(
                "progress",
                {
                    "stage": "stage4",
                    "stage_name": "结果回传",
                    "status": "done",
                    "summary": (
                        f"orchestrator 完成；cycles={result.get('cycles_used')}；"
                        f"confidence={float(result.get('confidence') or 0):.1%}；"
                        f"quality_passed={result.get('quality_passed')}"
                    ),
                },
            )
            yield _sse("complete", result)
        except Exception as exc:
            trace = _log_runtime_exception("POST /analyze_sse failed", exc)
            yield _sse(
                "error",
                {
                    "success": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "traceback_tail": trace[-1200:],
                    "execution_time": round(time.time() - start, 2),
                },
            )

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.post("/generate_ppt")
async def generate_ppt(request: PPTRequest) -> Dict[str, Any]:
    """Render a lightweight HTML deck from orchestrator output.

    This is presentation rendering only; it does not perform market analysis.
    """
    try:
        output_path = TEMP_ROOT / f"presentation_{int(time.time())}.html"
        content = request.report_content or (request.analysis_data or {}).get("report") or ""
        title = request.question or "市场战略分析"
        html_text = _presentation_html(title, content, request.analysis_data or {})
        output_path.write_text(html_text, encoding="utf-8")
        return {"success": True, "ppt_path": str(output_path), "ppt_url": "/temp/" + output_path.name, "message": "PPT生成成功"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _presentation_html(title: str, report_content: str, analysis_data: Dict[str, Any]) -> str:
    confidence = analysis_data.get("confidence", "-")
    cycles = analysis_data.get("cycles_used", "-")
    sources = ", ".join(analysis_data.get("sources") or []) or "无"
    safe_title = html.escape(title)
    safe_report = html.escape(report_content[:1800] or "暂无报告内容")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    body {{ margin:0; font-family: Arial, "Microsoft YaHei", sans-serif; background:#101418; color:#f7f8fa; }}
    section {{ min-height:100vh; padding:64px 8vw; box-sizing:border-box; display:flex; flex-direction:column; justify-content:center; }}
    h1 {{ font-size:48px; margin:0 0 24px; }}
    h2 {{ font-size:34px; margin:0 0 20px; }}
    p, pre {{ font-size:20px; line-height:1.65; color:#d7dce2; white-space:pre-wrap; }}
    .metric {{ display:inline-block; margin:8px 16px 8px 0; padding:12px 16px; border:1px solid #3b4652; border-radius:8px; }}
  </style>
</head>
<body>
  <section><h1>{safe_title}</h1><p>strategy-orchestrator ReAct 分析结果</p></section>
  <section><h2>证据与质量</h2><p><span class="metric">置信度：{confidence}</span><span class="metric">循环：{cycles}</span><span class="metric">来源：{html.escape(sources)}</span></p></section>
  <section><h2>报告摘要</h2><pre>{safe_report}</pre></section>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("live_agent_server:app", host="0.0.0.0", port=8003, reload=False)
