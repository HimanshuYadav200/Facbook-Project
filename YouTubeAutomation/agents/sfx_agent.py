import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.llm_client import LLMClient
from utils.elevenlabs_client import ElevenLabsClientManager

class SFXAgent:
    """
    Generates dynamic sound effects for each scene using ElevenLabs Sound Effects API.
    Uses LLM to analyze scene tone and generate appropriate SFX descriptions.
    """
    
    def __init__(self):
        self.client_manager = ElevenLabsClientManager()
        self.llm = LLMClient()
        
    def _analyze_scene_tone(self, scene_text, scene_type="body"):
        """
        Uses LLM to analyze scene tone and suggest an appropriate SFX description.
        Returns a short SFX prompt for ElevenLabs.
        """
        prompt = f"""You are a professional sound designer for YouTube Shorts.

Analyze this scene and suggest a SHORT sound effect description (max 10 words).
The sound effect should enhance the emotional impact of the scene.

Scene Type: {scene_type}
Scene Text: "{scene_text}"

Guidelines:
- For financial gains/money: cash register, coins, success chime
- For losses/crashes: dramatic impact, tension drop, alarm
- For news/alerts: notification sound, news intro, urgent beep
- For transitions: whoosh, swoosh, subtle transition
- For climax/endings: dramatic finale, resolution chord
- Keep it SHORT and descriptive

Respond with ONLY the SFX description, nothing else.
Example responses:
- "cash register ding with coins falling"
- "dramatic stock market crash impact"
- "suspenseful rising tension whoosh"
- "news alert notification beep"
"""
        
        try:
            response = self.llm.generate_text(prompt)
            if not response:
                raise Exception("Empty LLM response")
            sfx_desc = response.strip().strip('"').strip("'")
            
            # Ensure it's not too long
            if len(sfx_desc) > 100:
                sfx_desc = sfx_desc[:100]
                
            return sfx_desc
        except Exception as e:
            print(f"[!] SFX tone analysis failed: {e}")
            # Fallback based on scene type with more variety
            fallbacks = {
                "hook": "dramatic attention grabbing impact sound",
                "climax": "triumphant resolution orchestral hit",
                "close": "satisfying outro chime with echo",
                "body": "subtle cinematic transition whoosh",
                "suspense": "tense rising suspenseful drone",
                "context": "deep dramatic bass hit",
                "history": "ominous historical documentary tone",
                "alert": "urgent news alert notification sound",
                "warning": "alarming warning siren subtle"
            }
            return fallbacks.get(scene_type, "cinematic transition whoosh")
    
    def _generate_sfx_audio(self, sfx_description, output_path, duration=1.5):
        """
        Generates sound effect audio using ElevenLabs API with FAILOVER logic.
        """
        # Ensure client is ready
        if not self.client_manager.get_client():
            print("[!] No ElevenLabs client available")
            return None

        # Try with current key, then backup if needed
        max_attempts = 2 if self.client_manager.has_backup_available() else 1
        
        for attempt in range(max_attempts):
            try:
                client = self.client_manager.get_client()
                
                print(f"    Generating SFX: '{sfx_description[:50]}...'")
                
                # Use text_to_sound_effects API
                audio_generator = client.text_to_sound_effects.convert(
                    text=sfx_description,
                    duration_seconds=duration
                )
                
                # Save to file
                with open(output_path, "wb") as f:
                    for chunk in audio_generator:
                        f.write(chunk)
                
                return output_path
                
            except Exception as e:
                print(f"[!] SFX generation failed: {e}")
                
                # Cleanup partial file
                if os.path.exists(output_path):
                    try: os.remove(output_path)
                    except: pass
                
                # Check quota error
                if self.client_manager.is_quota_error(e):
                    print("    [!] Credits exhausted on current API key.")
                    if self.client_manager.switch_to_backup():
                        print("    [*] Retrying with backup key...")
                        continue
                    else:
                        print("    [!] No backup key available.")
                        return None
                else:
                    return None
        return None
    
    def _identify_key_scenes(self, script_data):
        """
        Uses LLM to identify the 3-5 most impactful scenes that deserve SFX.
        Returns list of scene keys that should have sound effects.
        """
        # Build scene list for analysis
        all_scenes = []
        if "hook" in script_data:
            all_scenes.append(("hook", script_data["hook"]["text"]))

        if "context" in script_data:
            all_scenes.append(("context", script_data["context"]["text"]))

        if "historical_precedents" in script_data:
            for i, scene in enumerate(script_data["historical_precedents"]):
                all_scenes.append((f"history_{i+1:02d}", scene["text"]))

        if "warning" in script_data:
            all_scenes.append(("warning", script_data["warning"]["text"]))

        if "close" in script_data:
            all_scenes.append(("close", script_data["close"]["text"]))
        
        if "body" in script_data:
            for i, scene in enumerate(script_data["body"]):
                all_scenes.append((f"body_{i+1:02d}", scene["text"]))
        
        if "climax" in script_data:
            all_scenes.append(("climax", script_data["climax"]["text"]))
        
        # Format for LLM
        scene_list = "\n".join([f"{key}: {text}" for key, text in all_scenes])
        
        prompt = f"""You are a sound designer for YouTube Shorts. Analyze these scenes and identify which ones need sound effects.

SCENES:
{scene_list}

RULES:
1. ALWAYS include: hook and climax (for impact)
2. Select 4-5 body scenes with the HIGHEST emotional impact:
   - Money moments (gaining/losing specific amounts like $14, $150)
   - Shocking revelations or surprises
   - Dramatic turns ("But here's the kicker...", "Then it got worse...")
   - Emotional peaks (joy, relief, despair)
   - Action moments (giving, receiving, discovering)
3. Spread the SFX throughout the video - not just at the start
4. Skip purely explanatory/transitional scenes
5. Maximum 7 scenes total

OUTPUT FORMAT: Return ONLY a comma-separated list of scene keys.
Example: hook, body_03, body_06, body_09, body_12, body_15, climax

Select the key scenes now:
"""
        
        try:
            response = self.llm.generate_text(prompt)
            if not response:
                raise Exception("Empty LLM response")
            scene_keys = [k.strip() for k in response.strip().split(",")]
            
            # Ensure hook and climax are included
            if "hook" not in scene_keys and "hook" in [s[0] for s in all_scenes]:
                scene_keys.insert(0, "hook")
            if "climax" not in scene_keys and "climax" in [s[0] for s in all_scenes]:
                scene_keys.append("climax")
            
            # Limit to 7 max (hook + 5 body + climax)
            scene_keys = scene_keys[:7]
            
            print(f"[*] Key scenes selected for SFX: {scene_keys}")
            return scene_keys
            
        except Exception as e:
            print(f"[!] Scene identification failed: {e}")
            # Fallback: key scenes for long-form content
            # Include hook, one from each major section, warning, and close
            fallback_keys = ["hook", "context", "history_01", "history_02", "warning", "close"]
            # Filter to only include scenes that actually exist
            existing = [s[0] for s in all_scenes]
            return [k for k in fallback_keys if k in existing][:7]
    
    def generate_sfx(self, script_data, assets_dir):
        """
        Generates sound effects for KEY scenes only (not all scenes).
        Saves API credits by only generating SFX for high-impact moments.
        Returns a mapping: {scene_key: sfx_file_path}
        """
        print("\n[SFX AGENT] Generating Dynamic Sound Effects...")
        print("[*] Identifying key scenes for SFX (not every scene needs one)...")
        
        sfx_mapping = {}
        
        # Step 1: Identify which scenes need SFX
        key_scenes = self._identify_key_scenes(script_data)
        
        # Build full scene data
        all_scenes = {}
        if "hook" in script_data:
            all_scenes["hook"] = {"text": script_data["hook"]["text"], "type": "hook"}
            
        if "body" in script_data: # Shorts Legacy
            for i, scene in enumerate(script_data["body"]):
                all_scenes[f"body_{i+1:02d}"] = {"text": scene["text"], "type": "body"}

        # LONG FORM SECTIONS
        if "context" in script_data:
             all_scenes["context"] = {"text": script_data["context"]["text"], "type": "suspense"}
             
        if "historical_precedents" in script_data:
            for i, scene in enumerate(script_data["historical_precedents"]):
                all_scenes[f"history_{i+1:02d}"] = {"text": scene["text"], "type": "history"}

        if "warning" in script_data:
             all_scenes["warning"] = {"text": script_data["warning"]["text"], "type": "alert"}

        if "close" in script_data:
             all_scenes["close"] = {"text": script_data["close"]["text"], "type": "climax"}
             
        if "climax" in script_data: # Shorts Legacy
            all_scenes["climax"] = {"text": script_data["climax"]["text"], "type": "climax"}
        
        # Step 2: Generate sfx_requests.txt for manual fallback
        sfx_requests_path = os.path.join(assets_dir, "sfx_requests.txt")
        with open(sfx_requests_path, "w", encoding="utf-8") as f:
            f.write("=== SFX ASSET REQUESTS ===\n")
            f.write("API: ElevenLabs Text to Sound Effects\n")
            f.write("Duration: 1.5 seconds each\n")
            f.write("Save files with EXACT names to this folder.\n\n")
            
            for scene_key in key_scenes:
                if scene_key not in all_scenes:
                    continue
                scene = all_scenes[scene_key]
                sfx_desc = self._analyze_scene_tone(scene["text"], scene["type"])
                
                f.write(f"SECTION: {scene_key.upper()}\n")
                f.write(f"REQUIRED FILENAME: sfx_{scene_key}.mp3\n")
                f.write(f"SCENE TEXT: {scene['text']}\n")
                f.write(f"SFX DESCRIPTION: {sfx_desc}\n")
                f.write("-" * 40 + "\n\n")
        
        print(f"[*] SFX requests saved to: {sfx_requests_path}")
        print("    (Use this file for manual ElevenLabs SFX generation if API fails)")
        
        # Step 3: Generate SFX audio files
        for scene_key in key_scenes:
            if scene_key not in all_scenes:
                continue
                
            scene = all_scenes[scene_key]
            print(f"\n[*] Scene: {scene_key}")
            
            # Analyze tone with LLM
            sfx_description = self._analyze_scene_tone(scene["text"], scene["type"])
            print(f"    Tone Analysis: {sfx_description}")
            
            # Generate audio with ElevenLabs
            sfx_filename = f"sfx_{scene_key}.mp3"
            sfx_path = os.path.join(assets_dir, sfx_filename)
            
            generated_path = self._generate_sfx_audio(sfx_description, sfx_path, duration=1.5)
            
            if generated_path:
                sfx_mapping[scene_key] = generated_path
                print(f"    [OK] Saved: {sfx_filename}")
            else:
                print(f"    [FAIL] Failed to generate SFX for {scene_key}")
        
        print(f"\n[*] SFX Generation Complete: {len(sfx_mapping)} files (key scenes only)")
        print(f"    API calls saved: {len(all_scenes) - len(key_scenes)} (skipped non-essential scenes)")
        return sfx_mapping


if __name__ == "__main__":
    # Test with sample script
    test_script = {
        "hook": {"text": "In 2025, the market crashed by 50% overnight."},
        "body": [
            {"text": "Investors panicked as stocks tumbled."},
            {"text": "But one trader made $10 million that day."}
        ],
        "climax": {"text": "Here's how you can prepare for the next crash."}
    }
    
    agent = SFXAgent()
    result = agent.generate_sfx(test_script, "assets")
    print(f"\nResult: {result}")
