import logging
from typing import List, Dict

from .schemas import UncertaintyLevel, MissingInformation, ContradictionItem

logger = logging.getLogger("foraa.reasoning.uncertainty")

class UncertaintyEngine:
    """
    Deterministically calculates uncertainty based on the presence of contradictions,
    missing information, and evidence availability.
    """
    def __init__(self):
        pass

    def calculate(
        self, 
        has_evidence: bool, 
        contradictions: List[ContradictionItem], 
        missing_info: MissingInformation,
        is_complex: bool
    ) -> UncertaintyLevel:
        
        # High uncertainty triggers
        if missing_info and missing_info.status == "required":
            return UncertaintyLevel.HIGH
            
        high_severity_contradictions = [c for c in contradictions if c.severity == "HIGH"]
        if high_severity_contradictions:
            return UncertaintyLevel.HIGH

        # Moderate uncertainty triggers
        if is_complex and not has_evidence:
            return UncertaintyLevel.MODERATE
            
        low_severity_contradictions = [c for c in contradictions if c.severity == "LOW"]
        if low_severity_contradictions:
            return UncertaintyLevel.MODERATE

        # Low uncertainty
        return UncertaintyLevel.LOW
