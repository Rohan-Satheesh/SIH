"""
test_nlp_pipeline.py
"""
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
from dotenv import load_dotenv
load_dotenv()

from nlp.orca_service import process_query
from nlp.detection.intent_classifier import classify_intent

queries = [
    "What is PFZ?",
    "What is SST?",
    "Can Python analyze SST data?",
    "What is the stock status of fish?",
    "How can I find a good fishing area?",
    "Give me a cake recipe.",
    "What about tomorrow?"
]

print("--- CLASSIFICATION TESTS ---")
for q in queries:
    intent = classify_intent(q)
    print(f"Q: '{q}' -> Intent: {intent['intent']} (Conf: {intent['confidence']:.2f})")

print("\n--- PIPELINE TESTS (WITH KEY) ---")
# Ensure key is present
key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
print(f"Key loaded: {bool(key)}")
for q in ["What is PFZ?", "Can Python analyze SST data?"]:
    res = process_query(q)
    print(f"Q: '{q}'\nA: {res['answer']}\n")

print("\n--- PIPELINE TESTS (WITHOUT KEY / OFFLINE) ---")
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]
if "GOOGLE_API_KEY" in os.environ:
    del os.environ["GOOGLE_API_KEY"]
    
for q in ["What is PFZ?", "Can Python analyze SST data?", "Give me a cake recipe."]:
    res = process_query(q)
    print(f"Q: '{q}'\nA: {res['answer']}\n")
