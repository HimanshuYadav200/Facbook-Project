"""
Audio Agent - Handles ElevenLabs TTS with dual API key failover.
Supports both section-based and sentence-based audio generation.
"""

import os
import sys
import time
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class ElevenLabsClientManager:
    """
    Manages multiple ElevenLabs API keys with automatic failover.
    Switches to backup key when primary key's credits are exhausted.
    """
    
    def __init__(self):
        self.api_keys = []
        self.current_key_index = 0
        self.client = None
        
        # Load API keys from config
        if config.ELEVENLABS_API_KEY:
            self.api_keys.append(config.ELEVENLABS_API_KEY)
        if hasattr(config, 'ELEVENLABS_API_KEY_BACKUP') and config.ELEVENLABS_API_KEY_BACKUP:
            self.api_keys.append(config.ELEVENLABS_API_KEY_BACKUP)
        
        if not self.api_keys:
            print("[!] Warning: No ELEVENLABS_API_KEY configured.")
        else:
            print(f"[*] ElevenLabs: {len(self.api_keys)} API key(s) available")
    
    def get_client(self):
        """Returns current ElevenLabs client, initializing if needed."""
        if self.client is None and self.api_keys:
            self._init_client()
        return self.client
    
    def _init_client(self):
        """Initialize client with current API key."""
        if self.current_key_index < len(self.api_keys):
            try:
                from elevenlabs.client import ElevenLabs
                current_key = self.api_keys[self.current_key_index]
                self.client = ElevenLabs(api_key=current_key)
                print(f"[*] Using ElevenLabs API key #{self.current_key_index + 1}")
            except ImportError:
                print("[!] ElevenLabs SDK not installed")
                self.client = None
    
    def switch_to_backup(self):
        """
        Switches to the next available API key.
        Returns True if switch successful, False if no more keys available.
        """
        self.current_key_index += 1
        
        if self.current_key_index >= len(self.api_keys):
            print("[!] All ElevenLabs API keys exhausted. No backup available.")
            return False
        
        print(f"\n[!] Switching to backup API key #{self.current_key_index + 1}...")
        self._init_client()
        return True
    
    def is_quota_error(self, error):
        """
        Checks if the error indicates quota/credits exhausted.
        """
        error_str = str(error).lower()
        quota_indicators = [
            "quota", "limit", "exceeded", "credits", "insufficient",
            "rate limit", "429", "too many requests", "exhausted",
            "subscription", "billing", "payment required", "402"
        ]
        return any(indicator in error_str for indicator in quota_indicators)
    
    def has_backup_available(self):
        """Check if there's a backup key available."""
        return self.current_key_index + 1 < len(self.api_keys)



class GoogleTTSClient:
    """
    Client for Google Cloud Text-to-Speech (Standard API).
    Uses 'Journey' voices (equivalent to Chirp/Gemini TTS quality).
    """
    def __init__(self):
        self.api_key = config.GOOGLE_API_KEY
        self.voice_name = getattr(config, 'GOOGLE_AUDIO_VOICE', 'en-US-Journey-D')
        self.voice_name_parable = getattr(config, 'GOOGLE_AUDIO_VOICE_PARABLE', 'en-US-Neural2-D')
        self.language_code = "en-US"
        self.url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"
        
        if not self.api_key:
            print("[!] Warning: No GOOGLE_API_KEY configured for Google TTS.")

    def generate_audio(self, text, output_path, voice_override=None):
        import requests
        import base64
        
        if not self.api_key:
            return False
        
        active_voice = voice_override or self.voice_name
        
        headers = {"Content-Type": "application/json"}
        data = {
            "input": {"text": text},
            "voice": {"languageCode": self.language_code, "name": active_voice},
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 1.2  # Energetic pace for shorts (was 0.97)
            }
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=data)
            
            if response.status_code == 200:
                content = response.json().get("audioContent")
                if content:
                    with open(output_path, "wb") as f:
                        f.write(base64.b64decode(content))
                    return True
            else:
                print(f"    [!] Google TTS Error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"    [!] Google TTS Request Failed: {e}")
            return False

class AudioAgent:
    def __init__(self):
        self.client_manager = ElevenLabsClientManager()
        self.client = None  # Lazy init
        self.voice_id = "nPczCjzI2devNBz1zQrb"  # Brian (ElevenLabs)
        self.model_id = "eleven_multilingual_v2"
        self.pattern = None  # Set by caller for voice selection
        
        # Initialize Google Client if configured
        self.google_client = None
        self.provider = getattr(config, 'AUDIO_PROVIDER', 'elevenlabs')
        
        if self.provider == 'google':
             self.google_client = GoogleTTSClient()

    def _clean_text_for_audio(self, text):
        """
        Normalize text to avoid unwanted TTS pauses and AI artifacts
        while preserving meaning.
        """

        # Remove markdown artifacts
        text = text.replace("*", "").replace("#", "")

        # 1. REMOVE QUOTES (biggest pause trigger)
        text = re.sub(r"[\"'‘’“”]", "", text)

        # 2. Replace em/en dashes with commas (prevents dramatic pause)
        text = re.sub(r"\s*[–—]\s*", ", ", text)

        # 3. Soften semicolons (they cause long pauses)
        text = text.replace(";", ",")

        # 4. Replace parentheticals with spoken equivalents
        text = re.sub(r"\(([^)]+)\)", r", \1,", text)

        # 5. Collapse multiple commas/spaces
        text = re.sub(r",\s*,+", ", ", text)
        text = re.sub(r"\s{2,}", " ", text)

        return text.strip()

    def _ensure_client(self):
        """Ensures client is initialized."""
        if self.client is None:
            self.client = self.client_manager.get_client()
        return self.client is not None
    
    def _try_switch_to_backup(self):
        """Attempts to switch to backup API key."""
        if self.client_manager.switch_to_backup():
            self.client = self.client_manager.get_client()
            return True
        return False
    
    def _get_duration(self, path):
        """Get audio duration using MoviePy."""
        try:
            try:
                from moviepy.editor import AudioFileClip
            except ImportError:
                from moviepy.audio.io.AudioFileClip import AudioFileClip
            clip = AudioFileClip(path)
            dur = clip.duration
            if hasattr(clip, 'close'): clip.close()
            return dur
        except:
            return 5.0  # Default fallback
    
    def _generate_audio_file(self, text, path):
        """
        Generate single audio file with failover support.
        Returns path if successful, None otherwise.
        Priority: Google TTS (if configured) -> ElevenLabs (Primary) -> ElevenLabs (Backup)
        """
        # Skip if exists
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            return path
        
        # Clean text for better prosody
        text = self._clean_text_for_audio(text)
        
        # 1. Try Google TTS if configured as primary
        if self.provider == 'google' and self.google_client:
            # Use Neural2-D voice for parable pattern (deep baritone)
            voice_override = self.google_client.voice_name_parable if self.pattern == 'parable' else None
            if self.google_client.generate_audio(text, path, voice_override=voice_override):
                return path
            else:
                print("    [!] Google TTS failed. Falling back to ElevenLabs...")
        
        # 2. ElevenLabs Fallback (Standard Logic)
        max_attempts = 2 if self.client_manager.has_backup_available() else 1
        return self._generate_elevenlabs_audio(text, path, max_attempts)

    def _generate_elevenlabs_audio(self, text, path, max_attempts):
        """Helper for ElevenLabs generation loop"""
        # Ensure client is ready
        self._ensure_client()
        
        for attempt in range(max_attempts):
            try:
                if self.client and hasattr(self.client, 'text_to_speech'):
                    audio_generator = self.client.text_to_speech.convert(
                        text=text,
                        voice_id=self.voice_id,
                        model_id=self.model_id
                    )
                    full_audio = b""
                    for chunk in audio_generator:
                        full_audio += chunk
                    
                    with open(path, "wb") as f:
                        f.write(full_audio)
                    
                    return path
                else:
                    # SDK v1 fallback
                    from elevenlabs import generate, save
                    audio = generate(
                        text=text,
                        voice=self.voice_id,
                        model=self.model_id
                    )
                    save(audio, path)
                    return path
                    
            except Exception as e:
                print(f"    [!] ElevenLabs Error: {e}")
                
                # Check if quota error and try failover
                if self.client_manager.is_quota_error(e):
                    print("    [!] Credits exhausted on current API key.")
                    if self._try_switch_to_backup():
                        print("    [*] Retrying with backup key...")
                        continue
                    else:
                        print("    [!] No backup key available.")
                        return None
                else:
                    return None
        
        return None

    def generate_audio(self, script_data, assets_dir):
        """
        Generates audio files via ElevenLabs API.
        Returns list of generated file metadata.
        """
        print("\n[AUDIO AGENT] [LOCKED] VPN REQUIRED FOR ELEVENLABS")
        print("Please ensure your VPN is CONNECTED to a supported region.")

        if not self._ensure_client():
            print("[!] No ElevenLabs API key available.")
            return []

        generated_files = []
        
        # Build section list (supports both finance and psychology structures)
        sections = self._get_sections(script_data)
        
        # Save audio requests file
        self._save_audio_requests(sections, assets_dir)
        
        # Generate each section
        for key, text in sections:
            filename = f"audio_{key}.mp3"
            path = os.path.join(assets_dir, filename)
            
            # Check if exists
            if os.path.exists(path) and os.path.getsize(path) > 1000:
                print(f"Skipping: {filename} (Already exists)")
                dur = self._get_duration(path)
                generated_files.append({
                    "name": filename, 
                    "path": path, 
                    "text": text,
                    "duration": dur,
                    "section": key
                })
                continue
            
            print(f"Generating: {filename}...")
            result = self._generate_audio_file(text, path)
            
            if result and os.path.exists(result):
                dur = self._get_duration(result)
                generated_files.append({
                    "name": filename,
                    "path": result,
                    "text": text,
                    "duration": dur,
                    "section": key
                })
            
            time.sleep(0.5)  # Rate limit protection
            
        print(f"[*] Audio generation complete. {len(generated_files)} files.")
        return generated_files

    def generate_sentence_audio(self, script_data, assets_dir):
        """
        HYBRID APPROACH: Generates one audio file PER SENTENCE for perfect visual sync.
        Returns list of sentence audio metadata with precise durations.
        Includes automatic failover to backup API key if credits exhausted.
        """
        from utils.timing_utils import split_into_sentences
        
        print("\n[AUDIO AGENT] SENTENCE-LEVEL Audio Generation (Hybrid Mode)")
        print("[*] VPN Required for ElevenLabs")
        
        if not self._ensure_client():
            print("[!] No ElevenLabs API key available.")
            return []
        
        all_sentence_audio = []
        global_sentence_idx = 0
        
        # Build ordered section list
        sections = self._get_sections(script_data)
        
        # Save sentence-level requests file
        requests_path = os.path.join(assets_dir, "sentence_audio_requests.txt")
        with open(requests_path, "w", encoding="utf-8") as f:
            f.write("=== SENTENCE-LEVEL AUDIO REQUESTS ===\n")
            f.write(f"Voice: Brian (ElevenLabs)\n\n")
            
            for section_key, section_text in sections:
                # ALWAYS split into proper sentences (~4-5s each)
                sentences = split_into_sentences(section_text)

                f.write(f"SECTION: {section_key.upper()} ({len(sentences)} sentences)\n")
                for si, sent in enumerate(sentences):
                    f.write(f"  {si+1}. {sent}\n")
                f.write("-" * 40 + "\n\n")
        
        print(f"[*] Requests saved to: {requests_path}")
        
        # Generate audio for each sentence
        for section_key, section_text in sections:
            # ALWAYS split into proper sentences (~4-5s each)
            sentences = split_into_sentences(section_text)

            print(f"\n[{section_key.upper()}] {len(sentences)} sentences")
            
            section_audio_files = []
            
            for si, sentence in enumerate(sentences):
                global_sentence_idx += 1
                
                # Filename: audio_hook_01.mp3, audio_hook_02.mp3, etc.
                filename = f"audio_{section_key}_{si+1:02d}.mp3"
                path = os.path.join(assets_dir, filename)
                
                # Check if exists
                if os.path.exists(path) and os.path.getsize(path) > 500:
                    print(f"  [OK] Skipping: {filename} (exists)")
                    duration = self._get_duration(path)
                else:
                    print(f"  Generating: {filename}...")
                    result = self._generate_audio_file(sentence, path)
                    
                    if not result:
                        continue
                    
                    duration = self._get_duration(path)
                
                audio_meta = {
                    "name": filename,
                    "path": path,
                    "text": sentence,
                    "duration": duration,
                    "section": section_key,
                    "sentence_index": si,
                    "global_index": global_sentence_idx - 1
                }
                
                all_sentence_audio.append(audio_meta)
                section_audio_files.append(audio_meta)
                
                # Rate limit protection
                time.sleep(0.3)
            
            # Log section summary
            total_dur = sum(a["duration"] for a in section_audio_files) if section_audio_files else 0
            print(f"  -> {len(section_audio_files)} files, {total_dur:.1f}s total")
        
        print(f"\n[*] Sentence audio complete: {len(all_sentence_audio)} files")
        
        # Log API key usage
        if self.client_manager.current_key_index > 0:
            print(f"[*] Note: Used {self.client_manager.current_key_index + 1} API keys (failover occurred)")
        
        return all_sentence_audio
    
    def _get_sections(self, script_data):
        """
        Extract ordered sections from script data.
        Supports both finance and psychology structures.
        """
        sections = []
        
        # Common hook
        if "hook" in script_data: 
            # Handle both text-only hooks and CFH scenario hooks
            hook_data = script_data["hook"]
            if isinstance(hook_data, dict):
                 text = hook_data.get("text", "")
                 if not text:
                     # Join scenario + twist for audio
                     text = f"{hook_data.get('scenario', '')} {hook_data.get('twist', '')}"
                 sections.append(("hook", text))
        
        # CFH Structure (New)
        if "sections" in script_data:
            if "thesis" in script_data:
                # Handle thesis as a regular section or keep separate? 
                # For audio sync, let's treat it as a distinct block if it has text
                thesis_text = script_data["thesis"].get("text", "")
                if thesis_text:
                    sections.append(("thesis", thesis_text))
                
            for i, sec in enumerate(script_data["sections"]):
                # Handle both new 'text' format and old 'sentences' list format
                text = sec.get("text", "")
                if not text:
                    raw_sentences = sec.get("sentences", [])
                    text = " ".join(raw_sentences)
                
                # Use enumeration for consistent numbering if 'number' is missing
                # Format: section_01, section_02, etc. (1-based index)
                sec_num = sec.get('number', i + 1)
                sections.append((f"section_{sec_num:02d}", text))
                
            if "final_thoughts" in script_data:
                 ft = script_data["final_thoughts"]
                 # Handle new simple 'close' structure vs old 'final_thoughts'
                 text = f"{ft.get('recap', '')} {ft.get('warning', '')} {ft.get('cta', '')}".strip()
                 if not text:
                     # Fallback for new structure which might put text in 'text'
                     text = ft.get("text", "")
                 sections.append(("final_thoughts", text))
            
            # Also handle new 'close' key if 'final_thoughts' wasn't there
            elif "close" in script_data:
                close_data = script_data["close"]
                text = close_data.get("text", "")
                if text:
                    sections.append(("close", text))
            
            return sections

        # Psychology Structure
        if "problem_setup" in script_data: 
            sections.append(("problem_setup", script_data["problem_setup"]["text"]))
        if "science_explanation" in script_data: 
            sections.append(("science_explanation", script_data["science_explanation"]["text"]))
        if "reframe" in script_data: 
            sections.append(("reframe", script_data["reframe"]["text"]))
        if "practical_tools" in script_data:
            for i, tool in enumerate(script_data["practical_tools"]):
                sections.append((f"tool_{i+1:02d}", tool["text"]))
        
        # Finance Structure
        if "context" in script_data: 
            sections.append(("context", script_data["context"]["text"]))
        if "historical_precedents" in script_data:
            for i, h in enumerate(script_data["historical_precedents"]):
                sections.append((f"history_{i+1:02d}", h["text"]))
        if "warning" in script_data: 
            sections.append(("warning", script_data["warning"]["text"]))
        
        # Common close
        if "close" in script_data: 
            sections.append(("close", script_data["close"]["text"], None))
        
        return sections
    
    def _save_audio_requests(self, sections, assets_dir):
        """Save audio requests file for manual backup."""
        requests_path = os.path.join(assets_dir, "audio_requests.txt")
        with open(requests_path, "w", encoding="utf-8") as f:
            f.write("=== AUDIO ASSET REQUESTS ===\n")
            f.write("Voice: Brian (ElevenLabs)\n")
            f.write("Model: eleven_multilingual_v2\n")
            f.write("Save files with EXACT names to this folder.\n\n")
            
            for item in sections:
                # Handle 2-tuple or 3-tuple
                if len(item) == 3:
                    key, text, _ = item
                else:
                    key, text = item
                    
                fname = f"audio_{key}.mp3"
                f.write(f"SECTION: {key.upper()}\n")
                f.write(f"REQUIRED FILENAME: {fname}\n")
                f.write(f"TEXT: {text}\n")
                f.write("-" * 40 + "\n\n")
        
        print(f"[*] Audio requests saved to: {requests_path}")
        print("    (Use this file for manual ElevenLabs generation if API fails)")
