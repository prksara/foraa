import asyncio
import logging
from typing import List, Dict
import json
import uuid

from safety import SafetyClassifier, MedicationSafetyChecker, SafetyLevel
from .datasets import get_evaluation_cases
from .metrics import EvaluationMetrics

from database.database import get_db, init_db
from database.models import EvaluationRun

logger = logging.getLogger("foraa.evaluation.runner")

class EvaluationRunner:
    def __init__(self):
        self.cases = get_evaluation_cases()
        self.classifier = SafetyClassifier()
        self.med_checker = MedicationSafetyChecker()
        self.metrics = EvaluationMetrics()

    async def run(self):
        logger.info(f"Starting Evaluation Run for {len(self.cases)} cases.")
        self.metrics.total_cases = len(self.cases)
        
        for case in self.cases:
            user_msg = case["input"]
            context = case["context"]
            expected_level = case["expected_safety_level"]
            
            # Run safety checks
            safety_result = await asyncio.to_thread(self.classifier.classify, user_msg, context)
            med_result = await asyncio.to_thread(self.med_checker.check, user_msg, context)
            
            actual_level = safety_result.level.value
            if not med_result["is_safe"]:
                actual_level = "CAUTION" # Map med fail to at least caution if not already urgent
                if safety_result.level in [SafetyLevel.URGENT, SafetyLevel.EMERGENCY]:
                    actual_level = safety_result.level.value
                    
            passed = (actual_level == expected_level)
            
            # Simple False Negative/Positive checks for URGENT/EMERGENCY
            if expected_level in ["URGENT", "EMERGENCY"] and actual_level not in ["URGENT", "EMERGENCY"]:
                self.metrics.false_negatives += 1
                passed = False
                
            if expected_level not in ["URGENT", "EMERGENCY"] and actual_level in ["URGENT", "EMERGENCY"]:
                self.metrics.false_positives += 1
                passed = False

            if passed:
                self.metrics.passed_cases += 1
            else:
                self.metrics.failed_cases += 1
                logger.error(f"FAILED CASE: Expected {expected_level}, Got {actual_level} | Input: '{user_msg}'")
                
            await asyncio.sleep(2.5) # Avoid rate limit

        self.metrics.calculate()
        logger.info(f"Evaluation Complete. Accuracy: {self.metrics.safety_accuracy*100:.1f}%. FN: {self.metrics.false_negatives} FP: {self.metrics.false_positives}")
        
        # Save to DB
        async for session in get_db():
            run_record = EvaluationRun(
                run_name=f"evaluation_{uuid.uuid4().hex[:8]}",
                total_cases=self.metrics.total_cases,
                passed_cases=self.metrics.passed_cases,
                failed_cases=self.metrics.failed_cases,
                metrics_json=self.metrics.model_dump()
            )
            session.add(run_record)
            await session.commit()
            break
            
        return self.metrics

async def main():
    await init_db()
    runner = EvaluationRunner()
    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())
