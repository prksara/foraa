from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional

class SafetyLevel(str, Enum):
    SAFE_GENERAL = "SAFE_GENERAL"
    CAUTION = "CAUTION"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    PROFESSIONAL_REVIEW = "PROFESSIONAL_REVIEW"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"

class ConfidenceCategory(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"

class SafetyClassificationResult(BaseModel):
    level: SafetyLevel = SafetyLevel.SAFE_GENERAL
    reasons: List[str] = Field(default_factory=list)
    detected_signals: List[str] = Field(default_factory=list)
    confidence_category: ConfidenceCategory = ConfidenceCategory.HIGH
    recommended_action: Optional[str] = None
    response_constraints: List[str] = Field(default_factory=list)

class ClaimValidationResult(BaseModel):
    claim: str
    status: str  # SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED
    reason: str

class ValidationResult(BaseModel):
    is_safe: bool = True
    claims: List[ClaimValidationResult] = Field(default_factory=list)
    invalid_citations: List[str] = Field(default_factory=list)
    rewrite_required: bool = False
    rewrite_reason: Optional[str] = None
