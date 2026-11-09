"""
Test script to regenerate visual_requests.txt only.
Uses existing script.json to verify visual prompts before spending API credits.
"""
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agents.visual_agent import VisualAgent

def test_visual_prompts(assets_dir):
    """Generate visual prompts from existing script.json"""
    
    script_path = os.path.join(assets_dir, "script.json")
    
    if not os.path.exists(script_path):
        print(f"[!] script.json not found at: {script_path}")
        return
    
    print(f"[*] Loading script from: {script_path}")
    
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)
    
    print(f"[*] Script loaded: {len(script_data.get('body', []))} body scenes")
    
    # Show script summary
    print("\n=== SCRIPT SUMMARY ===")
    print(f"HOOK: {script_data['hook']['text'][:80]}...")
    print(f"BODY: {len(script_data.get('body', []))} scenes")
    print(f"CLIMAX: {script_data['climax']['text'][:80]}...")
    
    # Generate visual prompts
    print("\n>>> Generating Visual Prompts...")
    visual_agent = VisualAgent()
    prompts = visual_agent.generate_image_prompts(script_data)
    
    print(f"\n[*] Generated {len(prompts)} visual prompts")
    
    # Build ordered list matching audio files
    audio_keys = ["hook"]
    for i in range(len(script_data.get("body", []))):
        audio_keys.append(f"body_{i+1:02d}")
    audio_keys.append("climax")
    
    # Write visual_requests.txt
    visual_requests_path = os.path.join(assets_dir, "visual_requests.txt")
    with open(visual_requests_path, "w", encoding="utf-8") as f:
        f.write("=== VISUAL ASSET REQUESTS ===\n")
        f.write("Save files with EXACT names to this folder. Support: .png or .mp4\n\n")
        
        for i, section_key in enumerate(audio_keys):
            audio_fname = f"audio_{section_key.replace('body_', 'scene_')}.mp3"
            if section_key == "hook": audio_fname = "audio_hook.mp3"
            elif section_key == "climax": audio_fname = "audio_climax.mp3"
            
            p_data = prompts[i] if i < len(prompts) else {"prompt": "Default Stickman", "type": "image"}
            
            ext = ".mp4" if p_data.get("type") == "animation" else ".png"
            asset_fname = f"visual_{section_key}{ext}"
            
            f.write(f"SECTION: {section_key.upper()}\n")
            f.write(f"REQUIRED FILENAME: {asset_fname}\n")
            f.write(f"TYPE: {p_data.get('type', 'image')}\n")
            f.write(f"PROMPT: {p_data.get('prompt')}\n")
            f.write("-" * 40 + "\n\n")
    
    print(f"\n[OK] Visual requests saved to: {visual_requests_path}")
    print("\n=== FIRST 3 VISUAL PROMPTS ===")
    for i, p in enumerate(prompts[:3]):
        print(f"\n{i+1}. {p.get('filename', 'unknown')}")
        print(f"   Type: {p.get('type', 'image')}")
        print(f"   Prompt: {p.get('prompt', 'N/A')[:100]}...")
    
    print("\n" + "="*50)
    print("CHECK the visual_requests.txt file to verify prompts!")
    print("="*50)


if __name__ == "__main__":
    # Use the existing run folder
    assets_dir = r"C:\Users\Himanshu Yadav\OneDrive\Desktop\Finance-agent\YouTubeAutomation\assets\run_20260110_204601"
    
    if len(sys.argv) > 1:
        assets_dir = sys.argv[1]
    
    test_visual_prompts(assets_dir)
