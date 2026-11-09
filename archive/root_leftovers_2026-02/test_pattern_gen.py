
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "YouTubeAutomation"))

from YouTubeAutomation.agents.script_agent import ScriptAgent

def test_v5_locking():
    print(">>> Testing Skulsy V5 Number Locking & Pattern Loading...")
    
    agent = ScriptAgent()
    
    # Dummy Research with Specific Numbers
    dummy_research = {
        "core_facts": [
            "Skulsy bought Enron stock at $90.50 in August 2000.",
            "By December 2001, the price hit $0.26.",
            "He lost 99.7% of his investment."
        ],
        "topic_decomposition": {
            "decision": "bought Enron",
            "asset": "Enron Stock",
            "start_year": "2000",
            "end_year": "2001",
            "key_events": ["CEO resigns", "SEC investigation"]
        }
    }
    
    # Generate with Mistake pattern
    print("[*] Generating script with 'mistake' pattern...")
    script = agent.generate_skulsy_script(
        topic="Skulsy buys Enron", 
        research_brief=dummy_research, 
        pattern="mistake"
    )
    
    if not script:
        print("[!] FAIL: No script returned.")
        return
        
    print("[*] Script generated successfully.")
    print(f"Title: {script.get('title')}")
    
    # Verify Number Locking
    full_text = " ".join([s['text'] for s in script.get('sentences', [])])
    print(f"Full Text: {full_text[:100]}...")
    
    missing = []
    if "$90.50" not in full_text: missing.append("$90.50")
    if "$0.26" not in full_text: missing.append("$0.26")
    
    if missing:
        print(f"[!] FAIL: Locked numbers missing: {missing}")
        print("V5 Number Locking check failed.")
    else:
        print("[PASS] All locked numbers found in script.")
        
    # Verify Pattern Structure
    if "beat_map" in script:
        print(f"[PASS] Beat map present: {list(script['beat_map'].keys())}")
    else:
        print("[!] FAIL: Beat map missing.")

if __name__ == "__main__":
    test_v5_locking()
