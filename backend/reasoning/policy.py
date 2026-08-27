import logging
from typing import List

from .schemas import (
    ReasoningState, ResponsePolicy, SafetyState, UncertaintyLevel, QueryCategory
)

logger = logging.getLogger("foraa.reasoning.policy")

class PolicyEngine:
    def __init__(self):
        pass

    def evaluate(self, state: ReasoningState) -> ResponsePolicy:
        """
        Determines the output path for the response generation based on the reasoning state.
        """
        if state.safety_state in [SafetyState.EMERGENCY, SafetyState.NEEDS_ESCALATION]:
            return ResponsePolicy.SAFETY_ESCALATION

        if state.missing_information and state.missing_information.status == "required":
            return ResponsePolicy.ASK_CLARIFICATION

        high_severity_contradictions = [c for c in state.contradictions if c.severity == "HIGH" and c.resolution_required]
        if high_severity_contradictions:
            return ResponsePolicy.ASK_CLARIFICATION

        if state.uncertainty == UncertaintyLevel.HIGH:
            return ResponsePolicy.INSUFFICIENT_INFORMATION

        if state.intent:
            if QueryCategory.MEDICAL_REPORT in state.intent.categories or state.intent.needs_reports:
                return ResponsePolicy.REPORT_INTERPRETATION
            
            if state.intent.needs_evidence and state.evidence_gathered:
                return ResponsePolicy.EVIDENCE_EXPLANATION

        return ResponsePolicy.DIRECT_ANSWER
