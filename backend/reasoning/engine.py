import time
import asyncio
import logging
from typing import Optional, AsyncGenerator

from .schemas import (
    ReasoningState, QueryComplexity, SafetyState, ResponsePolicy
)
from .classifier import QueryClassifier
from .decomposer import QuestionDecomposer
from .context_relevance import ContextRelevanceScorer
from .evidence_mapper import EvidenceMapper
from .contradiction import ContradictionDetector
from .missing_information import MissingInformationDetector
from .uncertainty import UncertaintyEngine
from .policy import PolicyEngine
from .validator import ResponseValidator

logger = logging.getLogger("foraa.reasoning.engine")

class ReasoningEngine:
    def __init__(self):
        self.classifier = QueryClassifier()
        self.decomposer = QuestionDecomposer()
        self.relevance_scorer = ContextRelevanceScorer()
        self.evidence_mapper = EvidenceMapper()
        self.contradiction_detector = ContradictionDetector()
        self.missing_info_detector = MissingInformationDetector()
        self.uncertainty_engine = UncertaintyEngine()
        self.policy_engine = PolicyEngine()
        self.validator = ResponseValidator()

    async def execute_reasoning_pipeline(
        self, 
        state: ReasoningState, 
        context_text: str, 
        evidence_text: str,
        yield_status_callback=None
    ) -> ReasoningState:
        """
        Executes the reasoning pipeline for a given request.
        Updates and returns the ReasoningState.
        """
        start_time = time.time()
        
        async def _emit(msg: str):
            if yield_status_callback:
                await yield_status_callback(msg)

        # 1. Classification
        await _emit("Analyzing your question...")
        state.intent = await asyncio.to_thread(self.classifier.classify, state.message)
        
        # Fast path for simple queries
        if state.intent.complexity == QueryComplexity.SIMPLE and not state.intent.needs_evidence:
            state.response_policy = ResponsePolicy.DIRECT_ANSWER
            state.latency_ms = int((time.time() - start_time) * 1000)
            return state

        # 2. Decomposition (if complex)
        if state.intent.complexity == QueryComplexity.COMPLEX:
            await _emit("Breaking down the question...")
            state.sub_questions = await asyncio.to_thread(self.decomposer.decompose, state.message)

        # 3. Context Relevance
        available_keys = ["profile", "active_conditions", "allergies", "active_medications", "active_goals", "recent_health_events"]
        state.relevant_context_keys = await asyncio.to_thread(self.relevance_scorer.score, state.message, available_keys)

        # 4. Contradiction Detection
        if context_text or evidence_text:
            await _emit("Checking for medical conflicts...")
            state.contradictions = await asyncio.to_thread(self.contradiction_detector.detect, state.message, context_text)

        # 5. Missing Information
        await _emit("Identifying missing information...")
        state.missing_information = await asyncio.to_thread(self.missing_info_detector.detect, state.message, context_text)

        # 6. Uncertainty Assessment
        state.uncertainty = self.uncertainty_engine.calculate(
            has_evidence=state.evidence_gathered,
            contradictions=state.contradictions,
            missing_info=state.missing_information,
            is_complex=(state.intent.complexity == QueryComplexity.COMPLEX)
        )

        # 7. Policy Selection
        state.response_policy = self.policy_engine.evaluate(state)
        
        if state.response_policy == ResponsePolicy.SAFETY_ESCALATION:
            state.safety_state = SafetyState.NEEDS_ESCALATION

        await _emit("Formulating response...")
        state.latency_ms = int((time.time() - start_time) * 1000)
        return state
