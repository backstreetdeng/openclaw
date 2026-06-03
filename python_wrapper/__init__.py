"""
Python Wrapper - 市场分析工作流封装

使用方式:
    from python_wrapper import run_market_analysis

    result = await run_market_analysis("分析比亚迪的市场战略")
"""

from workflow import MarketAnalysisWorkflow, run_market_analysis, WorkflowResult
from stage_connectors import (
    build_stage2_input, build_stage3_input, build_report_input,
    Stage2Input, Stage3Input, ReportInput
)
from skill_caller import SkillCaller, get_caller

__all__ = [
    "MarketAnalysisWorkflow",
    "run_market_analysis",
    "WorkflowResult",
    "build_stage2_input",
    "build_stage3_input",
    "build_report_input",
    "Stage2Input",
    "Stage3Input",
    "ReportInput",
    "SkillCaller",
    "get_caller"
]

__version__ = "1.0.0"
