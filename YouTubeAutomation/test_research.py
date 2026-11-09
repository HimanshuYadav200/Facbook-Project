
import os
import sys
import json
from agents.research_agent import ResearchAgent

# Mock the environment if needed, but we want to see real behavior with current credentials
def test_research_execution():
    print(">>> Testing Research Agent Execution (Short Form)...")
    
    agent = ResearchAgent(topic="Skulsy buys Bitcoin 2012", content_type="short")
    
    try:
        results = agent.execute()
        
        print("\n>>> Research Output:")
        print(json.dumps(results, indent=2))
        
        # Validation
        if not results.get('topic_decomposition'):
            print("❌ Topic Decomposition failed")
        else:
            print("✅ Topic Decomposition success")
            
        if 'core_facts' in results:
            print(f"✅ Output has {len(results['core_facts'])} facts (may be 0 if no keys)")
        else:
            print("❌ Output missing 'core_facts' key")
            
        return results
        
    except Exception as e:
        print(f"❌ Execution crashed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_long_form_execution():
    print("\n>>> Testing Research Agent Execution (Long Form)...")
    agent = ResearchAgent(topic="The 2008 Housing Crisis", content_type="long")
    try:
        results = agent.execute()
        
        if 'long_form_modules' in results:
             print(f"✅ Long Form Modules Generated: {len(results['long_form_modules'].get('modules', []))}")
             print(json.dumps(results['long_form_modules'], indent=2))
        else:
             print("❌ Long Form Modules missing")
             
    except Exception as e:
        print(f"❌ Long Form Execution crashed: {e}")

if __name__ == "__main__":
    # Ensure raw output
    res = test_research_execution()
    if res:
        test_long_form_execution()
