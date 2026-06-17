"""
Evidence Ledger - 证据账本核心实现

职责：
1. 记录每条证据的来源、内容、置信度
2. 检测证据冲突
3. 计算总体置信度
4. 支持证据查询和回溯
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import json


class EvidenceSource(Enum):
    """证据来源类型"""
    NL2SQL = "nl2sql-pg"           # 结构化数据库
    RAG = "rag"                     # 向量数据库检索
    ANALYSIS_AGENT = "analysis-agent"  # 分析 Agent
    WEB_SEARCH = "web-search"       # 搜索结果
    USER_INPUT = "user-input"       # 用户输入
    LLM_INFERENCE = "llm-inference" # LLM 推断
    EXTERNAL_API = "external-api"   # 外部 API


class EvidenceTag(Enum):
    """证据标签"""
    VERIFIED = "verified"           # 已验证
    CONTRADICTED = "contradicted"   # 冲突
    PENDING = "pending"             # 待验证
    DISPUTED = "disputed"          # 争议中
    DEPRECATED = "deprecated"       # 已废弃


@dataclass
class Evidence:
    """
    单条证据
    
    Attributes:
        evidence_id: 唯一标识
        source: 来源类型
        tool: 具体工具名称
        claim: 这条证据支持什么结论
        content: 原始内容摘要
        time_range: 数据/文档覆盖时间
        metrics: 涉及的指标列表
        confidence: 置信度 0-1
        limitations: 局限性说明
        tags: 标签列表
        created_at: 创建时间
        retrieved_at: 获取时间
    """
    source: str
    tool: str
    claim: str
    content: str
    time_range: str = "unknown"
    metrics: List[str] = field(default_factory=list)
    confidence: float = 0.5
    limitations: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    retrieved_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Evidence':
        return cls(**data)


class EvidenceConflict:
    """证据冲突记录"""
    def __init__(self, evidence_a: Evidence, evidence_b: Evidence, conflict_type: str, severity: str):
        self.evidence_a = evidence_a
        self.evidence_b = evidence_b
        self.conflict_type = conflict_type  # data/time/caliber
        self.severity = severity  # high/medium/low
        self.detected_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_a_id": self.evidence_a.evidence_id,
            "evidence_b_id": self.evidence_b.evidence_id,
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "detected_at": self.detected_at,
            "claim_a": self.evidence_a.claim,
            "claim_b": self.evidence_b.claim
        }


class EvidenceLedger:
    """
    证据账本
    
    核心功能：
    1. 添加证据
    2. 查询证据
    3. 检测冲突
    4. 计算置信度
    5. 生成报告
    """
    
    def __init__(self):
        self.evidences: Dict[str, Evidence] = {}
        self.conflicts: List[EvidenceConflict] = []
        self._claim_index: Dict[str, List[str]] = {}  # claim -> evidence_ids
    
    def add_evidence(
        self,
        source: str,
        tool: str,
        claim: str,
        content: str,
        time_range: str = "unknown",
        metrics: List[str] = None,
        confidence: float = 0.5,
        limitations: List[str] = None,
        tags: List[str] = None
    ) -> Evidence:
        """
        添加一条证据
        
        Returns:
            Evidence: 创建的证据对象
        """
        evidence = Evidence(
            source=source,
            tool=tool,
            claim=claim,
            content=content[:2000] if len(content) > 2000 else content,  # 截断过长内容
            time_range=time_range,
            metrics=metrics or [],
            confidence=confidence,
            limitations=limitations or [],
            tags=tags or ["pending"]
        )
        
        self.evidences[evidence.evidence_id] = evidence
        
        # 更新索引
        claim_key = self._normalize_claim(claim)
        if claim_key not in self._claim_index:
            self._claim_index[claim_key] = []
        self._claim_index[claim_key].append(evidence.evidence_id)
        
        # 检测冲突
        self._check_conflicts(evidence)
        
        return evidence
    
    def _normalize_claim(self, claim: str) -> str:
        """标准化 claim 用于索引"""
        return claim.lower().strip()[:100]
    
    def _check_conflicts(self, new_evidence: Evidence):
        """检测与现有证据的冲突"""
        for existing_id, existing in self.evidences.items():
            if existing_id == new_evidence.evidence_id:
                continue
            
            conflict = self._detect_pair_conflict(new_evidence, existing)
            if conflict:
                self.conflicts.append(conflict)
                # 给冲突证据打标签
                new_evidence.tags.append("contradicted")
                existing.tags = [t if t != "verified" else "disputed" for t in existing.tags]
                if "contradicted" not in existing.tags:
                    existing.tags.append("contradicted")
    
    def _detect_pair_conflict(self, a: Evidence, b: Evidence) -> Optional[EvidenceConflict]:
        """
        检测两条证据之间的冲突
        
        Returns:
            EvidenceConflict 或 None
        """
        # 1. 数据冲突：同一指标数据差异 > 10%
        if self._has_data_conflict(a, b):
            return EvidenceConflict(a, b, "data", "high")
        
        # 2. 时间冲突：时间范围重叠但数据矛盾
        if self._has_time_conflict(a, b):
            return EvidenceConflict(a, b, "time", "medium")
        
        # 3. 口径冲突：指标定义不同
        if self._has_caliber_conflict(a, b):
            return EvidenceConflict(a, b, "caliber", "medium")
        
        return None
    
    def _has_data_conflict(self, a: Evidence, b: Evidence) -> bool:
        """检测数据冲突"""
        # 如果有共同的指标，检查数值差异
        common_metrics = set(a.metrics) & set(b.metrics)
        for metric in common_metrics:
            # 尝试从 content 中提取数值进行比较
            val_a = self._extract_metric_value(a.content, metric)
            val_b = self._extract_metric_value(b.content, metric)
            if val_a and val_b:
                diff = abs(val_a - val_b) / max(val_a, val_b)
                if diff > 0.1:  # 差异 > 10%
                    return True
        return False
    
    def _extract_metric_value(self, content: str, metric: str) -> Optional[float]:
        """从内容中提取指标数值"""
        import re
        # 简单的数值提取逻辑
        patterns = [
            rf"{metric}[：:]\s*(\d+\.?\d*)",
            rf"(\d+\.?\d*)\s*{metric}",
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return None
    
    def _has_time_conflict(self, a: Evidence, b: Evidence) -> bool:
        """检测时间冲突"""
        # 如果 claim 相关但时间范围不同
        if a.time_range != "unknown" and b.time_range != "unknown":
            if a.time_range != b.time_range:
                # 检查内容是否暗示相同时间段
                if self._same_time_period(a.content, b.content):
                    return True
        return False
    
    def _same_time_period(self, content_a: str, content_b: str) -> bool:
        """判断是否来自相同时间段"""
        import re
        # 提取年份/月份
        years_a = set(re.findall(r"20\d{2}", content_a))
        years_b = set(re.findall(r"20\d{2}", content_b))
        return years_a and years_b and years_a == years_b
    
    def _has_caliber_conflict(self, a: Evidence, b: Evidence) -> bool:
        """检测口径冲突"""
        caliber_keywords = ["批发", "零售", "上险", "交付", "订单"]
        content_a_lower = a.content.lower()
        content_b_lower = b.content.lower()
        
        for keyword in caliber_keywords:
            if keyword in content_a_lower and keyword not in content_b_lower:
                return True
            if keyword in content_b_lower and keyword not in content_a_lower:
                return True
        return False
    
    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """根据 ID 获取证据"""
        return self.evidences.get(evidence_id)
    
    def get_evidences_by_claim(self, claim: str) -> List[Evidence]:
        """根据 claim 获取相关证据"""
        claim_key = self._normalize_claim(claim)
        evidence_ids = self._claim_index.get(claim_key, [])
        return [self.evidences[eid] for eid in evidence_ids if eid in self.evidences]
    
    def get_evidences_by_source(self, source: str) -> List[Evidence]:
        """根据来源获取证据"""
        return [e for e in self.evidences.values() if e.source == source]
    
    def get_conflicts(self, severity: str = None) -> List[Dict]:
        """获取冲突列表"""
        if severity:
            return [c.to_dict() for c in self.conflicts if c.severity == severity]
        return [c.to_dict() for c in self.conflicts]
    
    def calculate_overall_confidence(self) -> Tuple[float, Dict[str, Any]]:
        """
        计算总体置信度
        
        Returns:
            (overall_confidence, details)
        """
        if not self.evidences:
            return 0.0, {"error": "No evidences"}
        
        # 按来源分组计算加权平均
        source_weights = {
            EvidenceSource.NL2SQL.value: 0.8,
            EvidenceSource.RAG.value: 0.7,
            EvidenceSource.ANALYSIS_AGENT.value: 0.65,
            EvidenceSource.WEB_SEARCH.value: 0.6,
            EvidenceSource.USER_INPUT.value: 0.5,
            EvidenceSource.LLM_INFERENCE.value: 0.4,
        }
        
        weighted_sum = 0.0
        weight_total = 0.0
        
        for evidence in self.evidences.values():
            weight = source_weights.get(evidence.source, 0.5)
            # 根据 limitations 调整权重
            if evidence.limitations:
                weight *= (1 - 0.1 * len(evidence.limitations))
            
            weighted_sum += evidence.confidence * weight
            weight_total += weight
        
        base_confidence = weighted_sum / weight_total if weight_total > 0 else 0.0
        
        # 冲突系数
        high_conflicts = len([c for c in self.conflicts if c.severity == "high"])
        medium_conflicts = len([c for c in self.conflicts if c.severity == "medium"])
        
        if high_conflicts > 0:
            conflict_factor = 0.5
        elif medium_conflicts > 0:
            conflict_factor = 0.8
        else:
            conflict_factor = 1.0
        
        # 完整性系数（根据是否有结构化+RAG+分析多源）
        sources_present = set(e.source for e in self.evidences.values())
        if EvidenceSource.NL2SQL.value in sources_present and EvidenceSource.RAG.value in sources_present:
            completeness_factor = 1.0
        elif EvidenceSource.NL2SQL.value in sources_present or EvidenceSource.RAG.value in sources_present:
            completeness_factor = 0.85
        else:
            completeness_factor = 0.6
        
        overall = base_confidence * conflict_factor * completeness_factor
        
        details = {
            "base_confidence": round(base_confidence, 3),
            "conflict_factor": conflict_factor,
            "completeness_factor": completeness_factor,
            "high_conflicts": high_conflicts,
            "medium_conflicts": medium_conflicts,
            "sources_count": len(sources_present),
            "total_evidences": len(self.evidences)
        }
        
        return round(overall, 3), details
    
    def generate_report(self) -> Dict[str, Any]:
        """生成证据账本报告"""
        overall_conf, details = self.calculate_overall_confidence()
        
        return {
            "summary": {
                "total_evidences": len(self.evidences),
                "overall_confidence": overall_conf,
                "confidence_details": details,
                "total_conflicts": len(self.conflicts),
                "high_severity_conflicts": len([c for c in self.conflicts if c.severity == "high"])
            },
            "evidences": [e.to_dict() for e in self.evidences.values()],
            "conflicts": self.get_conflicts(),
            "by_source": {
                source: len(self.get_evidences_by_source(source))
                for source in [e.value for e in EvidenceSource]
            },
            "generated_at": datetime.now().isoformat()
        }
    
    def export_json(self) -> str:
        """导出为 JSON 字符串"""
        return json.dumps(self.generate_report(), ensure_ascii=False, indent=2)
    
    def clear(self):
        """清空账本"""
        self.evidences.clear()
        self.conflicts.clear()
        self._claim_index.clear()


# 全局单例
_ledger_instance: Optional[EvidenceLedger] = None


def get_evidence_ledger() -> EvidenceLedger:
    """获取证据账本单例"""
    global _ledger_instance
    if _ledger_instance is None:
        _ledger_instance = EvidenceLedger()
    return _ledger_instance


def reset_evidence_ledger():
    """重置证据账本（用于新任务）"""
    global _ledger_instance
    _ledger_instance = EvidenceLedger()