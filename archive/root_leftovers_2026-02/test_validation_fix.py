
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "YouTubeAutomation"))

from YouTubeAutomation.agents.script_agent import ScriptAgent
from YouTubeAutomation.agents.quality_validator_agent import QualityValidatorAgent

def test_validation_logic():
    print("Testing Validation Logic Fixes...")
    
    validator = QualityValidatorAgent()
    
    # Mock Research Data
    research_data = {
        "core_facts": [
            "Skulsy bought Amazon stock at $10.50 in 2001",
            "He sold it when it reached $15.75 per share",
            "This resulted in a 50% ROI"
        ],
        "data_points": [
            {"value": "$10.50", "date": "2001-01-01"},
            {"value": "50%", "context": "return"}
        ]
    }
    
    # Mock Script Data (Correct)
    correct_script = {
        "sentences": [
            {"text": "Skulsy bought Amazon at $10.50 back in 2001."},
            {"text": "He waited until it hit $15.75."},
            {"text": "He made a 50% return on investment."}
        ]
    }
    
    # Mock Script Data (Flawed - wrong number, missing year)
    flawed_script = {
        "sentences": [
            {"text": "Skulsy bought Amazon at $99.00."}, # Wrong price
            {"text": "He sold it later."}, # Missing price
            {"text": "He made a 5% return."} # Wrong %
        ]
    }
    
    # Test Extraction
    print("\n--- Testing Extraction ---")
    nums = validator._extract_research_numbers(research_data)
    print(f"Extracted Research Nums: {nums}")
    
    # Test Scoring (Correct)
    print("\n--- Testing Correct Script ---")
    score_c = validator._score_accuracy(correct_script, research_data)
    print(f"Score (Should be high): {score_c}")
    
    # Test Scoring (Flawed)
    print("\n--- Testing Flawed Script ---")
    score_f = validator._score_accuracy(flawed_script, research_data)
    print(f"Score (Should be low): {score_f}")
    
    # Test Feedback Generation
    if score_f < 70:
        print("\n--- Testing Feedback ---")
        dummy_scores = {"accuracy": score_f, "retention": 80, "narrative": 80, "pacing": 80, "viral": 80}
        feedback = validator._generate_feedback(dummy_scores, flawed_script, research_data)
        print(json.dumps(feedback, indent=2))

if __name__ == "__main__":
    test_validation_logic()
