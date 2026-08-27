from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class QueryCategory(str, Enum):
    GENERAL_HEALTH = "GENERAL_HEALTH"
    SYMPTOM = "SYMPTOM"
    MEDICATION = "MEDICATION"
    LAB_RESULT = "LAB_RESULT"
    MEDICAL_REPORT = "MEDICAL_REPORT"
    NUTRITION = "NUTRITION"
    FITNESS = "FITNESS"
    MENTAL_WELLNESS = "MENTAL_WELLNESS"
    PREVENTION = "PREVENTION"
    LIFESTYLE = "LIFESTYLE"
    HEALTH_HISTORY = "HEALTH_HISTORY"
    FOLLOW_UP = "FOLLOW_UP"
    URGENT = "URGENT"
    OTHER = "OTHER"

class QueryComplexity(str, Enum):
    SIMPLE = "SIMPLE"       # e.g., "Hi", "What's my age again?"
    COMPLEX = "COMPLEX"     # e.g., "My lab results show high ferritin, what should I do?"

class UncertaintyLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"

class SafetyState(str, Enum):
    SAFE = "SAFE"
    NEEDS_ESCALATION = "NEEDS_ESCALATION"
    EMERGENCY = "EMERGENCY"

class ResponsePolicy(str, Enum):
    DIRECT_ANSWER = "DIRECT_ANSWER"
    ASK_CLARIFICATION = "ASK_CLARIFICATION"
    EVIDENCE_EXPLANATION = "EVIDENCE_EXPLANATION"
    REPORT_INTERPRETATION = "REPORT_INTERPRETATION"
    SAFETY_ESCALATION = "SAFETY_ESCALATION"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    CLINICAL_REVIEW = "CLINICAL_REVIEW"

class ValidationStatus(str, Enum):
    PENDING = "PENDING"
    VALID = "VALID"
    INVALID_RETRY = "INVALID_RETRY"
    FAILED_ABORT = "FAILED_ABORT"

class IntentAnalysis(BaseModel):
    categories: List[QueryCategory] = Field(default_factory=list)
    complexity: QueryComplexity = QueryComplexity.SIMPLE
    needs_evidence: bool = False
    needs_profile: bool = False
    needs_reports: bool = False

class SubQuestion(BaseModel):
    id: str
    text: str
    type: str
    evidence_required: bool = False
    context_required: bool = False

class CandidateInterpretation(BaseModel):
    description: str
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    confidence_category: UncertaintyLevel

class ContradictionItem(BaseModel):
    description: str
    conflicting_items: List[str]
    severity: str # LOW, HIGH
    resolution_required: bool = False

class MissingInformation(BaseModel):
    missing_items: List[str]
    status: str # required, optional, irrelevant

class ReasoningState(BaseModel):
    """
    Internal structured representation of the health reasoning pipeline.
    Maintains all metadata across the lifecycle of a request.
    DOES NOT store raw text of private chain-of-thought to prevent leakage.
    """
    request_id: str
    user_id: str
    conversation_id: str
    message: str

    intent: Optional[IntentAnalysis] = None
    
    # Context filtered by relevance
    relevant_context_keys: List[str] = Field(default_factory=list)
    
    # Evidence gathered
    evidence_gathered: bool = False
    evidence_count: int = 0
    
    # Reasoning execution 
    sub_questions: List[SubQuestion] = Field(default_factory=list)
    candidate_interpretations: List[CandidateInterpretation] = Field(default_factory=list)
    
    # Checks
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    missing_information: Optional[MissingInformation] = None
    uncertainty: UncertaintyLevel = UncertaintyLevel.LOW
    
    # Policy and Validation
    safety_state: SafetyState = SafetyState.SAFE
    response_policy: ResponsePolicy = ResponsePolicy.DIRECT_ANSWER
    validation_status: ValidationStatus = ValidationStatus.PENDING
    
    # Observability
    created_at: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: int = 0
