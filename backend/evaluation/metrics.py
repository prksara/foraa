from pydantic import BaseModel
from typing import Dict

class EvaluationMetrics(BaseModel):
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    safety_accuracy: float = 0.0

    def calculate(self):
        if self.total_cases > 0:
            self.safety_accuracy = self.passed_cases / self.total_cases
