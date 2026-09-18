import sys
import os
import json
from dotenv import load_dotenv

# Ensure we can import from the project root
sys.path.append(os.getcwd())
load_dotenv()

from agents.orchestrator.graph import run_marine_agent

questions = [
    {"q": "Is it safe to go fishing near Mumbai?", "lang": "en"},
    {"q": "Where is the nearest PFZ in Kochi?", "lang": "en"},
    {"q": "toofan ki chetawani hai kya?", "lang": "hi"},
    {"q": "kadal kshobham undo", "lang": "ml"},
    {"q": "What is SST?", "lang": "en"},
    {"q": "तेज़ हवा", "lang": "hi"},
    {"q": "How high are the waves near 15.35, 73.55?", "lang": "en"}
]

print("Starting NLP tests. Output will be saved to test.txt...")

with open("test.txt", "w", encoding="utf-8") as f:
    f.write("=== NEERMITRA NLP PIPELINE TEST LOGS ===\n\n")
    
    for item in questions:
        query = item["q"]
        lang = item["lang"]
        print(f"Testing: {query}")
        f.write(f"--- QUERY ---\n")
        f.write(f"Text: {query}\n")
        f.write(f"Language: {lang}\n\n")
        
        try:
            # We pass context with a location so that default routing works too
            result = run_marine_agent(
                query=query, 
                language=lang,
                context={"location": "Mumbai"}
            )
            
            f.write("--- RESPONSE ---\n")
            f.write(f"Text: {result.get('text')}\n")
            f.write(f"Risk: {result.get('risk')}\n")
            f.write(f"Agents Invoked: {', '.join(result.get('agents_invoked', []))}\n")
            f.write(f"Conditions: {result.get('conditions')}\n")
            f.write("\n========================================\n\n")
        except Exception as e:
            f.write(f"--- ERROR ---\n")
            f.write(f"{str(e)}\n")
            f.write("\n========================================\n\n")
            print(f"Error testing {query}: {e}")

print("Testing complete. Check test.txt for logs.")
