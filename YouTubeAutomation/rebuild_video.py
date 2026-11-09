import os
import sys
import glob

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agents.editor_agent import EditorAgent

def rebuild():
    # Accept assets directory from command line
    if len(sys.argv) > 1 and sys.argv[1] == "--assets-dir" and len(sys.argv) > 2:
        assets_dir = os.path.abspath(sys.argv[2])
    else:
        assets_dir = os.path.abspath("assets")
    
    output_dir = os.path.abspath("output")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"[*] Rebuilding video from assets in: {assets_dir}")
    
    # 1. Reconstruct Scene List
    # Logic: Find audio files, match with visual files.
    # Order: hook, body_01...body_XX, climax
    
    scenes = []
    
    # Define order keys
    keys = ["hook"]
    # Scan for body indices
    body_audios = glob.glob(os.path.join(assets_dir, "audio_scene_*.mp3"))
    # extract indices
    indices = []
    for p in body_audios:
        try:
            fname = os.path.basename(p)
            # audio_scene_01.mp3
            idx_str = fname.replace("audio_scene_", "").replace(".mp3", "")
            indices.append(int(idx_str))
        except: pass
    indices.sort()
    for i in indices:
        keys.append(f"body_{i:02d}")
        
    keys.append("climax")
    
    for k in keys:
        # Audio File
        if k == "hook": audio_name = "audio_hook.mp3"
        elif k == "climax": audio_name = "audio_climax.mp3"
        else:
            # body_02
            idx = int(k.split("_")[1])
            audio_name = f"audio_scene_{idx:02d}.mp3"
            
        audio_path = os.path.join(assets_dir, audio_name)
        
        # Visual File
        # Could be .png or .mp4
        visual_name_base = f"visual_{k}"
        visual_path = None
        
        # Check png
        if os.path.exists(os.path.join(assets_dir, visual_name_base + ".png")):
             visual_path = os.path.join(assets_dir, visual_name_base + ".png")
        # Check mp4
        elif os.path.exists(os.path.join(assets_dir, visual_name_base + ".mp4")):
             visual_path = os.path.join(assets_dir, visual_name_base + ".mp4")
             
        if audio_path and visual_path:
             # Text? We don't have the text map easily unless we read script.json
             # For rebuild, let's just use empty text or try to read script?
             # User mainly cares about visual. But subtitles are important.
             # Let's try to read script.json if possible.
             text = ""
             import json
             try:
                 with open(os.path.join(assets_dir, "script.json"), "r") as f:
                     script = json.load(f)
                     if k == "hook": text = script["hook"]["text"]
                     elif k == "climax": text = script["climax"]["text"]
                     else:
                         # body_02 -> index 1
                         idx = int(k.split("_")[1]) - 1
                         if idx < len(script["body"]):
                             text = script["body"][idx]["text"]
             except:
                 pass
                 
             scenes.append({
                 "asset_path": visual_path,
                 "audio_path": audio_path,
                 "text": text,
                 "scene_key": k  # For SFX mapping
             })
             print(f"Added Scene: {k} | {os.path.basename(visual_path)}")
        else:
             print(f"Skipping {k} (Missing audio or visual)")

    if not scenes:
        print("No scenes found.")
        return

    # 1.5 OPTIONAL: Generate Dynamic SFX
    sfx_mapping = None
    use_dynamic_sfx = input("\nGenerate Dynamic SFX? (y/n, default n): ").lower() == 'y'
    if use_dynamic_sfx and script_path and os.path.exists(os.path.join(assets_dir, "script.json")):
        try:
            from agents.sfx_agent import SFXAgent
            with open(os.path.join(assets_dir, "script.json"), "r") as f:
                script_data = json.load(f)
            sfx_agent = SFXAgent()
            sfx_mapping = sfx_agent.generate_sfx(script_data, assets_dir)
        except Exception as e:
            print(f"SFX generation skipped: {e}")

    # 2. Run Editor
    editor = EditorAgent()
    output_path = os.path.join(output_dir, "rebuild_final.mp4")
    success = editor.create_video(scenes, output_path, sfx_mapping=sfx_mapping)
    
    if success:
        print(f"SUCCESS: {output_path}")
        
        # 3. Running SEO Agent
        print("\n>>> Running SEO Agent...")
        try:
            # We already loaded script locally if possible, but let's re-read specifically for SEO
            script_path = os.path.join(assets_dir, "script.json")
            if os.path.exists(script_path):
                with open(script_path, "r") as f:
                    script_data = json.load(f)
                
                from agents.seo_agent import SEOAgent
                seo = SEOAgent()
                metadata = seo.generate_metadata(script_data)
                
                if metadata:
                    meta_path = os.path.join(output_dir, "metadata_rebuild.txt")
                    with open(meta_path, "w", encoding="utf-8") as f:
                        f.write(f"TITLE: {metadata.get('title')}\n\n")
                        f.write(f"DESCRIPTION:\n{metadata.get('description')}\n\n")
                        f.write(f"TAGS: {metadata.get('tags')}\n\n")
                        f.write(f"THUMBNAIL PROMPT:\n{metadata.get('thumbnail_prompt')}\n")
                    
                    print(f"[*] SEO Metadata saved to: {meta_path}")
                    print("-" * 30)
                    print(f"TITLE: {metadata.get('title')}")
                    print(f"THUMBNAIL: {metadata.get('thumbnail_prompt')}")
                    print("-" * 30)
            else:
                 print("Script.json not found, skipping SEO generation.")
        except Exception as e:
            print(f"Failed to run SEO Agent: {e}")

    else:
        print("FAIL")

if __name__ == "__main__":
    rebuild()
