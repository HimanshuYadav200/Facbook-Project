from agents.visual_agent import VisualAgent
from utils.metaphor_comparison import MetaphorQualityAnalyzer
import json

def test_visual_quality():
    print(">>> TESTING VISUAL AGENT METAPHOR SYSTEM <<<")
    
    # Test script related to energy crisis (CFH style)
    test_script = {
        "title": "Germany's Energy Crisis and Deindustrialization",
        "hook": {"text": "Germany turned off its nuclear power, and now its factories are dying."},
        "sections": [
            {
                "title": "The Shutdown", 
                "sentences": [
                    "Germany effectively committed economic suicide in 2011.",
                    "Reactors were shut down, and coal was burned instead.",
                    "Energy prices skyrocketed by 400% in a single year."
                ]
            }
        ]
    }
    
    # 1. Generate Prompts using new agent
    print("\n[*] Initializing VisualAgent...")
    agent = VisualAgent()
    
    sentences = test_script["sections"][0]["sentences"]
    print(f"[*] Generating prompts for {len(sentences)} sentences...")
    
    prompts = agent.generate_image_prompts(test_script, sentences=sentences)
    
    # Check results
    print(f"\n[*] Generated {len(prompts)} prompts:")
    for p in prompts:
        print(f"\nFILE: {p['filename']}")
        print(f"PROMPT: {p['prompt'][:150]}...")
        if 'metaphor_data' in p:
             print(f"SYMBOL: {p['metaphor_data'].get('symbol', 'N/A')}")
    
    # 2. Analyze Quality
    print("\n[*] Analyzing Quality...")
    analyzer = MetaphorQualityAnalyzer()
    report = analyzer.generate_quality_report(prompts)
    
    try:
        print(report)
    except:
        # Force ASCII for Windows Console
        print(report.encode('ascii', 'ignore').decode('ascii'))

    
    # 3. Test Thumbnail
    print("\n[*] Testing Thumbnail Generation...")
    thumb_prompt = agent.generate_thumbnail_prompt(test_script)
    print(f"THUMBNAIL PROMPT:\n{thumb_prompt[:300]}...")

if __name__ == "__main__":
    test_visual_quality()
