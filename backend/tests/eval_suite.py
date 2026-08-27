import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(env_path)

from ai.intent import IntentAnalyzer
from services.evidence_retrieval import EvidenceRetrievalService
from ai.health_context import HealthContextBuilder

# Just a simple runner to test the Intent Analyzer and Retrieval logic manually.
async def run_evals():
    analyzer = IntentAnalyzer()
    
    test_queries = [
        ("Hi, how are you?", "general_greeting"),
        ("What is a normal blood pressure?", "general_health"),
        ("Based on my peanut allergy, what protein can I eat?", "personal_health"),
        ("I'm having severe chest pain right now, what should I do?", "urgent"),
        ("Can you interpret my uploaded blood report?", "report_interpretation"),
        ("What does the latest evidence say about Vitamin D and bone health?", "nutrition"),
        ("Should I stop taking my lisinopril?", "medication")
    ]
    
    print("=== Intent Classification Evaluation ===")
    for query, expected in test_queries:
        intent = await asyncio.to_thread(analyzer.analyze, query)
        print(f"Query: {query}")
        print(f"Categories: {intent.get('categories')}")
        print(f"Needs Evidence: {intent.get('needs_evidence')}")
        print(f"Needs Profile: {intent.get('needs_profile')}")
        print("-" * 40)

    print("\n=== Intent Classification Complete ===")

if __name__ == "__main__":
    asyncio.run(run_evals())
