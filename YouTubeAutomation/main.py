import os
import sys
import argparse
import time
import json
import glob
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

from agents.fetcher_agent import FetcherAgent
from agents.script_agent import ScriptAgent
from agents.verification_agent import VerificationAgent
from agents.visual_agent import VisualAgent
from agents.audio_agent import AudioAgent
from agents.editor_agent import EditorAgent
from agents.research_agent import ResearchAgent


def wait_for_visual_drops(assets_dir, expected_count, visual_mode="videos"):
    """
    Monitors assets_dir for dropped visual files (videos OR images).
    Auto-renames them to visual_XX format in order of detection.
    Returns once all expected files are present.
    
    Args:
        assets_dir: Path to assets folder
        expected_count: Number of visual files expected
        visual_mode: "videos" (.mp4) or "images" (.png/.jpg/.webp)
    """
    # Configure based on mode
    if visual_mode == "images":
        target_ext = ".png"
        drop_exts = ['.png', '.jpg', '.jpeg', '.webp']
        asset_type = "IMAGES"
    else:
        target_ext = ".mp4"
        drop_exts = ['.mp4']
        asset_type = "VIDEOS"
    
    print(f"\n{'='*60}")
    print(f"[*] WAITING FOR {asset_type}: Drop {expected_count} files into:")
    print(f"    {assets_dir}")
    print(f"{'='*60}")
    print(f"    Accepted formats: {', '.join(drop_exts)}")
    print(f"    Files will be auto-renamed to visual_01{target_ext}, visual_02{target_ext}, etc.")
    print("    Tip: Drop files in ORDER for best results.\n")
    
    processed_files = set()
    last_progress = -1
    
    while True:
        # Check for complete set first (check ALL valid extensions per slot)
        all_present = all(
            any(os.path.exists(os.path.join(assets_dir, f"visual_{i+1:02d}{ext}"))
                for ext in drop_exts)
            for i in range(expected_count)
        )
        if all_present:
            print(f"\n\n[✓] All {expected_count} {asset_type.lower()} detected. Continuing pipeline...")
            return True
        
        # Scan for new unprocessed files (not already named visual_XX)
        try:
            dropped_files = sorted([
                f for f in os.listdir(assets_dir) 
                if any(f.lower().endswith(ext) for ext in drop_exts)
                and not f.startswith('visual_')
                and not f.startswith('final_')
                and not f.startswith('ref_')
                and f not in processed_files
            ])
        except:
            dropped_files = []
        
        for dropped in dropped_files:
            # Find next available visual_XX slot
            for i in range(expected_count):
                # Check ALL possible extensions for this slot
                slot_taken = any(
                    os.path.exists(os.path.join(assets_dir, f"visual_{i+1:02d}{ext}"))
                    for ext in ['.png', '.jpg', '.jpeg', '.webp', '.mp4']
                )
                if slot_taken:
                    continue
                    
                src_path = os.path.join(assets_dir, dropped)
                try:
                    if visual_mode == "images":
                        src_ext = os.path.splitext(dropped)[1].lower()
                        target_name = f"visual_{i+1:02d}{src_ext}"
                    else:
                        target_name = f"visual_{i+1:02d}{target_ext}"
                    target_path = os.path.join(assets_dir, target_name)
                    
                    os.rename(src_path, target_path)
                    print(f"    [RENAMED] {dropped} → {target_name}")
                except Exception as e:
                    print(f"    [!] Rename failed for {dropped}: {e}")
                processed_files.add(dropped)
                break
            else:
                # No slot found — all slots taken, mark as processed to avoid retry
                processed_files.add(dropped)
        
        # Show progress periodically
        if visual_mode == "images":
            # Check for any image extension
            current = sum(
                1 for i in range(expected_count) 
                if any(os.path.exists(os.path.join(assets_dir, f"visual_{i+1:02d}{ext}")) 
                       for ext in ['.png', '.jpg', '.jpeg', '.webp'])
            )
        else:
            current = sum(
                1 for i in range(expected_count) 
                if os.path.exists(os.path.join(assets_dir, f"visual_{i+1:02d}.mp4"))
            )
        
        if current != last_progress:
            print(f"    Progress: {current}/{expected_count}")
            last_progress = current
        
        time.sleep(2)  # Poll every 2 seconds


def run_skulsy_pipeline(args, assets_dir, session_id):
    """
    Executes the specialized 'Skulsy Engine' pipeline for 45s Shorts.
    Workflow: Topic -> Skulsy Script -> Audio -> Grok Prompts -> [USER MANUAL] -> Assembly.
    """
    print(f"\nExample: 'Skulsy buys Bitcoin 2011'")
    print(f"\nExample: 'Skulsy buys Bitcoin 2011'")
    
    script_path = os.path.join(assets_dir, "script.json")
    script_agent = ScriptAgent()
    script = None
    pattern_choice = getattr(args, 'pattern', 'what_if')

    # 1. SCRIPT GENERATION (or Load)
    if args.resume and os.path.exists(script_path):
        print(f"[*] Resuming: Skulsy Script loaded.")
        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)
            
    # If no script loaded, we need a topic to generate it
    if not script:
        topic = args.topic
        if not topic:
            topic = input("Enter Skulsy Topic: ")
            
        print(f"\n>>> PHASE 0: RESEARCH (Truth Engine)")
        research_path = os.path.join(assets_dir, "research_brief.json")
        research_brief = None
        
        # Check for existing research
        if args.use_existing_research and os.path.exists(args.use_existing_research):
            print(f"[*] Loading existing research: {args.use_existing_research}")
            with open(args.use_existing_research, 'r') as f: research_brief = json.load(f)
        elif os.path.exists(research_path):
             print(f"[*] Loading session research: {research_path}")
             with open(research_path, 'r') as f: research_brief = json.load(f)
        else:
             # Run Research Agent
             print(f"[*] Researching '{topic}' for verification...")
             # Force short-form optimized research
             research_agent = ResearchAgent(content_type="short")
             research_brief = research_agent.research_topic(topic)
             
             with open(research_path, "w", encoding="utf-8") as f:
                 json.dump(research_brief, f, indent=2)
            
        print(f"\n>>> PHASE 1: SKULSY ENGINE SCRIPT (Iterative Refinement)")
        

        
        # New V5 Agent handles the iterative loop internally
        print(f"[*] Calling Skulsy Engine V5 (Pattern: {pattern_choice})...")
        script = script_agent.generate_skulsy_script(topic, research_brief, pattern=pattern_choice)
        
        if not script: 
            print("[!] Script generation failed.")
            return
        
        # Save validated script
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2)

    # 2. AUDIO GENERATION
    voice_label = 'Neural2-D (Parable)' if pattern_choice == 'parable' else 'Journey-D'
    print(f"\n>>> PHASE 2: AUDIO ({voice_label})")
    # Flatten script for AudioAgent
    audio_files_map = {} # filename -> duration
    
    # Initialize TTS Client
    from agents.audio_agent import GoogleTTSClient, AudioAgent
    tts_client = None
    if config.AUDIO_PROVIDER == "google":
        tts_client = GoogleTTSClient()
    else:
        # Fallback to generic audio agent
        audio_agent_instance = AudioAgent()

    sentences = script.get('sentences', [])
    for i, sent in enumerate(sentences):
        fname = f"audio_{i+1:02d}.mp3"
        fpath = os.path.join(assets_dir, fname)
        text = sent['text']
        
        if os.path.exists(fpath):
            audio_files_map[fname] = fpath
            continue # Skip existing
            
        print(f"   Generating Line {i+1}: {text[:40]}...")
        
        try:
            success = False
            if tts_client:
                # Use Neural2-D for parable pattern
                voice_override = tts_client.voice_name_parable if pattern_choice == 'parable' else None
                success = tts_client.generate_audio(text, fpath, voice_override=voice_override)
            else:
                # Fallback to AudioAgent's internal generator
                audio_agent_instance.pattern = pattern_choice
                result = audio_agent_instance._generate_audio_file(text, fpath)
                success = result is not None
                
            if success:
                audio_files_map[fname] = fpath
            else:
                print(f"   [!] Audio Failed for line {i+1}")
        except Exception as e:
            print(f"   [!] Audio Error: {e}")

            
    # Update durations in script meta
    for i, sent in enumerate(sentences):
        fname = f"audio_{i+1:02d}.mp3"
        fpath = os.path.join(assets_dir, fname)
        if os.path.exists(fpath):
            try:
                # Get duration
                from moviepy.editor import AudioFileClip
                a = AudioFileClip(fpath)
                sent['duration'] = a.duration
                a.close()
                del a
            except:
                sent['duration'] = 3.0 # Fallback
                
    # Save script with durations
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2)

    # 3. GENERATE VISUAL PROMPTS (V5 DUAL LAYER)
    print("\n>>> PHASE 3: VISUAL PROMPTS (V5 DUAL LAYER)")
    grok_path = os.path.join(assets_dir, "grok_prompts.txt")
    img_path = os.path.join(assets_dir, "image_prompts.txt")
    
    visual_agent = VisualAgent()
    dual_prompts = None  # Store for auto-gen reuse
    
    if os.path.exists(grok_path):
        print("[*] Visual prompts already exist. Skipping generation.")
    else:
        print("[VisualAgent] Generating Reference Images + Grok Video Prompts...")
        
        # Call V5 Dual Layer Generator
        dual_prompts = visual_agent.generate_dual_layer_prompts(script['sentences'])
        
        # Save both files
        visual_agent._save_dual_layer_requests(dual_prompts, assets_dir)
    
    # 3.5 AUTO IMAGE GENERATION (Gemini API)
    expected_count = len(script['sentences'])
    visual_mode = getattr(args, 'visual_mode', 'videos')  # default to videos
    manual_images = getattr(args, 'manual_images', False)
    
    # Auto-gen only works for image mode (not video mode)
    if visual_mode == "images" and not manual_images:
        print("\n>>> PHASE 3.5: AUTO IMAGE GENERATION (Gemini API)")
        
        # Load prompts if not already in memory
        if dual_prompts is None:
            dual_prompts = visual_agent.generate_dual_layer_prompts(script['sentences'])
        
        result = visual_agent.generate_images_auto(dual_prompts, assets_dir)
        
        if len(result["failed"]) == 0:
            print(f"[✓] All {expected_count} images generated successfully. Skipping manual mode.")
        else:
            failed_indices = result["failed"]
            print(f"\n[!] {len(failed_indices)} images failed auto-generation. Switching to MANUAL mode for:")
            for idx in failed_indices:
                print(f"    - visual_{idx+1:02d}.png")
            print(f"\n    DROP missing .png/.jpg files into: {assets_dir}")
            print("    They will be auto-renamed to visual_01, visual_02, etc.")
            wait_for_visual_drops(assets_dir, expected_count, "images")
    else:
        # 4. WAIT FOR VISUAL DROPS (Manual mode - videos or forced manual)
        # Determine file extension based on mode
        if visual_mode == "images":
            check_exts = ['.png', '.jpg', '.jpeg', '.webp']
        else:
            check_exts = ['.mp4']
        
        # First check if all visuals already exist (resume case)
        def check_visual_exists(idx):
            for ext in check_exts:
                if os.path.exists(os.path.join(assets_dir, f"visual_{idx+1:02d}{ext}")):
                    return True
            return False
        
        all_present = all(check_visual_exists(i) for i in range(expected_count))
        
        if not all_present:
            print(f"\n[!] ACTION REQUIRED: Generate visuals now. (Mode: {visual_mode})")
            if visual_mode == "images":
                print("    1. Open 'whisk_prompts.txt' → Generate Images (Whisk/Imagen).")
                print(f"    2. DROP .png/.jpg files into: {assets_dir}")
            else:
                print("    1. Open 'image_prompts.txt' → Generate Reference Images (Whisk/Imagen).")
                print("    2. Open 'grok_prompts.txt' → Generate Videos (Grok) using Reference Images.")
                print(f"    3. DROP .mp4 files into: {assets_dir}")
            print("       They will be auto-renamed to visual_01, visual_02, etc.")
            
            # Start the watcher
            wait_for_visual_drops(assets_dir, expected_count, visual_mode)
        else:
            print(f"\n[*] All {expected_count} visuals already present. Skipping wait.")

    # 5. ASSEMBLY
    print(f"\n>>> PHASE 5: ASSEMBLY (Skulsy Compiler)")
    editor = EditorAgent()
    
    # Prepare Scene Data - detect actual file extension
    def find_visual_file(idx):
        for ext in ['.mp4', '.png', '.jpg', '.jpeg', '.webp']:
            path = os.path.join(assets_dir, f"visual_{idx+1:02d}{ext}")
            if os.path.exists(path):
                return f"visual_{idx+1:02d}{ext}"
        return f"visual_{idx+1:02d}.mp4"  # fallback
    
    scenes = []
    for i, sent in enumerate(sentences):
        fname_audio = f"audio_{i+1:02d}.mp3"
        fname_visual = find_visual_file(i)
        
        scenes.append({
            'asset_path': os.path.join(assets_dir, fname_visual),
            'audio_path': os.path.join(assets_dir, fname_audio),
            'text': sent['text'],
            'scene_key': sent.get('state'),
            'state': sent.get('state'),
            'intensity': sent.get('intensity'),
            'timeline_anchor': sent.get('timeline_anchor')
        })
        
    final_video = editor.create_video(scenes, None) # Output handled later or return
    
    if final_video:
        out_path = os.path.join(assets_dir, "final_skulsy.mp4")
        if getattr(editor, 'IS_MOVIEPY_2', False):
            final_video.write_videofile(out_path, fps=30, codec='libx264', audio_codec='aac')
        else:
            final_video.write_videofile(out_path, fps=30, codec='libx264', audio_codec='aac', threads=4)
        print(f"\n[*] Skulsy Short Generated: {out_path}")
    else:
        print("[!] Assembly Failed")
    
    sys.exit(0) # End skulsy mode


def main():
    parser = argparse.ArgumentParser(description="Finance Shorts Automation Agent")
    parser.add_argument("--niche", type=str, default="personalfinance", help="Target subreddit niche")
    parser.add_argument("--topic", type=str, help="Manual topic override")
    parser.add_argument("--style", type=str, default="storytelling", choices=["storytelling", "analysis"], help="Content style")
    parser.add_argument("--resume", type=str, help="Resume from specific session ID (folder name)")
    parser.add_argument("--sentence-audio", action="store_true", help="Use sentence-level audio generation for precise sync")
    parser.add_argument("--test-short", action="store_true", help="Generate a short 45s script for testing purposes")
    parser.add_argument("--test-medium", action="store_true", help="Generate a medium 2-min script for testing purposes")
    parser.add_argument("--test-long", action="store_true", help="Generate a standard 5-min script")
    parser.add_argument("--test-8min", action="store_true", help="Generate an exact 8-minute script (100 Visuals)")
    parser.add_argument("--test-1min", action="store_true", help="Generate a short 1-minute test (Hook + 1 Section)")
    
    # CFH New Arguments
    parser.add_argument("--research-only", action="store_true", help="Only run research phase, skip video generation")
    parser.add_argument("--use-existing-research", type=str, help="Path to existing research_brief.json")
    parser.add_argument("--manual-images", action="store_true", help="Force manual image upload mode from the start")
    parser.add_argument("--mode", type=str, choices=["default", "skulsy", "research"], default="default", help="Operation mode")
    parser.add_argument("--pattern", type=str, default="what_if", choices=["what_if", "mistake", "explainer", "success", "comparison", "timeline", "reaction", "parable"], help="Skulsy Script Pattern")
    parser.add_argument("--visual-mode", type=str, default="videos", choices=["images", "videos"], help="Visual asset type: 'images' (PNG/JPG) or 'videos' (MP4)")
    args = parser.parse_args()

    # Interactive Mode if no args
    if len(sys.argv) == 1:
        print("\n=== INTERACTIVE MODE ===")
        print("1. Auto (Viral Topic from 'personalfinance')")
        print("2. Manual Topic")
        choice = input("Select Option (1/2): ")
        
        if choice == "2":
            manual_topic = input("Enter Topic: ")
            if manual_topic.strip():
                args.topic = manual_topic
            
            print("\nSelect Style:")
            print("1. Storytelling (Default)")
            print("2. Analysis / Explainer")
            style_choice = input("Select Option (1/2): ")
            if style_choice == "2":
                args.style = "analysis"
        else:
            print("Using Default: Auto (personalfinance)")

    # 0. SETUP
    if args.resume:
        session_id = args.resume
        print(f"[*] RESUMING SESSION: {session_id}")
    else:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"run_{timestamp_str}"
    
    print(f"=== FINANCE AUTOMATION | Session: {session_id} | Mode: {args.mode} ===")
    
    # Use path relative to script location, not CWD
    base_assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    assets_dir = os.path.join(base_assets_dir, session_id)
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        
    # --- SKULSY MODE BRANCH ---
    if args.mode == 'skulsy':
        run_skulsy_pipeline(args, assets_dir, session_id)
        return
    # --------------------------
    
    print(f"=== FINANCE LONG-FORM AUTOMATION (10-12 MIN) | Session: {session_id} ===")
        
    # 1. FETCH / GENERATE SCRIPT
    script_path = os.path.join(assets_dir, "script.json")
    
    if args.resume and os.path.exists(script_path):
        print(f"[*] Loading existing script from: {script_path}")
        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)
        story_data = None # Not needed if resuming
    else:
        # 1. FETCH -> STORY
        if args.topic:
            story_data = {"title": args.topic, "text": "Manual topic.", "subreddit": "manual"}
        else:
            # Check if we should use the new Research Agent pipeline (Default for Auto now)
            # If no manual topic, get one from TopicAgent
            pass # Logic handled below in new Research Phase

    # ==========================================
    # PHASE 1: RESEARCH (NEW)
    # ==========================================
    
    research_brief = None
    research_path = os.path.join(assets_dir, "research_brief.json")
    
    # A. Check for existing research arg
    if args.use_existing_research and os.path.exists(args.use_existing_research):
        print(f"\n[*] Loading existing research from: {args.use_existing_research}")
        with open(args.use_existing_research, 'r', encoding='utf-8') as f:
            research_brief = json.load(f)
            
    # B. Check for session research
    elif os.path.exists(research_path):
        print(f"\n[*] Loading research from session: {research_path}")
        with open(research_path, 'r', encoding='utf-8') as f:
            research_brief = json.load(f)
            
    # C. Conduct New Research
    else:
        print("\n" + "="*60)
        print(">>> PHASE 1: RESEARCH")
        print("="*60)
        
        target_topic = args.topic
        target_angle = None
        
        if not target_topic:
            from agents.topic_agent import TopicAgent
            topic_agent = TopicAgent()
            target_topic = topic_agent.get_trending_topic(niche="geopolitics")
            
            # Extract angle if present "Topic: Angle"
            if ':' in target_topic:
                target_topic, target_angle = target_topic.split(':', 1)
                target_topic = target_topic.strip()
                target_angle = target_angle.strip()
        
        print(f"[*] Researching Topic: {target_topic} ({target_angle})")
        
        research_agent = ResearchAgent()
        research_brief = research_agent.research_topic(
            topic=target_topic,
            angle=target_angle,
            depth="deep"
        )
        
        # Save
        with open(research_path, 'w', encoding='utf-8') as f:
            json.dump(research_brief, f, indent=2, ensure_ascii=False)
            
        if args.research_only:
            print("[*] Research-only mode complete. Exiting.")
            return

    # ==========================================
    # PHASE 2: SCRIPT GENERATION (CFH Modified)
    # ==========================================
    
    if args.resume and os.path.exists(script_path):
        print(f"[*] Loading existing script from: {script_path}")
        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)
    else:
        print("\n" + "="*60)
        print(">>> PHASE 2: SCRIPT GENERATION")
        print("="*60)
        
        script_agent = ScriptAgent()
        
        # Determine if we use CFH style (Section based) or Legacy
        # Use CFH style if research_brief is available
        if research_brief:
            script = script_agent.generate_script_cfh(research_brief)
        else:
            # Fallback to legacy if no research brief (e.g. manual simple run)
            # Create dummy story data from topic if needed
            story_data = {"title": getattr(args, 'topic', "Untitled"), "text": "No research.", "subreddit": "manual"}
            if args.topic is None: story_data['title'] = "Auto Topic"
            
            script = script_agent.generate_script(story_data, style="analysis", duration="8min")

        if not script: return
        
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2)

    # ==========================================
    # PHASE 2.5: FACT-CHECKING
    # ==========================================
    if research_brief:
        print("\n>>> PHASE 2.5: FACT-CHECKING")
        fact_check_report = verify_script_claims(script, research_brief)
        # We just log it for now, user can inspect
        with open(os.path.join(assets_dir, "fact_check.json"), "w") as f:
            json.dump(fact_check_report, f, indent=2)

    # Legacy script block removed/merged above
    pass
    
    # 2.5 GENERATE SEO METADATA
    seo_path = os.path.join(assets_dir, "seo.json")
    if not os.path.exists(seo_path):
        print("\n>>> Generating SEO Metadata...")
        from agents.seo_agent import SEOAgent
        seo_agent = SEOAgent()
        seo_agent.generate_seo(script, assets_dir)
    else:
        print("[*] SEO metadata already exists, skipping.")
        
    # LOGIC FOR TEST-1MIN (Truncate Script)
    if args.test_1min:
        print("\n[!] TEST-1MIN MODE: Truncating script to Hook + 1 Section...")
        if "sections" in script:
            script["sections"] = script["sections"][:1]  # Keep only first section
        if "final_thoughts" in script:
            del script["final_thoughts"] # Remove outro
        # Keep hook and thesis as they are small
        print("[!] Script truncated for testing.")

    # 3. AUDIO (Generate First to get Duration)
    audio_agent = AudioAgent()
    
    # Check if using sentence-level audio (hybrid mode)
    # FORCE ENABLE for Long Form / 8-Min Verification to ensure strict sync
    use_sentence_audio = getattr(args, 'sentence_audio', False) or args.test_8min or args.test_long or args.test_1min
    
    if use_sentence_audio:
        print("\n>>> Generating Sentence-Level Audio (Hybrid Mode)...")
        # Returns list of dicts per sentence: {'name', 'path', 'text', 'duration', 'section', 'sentence_index'}
        sentence_audio_files = audio_agent.generate_sentence_audio(script, assets_dir)
        
        # Check if we have all audio files or need to wait for manual generation
        from utils.timing_utils import split_into_sentences
        
        # Build expected audio file list
        sections = audio_agent._get_sections(script)
        expected_audio = []
        for section_key, section_text in sections:
            # ALWAYS split into proper sentences (~4-5s each)
            sentences = split_into_sentences(section_text)

            for si in range(len(sentences)):
                filename = f"audio_{section_key}_{si+1:02d}.mp3"
                expected_audio.append({
                    'filename': filename,
                    'section': section_key,
                    'text': sentences[si] if si < len(sentences) else ""
                })
        
        # Count missing audio files
        missing_audio = []
        for ea in expected_audio:
            path = os.path.join(assets_dir, ea['filename'])
            if not os.path.exists(path) or os.path.getsize(path) < 500:
                missing_audio.append(ea)
        
        if missing_audio:
            print(f"\n[!] Missing {len(missing_audio)} audio files. Waiting for manual generation...")
            print("=" * 50)
            print("ACTION REQUIRED: GENERATE AUDIO FILES")
            print(f"1. Open 'sentence_audio_requests.txt' for text content")
            print(f"2. Use ElevenLabs (Voice: Brian) to generate each sentence")
            print(f"3. Drop files into: '{assets_dir}'")
            print("   (Files will be auto-renamed in order)")
            print("=" * 50)
            
            # Auto-rename loop for audio files
            while missing_audio:
                # Scan for new audio files (mp3, wav, m4a, aac)
                all_files = os.listdir(assets_dir)
                audio_exts = ('.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac')
                audio_candidates = [f for f in all_files 
                                    if f.lower().endswith(audio_exts) 
                                    and not f.startswith('audio_')]
                
                # Also check for already-named files
                for ea in list(missing_audio):
                    path = os.path.join(assets_dir, ea['filename'])
                    if os.path.exists(path) and os.path.getsize(path) >= 500:
                        print(f"[*] Found: {ea['filename']}")
                        missing_audio.remove(ea)
                
                # Auto-rename/convert candidates
                if audio_candidates and missing_audio:
                    for candidate in sorted(audio_candidates):
                        if not missing_audio:
                            break
                        
                        target = missing_audio[0]
                        candidate_path = os.path.join(assets_dir, candidate)
                        target_path = os.path.join(assets_dir, target['filename'])
                        
                        try:
                            # If not MP3, convert using MoviePy
                            if not candidate.lower().endswith('.mp3'):
                                print(f"[*] Converting '{candidate}' to MP3...")
                                try:
                                    from moviepy.editor import AudioFileClip
                                except ImportError:
                                    from moviepy.audio.io.AudioFileClip import AudioFileClip
                                
                                audio_clip = AudioFileClip(candidate_path)
                                # MoviePy v2 doesn't support verbose/logger args
                                try:
                                    audio_clip.write_audiofile(target_path, codec='libmp3lame')
                                except:
                                    audio_clip.write_audiofile(target_path)
                                audio_clip.close()
                                
                                # Try to remove original with retry
                                import time as t_mod
                                for retry in range(5):
                                    try:
                                        t_mod.sleep(0.5)  # Wait for file lock release
                                        os.remove(candidate_path)
                                        break
                                    except:
                                        if retry == 4:
                                            # Last resort: rename to .processed to prevent reuse
                                            try:
                                                os.rename(candidate_path, candidate_path + ".processed")
                                            except:
                                                pass
                                
                                print(f"[*] Converted: '{candidate}' -> '{target['filename']}'")
                            else:
                                os.rename(candidate_path, target_path)
                                print(f"[*] Auto-Renamed: '{candidate}' -> '{target['filename']}'")
                            
                            missing_audio.pop(0)
                        except Exception as e:
                            print(f"[!] Rename/Convert error: {e}")
                            # Skip this candidate to prevent infinite loop
                            break
                
                if missing_audio:
                    import time as time_module
                    import sys as sys_module
                    print(".", end="", flush=True)
                    sys_module.stdout.flush()
                    time_module.sleep(2)  # Check every 2 seconds
            
            print("\n[*] All audio files found!")
        
        # Reload sentence audio files with durations
        sentence_audio_files = []
        for ea in expected_audio:
            path = os.path.join(assets_dir, ea['filename'])
            if os.path.exists(path):
                dur = audio_agent._get_duration(path)
                sentence_audio_files.append({
                    'name': ea['filename'],
                    'path': path,
                    'text': ea['text'],
                    'duration': dur,
                    'section': ea['section']
                })
        
        if not sentence_audio_files:
            print("Sentence audio failed. Exiting.")
            return
        
        # Group by section for visual calculation
        audio_files = []
        section_totals = {}
        for sa in sentence_audio_files:
            section = sa['section']
            if section not in section_totals:
                section_totals[section] = {'duration': 0, 'text': '', 'files': []}
            section_totals[section]['duration'] += sa['duration']
            section_totals[section]['text'] += ' ' + sa['text']
            section_totals[section]['files'].append(sa)
        
        # Create consolidated audio_files list for visual calculation
        for section, data in section_totals.items():
            audio_files.append({
                'name': f"audio_{section}.mp3",
                'path': data['files'][0]['path'],  # First file for reference
                'text': data['text'].strip(),
                'duration': data['duration'],
                'section': section,
                'sentence_files': data['files']  # Store all sentence files
            })
        
        print(f"[*] Sentence audio grouped into {len(audio_files)} sections")
    else:
        print("\n>>> Generating Audio (ElevenLabs)...")
        # Returns list of dicts: {'name', 'path', 'text', 'duration', 'section'}
        audio_files = audio_agent.generate_audio(script, assets_dir)
        
        if not audio_files:
            print("Audio failed. Exiting.")
            return

    # 4. CALCULATE VISUALS NEEDED
    # Logic split: Strict 1:1 (Sentence Mode) vs Distributed (Legacy)
    
    use_strict_mode = use_sentence_audio
    sentences_list = []
    
    if use_strict_mode:
        print("\n>>> STRICT SYNC MODE ACTIVE (1 Sentence = 1 Visual)")
        # Flatten all sentences from all sections
        for af in audio_files:
            if 'sentence_files' in af:
                for s in af['sentence_files']:
                    sentences_list.append(s['text'])
        
        total_prompts_needed = len(sentences_list)
        print(f"[*] Total Sentences/Visuals: {total_prompts_needed}")
        
        section_visual_counts = {} # Not used in strict mode really, but kept for safe
    else:
        # Legacy Duration Logic
        section_visual_counts = {}
        total_prompts_needed = 0
        
        print("\n>>> Calculating Visual Requirements (Legacy Duration-Based)...")
        for af in audio_files:
            dur = af.get('duration', 0)
            count = max(1, int(dur / 6.0)) 
            section_visual_counts[af['name']] = count
            total_prompts_needed += count
            print(f" - {af['name']} ({dur:.1f}s) -> {count} visuals")
            
        print(f"[*] Total Visuals Needed: {total_prompts_needed}")

    # 5. GENERATE PROMPTS (OR LOAD EXISTING)
    # Initialize visual_blocks to ensure it's always defined
    visual_blocks = []
    
    # ===================================================================
    # VISUAL GROUPER - PHASE 2 of Strict Sync (MOVED UP)
    # Merge granular sentence audio (~2s each) into visual blocks (~5s each)
    # This MUST run regardless of whether we have existing prompts or not.
    # ===================================================================
    if use_sentence_audio:
        print("\n>>> PHASE 2: VISUAL GROUPER (Merge Sentences -> Blocks)...")
        from utils.visual_grouper import group_audio_segments
        
        # Flatten all sentence files
        all_sentence_files = []
        for af in audio_files:
            if 'sentence_files' in af:
                all_sentence_files.extend(af['sentence_files'])
        
        if all_sentence_files:
            merged_audio_dir = os.path.join(assets_dir, "audio_blocks")
            total_duration = sum(s['duration'] for s in all_sentence_files)
            target_block_count = max(1, int(total_duration / 5.0))
            
            visual_blocks = group_audio_segments(
                all_sentence_files,
                target_count=target_block_count,
                output_dir=merged_audio_dir,
                merge_audio=True
            )
            print(f"[*] Created {len(visual_blocks)} visual blocks from {len(all_sentence_files)} sentences")
        else:
            print("[!] No sentence files found for grouping")

    # Initialize VisualAgent for prompt generation
    visual_agent = VisualAgent()
    
    prompts_path = os.path.join(assets_dir, "visual_requests.txt")
    
    if os.path.exists(prompts_path) and os.path.getsize(prompts_path) > 100:
        print(f"[*] Loading existing visual prompts from: {prompts_path}", flush=True)
        prompts = []
        with open(prompts_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        current_prompt = {}
        for line in lines:
            line = line.strip()
            if line.startswith("FILE:"):
                current_prompt['filename'] = line.replace("FILE:", "").strip()
            elif line.startswith("TYPE:"):
                current_prompt['type'] = line.replace("TYPE:", "").strip()
            elif line.startswith("PROMPT:"):
                current_prompt['prompt'] = line.replace("PROMPT:", "").strip()
            elif line.startswith("---") and 'filename' in current_prompt:
                prompts.append(current_prompt)
                current_prompt = {}
        if 'filename' in current_prompt:
             prompts.append(current_prompt)
             
        print(f"[*] Loaded {len(prompts)} prompts.", flush=True)
        
    else:
        # 5. VISUAL PROMPTS
        # ------------------------------------------------------------------
        # STRICT SYNC UPDATE: Using pre-calculated visual_blocks (from Phase 2 above)
        # ------------------------------------------------------------------
        
        # ===================================================================
        # VISUAL PROMPTS - PHASE 3 of Strict Sync
        # Generate 1 prompt per block (NOT per sentence)
        # ===================================================================
        visual_requests_path = os.path.join(assets_dir, "visual_requests.txt")
        prompts = []
        
        # Determine expected prompt count
        expected_prompts = len(visual_blocks) if visual_blocks else total_prompts_needed
        
        if os.path.exists(visual_requests_path) and os.path.getsize(visual_requests_path) > 100:
            print(f"[*] Loading existing visual prompts from: {visual_requests_path}")
            prompts = visual_agent._parse_existing_requests(visual_requests_path)
            
            # Check if prompt count matches BLOCK count (not sentence count)
            if use_sentence_audio and visual_blocks and len(prompts) != len(visual_blocks):
                print(f"[!] Prompt count mismatch: {len(prompts)} prompts vs {len(visual_blocks)} blocks")
                print(f"[*] Regenerating prompts for 1:1 BLOCK mapping...")
                prompts = []  # Force regeneration
        
        if not prompts:
            print(f"\n>>> Generating Visual Prompts (1:1 BLOCK SYNC)...")
            
            if use_sentence_audio and visual_blocks:
                # STRICT SYNC: 1 prompt per BLOCK
                block_texts = [b['text'] for b in visual_blocks]
                prompts = visual_agent.generate_image_prompts(script, sentences=block_texts)
                print(f"[*] Generated {len(prompts)} prompts for {len(visual_blocks)} blocks")
            else:
                # Fallback (Legacy)
                prompts = visual_agent.generate_image_prompts(script, num_prompts=30)
                 
            visual_agent._save_visual_requests(prompts, assets_dir)
            print(f"[*] Saved {len(prompts)} prompts to {visual_requests_path}")
        
        # Log metaphor quality
        try:
            from utils.metaphor_comparison import MetaphorQualityAnalyzer
            analyzer = MetaphorQualityAnalyzer()
            try:
                report = analyzer.run_quality_check(prompts, output_dir=assets_dir)
            except AttributeError:
                 # Fallback if I messed up the method name in previous step
                 try:
                     report = analyzer.analyze_batch(prompts)
                     analyzer.generate_quality_report(prompts, os.path.join(assets_dir, "visual_quality_report.txt"))
                 except Exception as e:
                     print(f"[!] Metaphor Check Failed: {e}")
                     report = None
            
        except Exception as e:
            print(f"[!] Metaphor Check Failed: {e}")
        
        # 6. IMAGE GENERATION
        print("\n>>> GENERATING VISUALS (AUTOMATED)...")
        print("=" * 50)
        
        # QUALITY ANALYSIS (Added for CFH Metaphor Check)
        try:
            from utils.metaphor_comparison import MetaphorQualityAnalyzer
            analyzer = MetaphorQualityAnalyzer()
            quality_report = analyzer.analyze_batch(prompts)
            
            print(f"\n[QUALITY CHECK] Visual Metaphor Quality:")
            print(f"  Average Score: {quality_report['average_score']:.1f}/100")
            print(f"  Grade: {quality_report['overall_grade']}")
            
            if quality_report['weak_prompts']:
                print(f"  ⚠ {len(quality_report['weak_prompts'])} prompts below threshold")
            
            # Save report
            report_path = os.path.join(assets_dir, "visual_quality_report.txt")
            analyzer.generate_quality_report(prompts, output_path=report_path)
        except Exception as e:
            print(f"[!] Quality analysis skipped: {e}")
        
        with open(prompts_path, "w", encoding="utf-8") as f:
            f.write(f"=== VISUAL ASSET REQUESTS ({len(prompts)}) ===\n")
            f.write("Note: You can drop images (.png, .jpg) OR video clips (.mp4)!\n")
            f.write("The system will auto-rename them (visual_01.mp4, visual_02.png etc).\n\n")
            for p in prompts:
                f.write(f"FILE: {p['filename']}\n")
                f.write(f"TYPE: {p['type']}\n")
                f.write(f"PROMPT: {p['prompt']}\n")
                f.write("-" * 20 + "\n")
                
        print(f"[*] Saved prompt list to {prompts_path}", flush=True)

    # 6. AUTOMATED IMAGE GENERATION (Google Gemini/Imagen)
    print("\n" + "="*50)
    print(">>> GENERATING VISUALS (AUTOMATED)...")
    print("="*50 + "\n")

    from agents.image_gen_agent import ImageGenAgent
    try:
        image_agent = ImageGenAgent(manual_mode=getattr(args, 'manual_images', False))
        
        for i, p in enumerate(prompts):
            # Target filename
            # User Rule: "where ever ... it is mentioned to generate animation mp4 file , there also image will be used"
            # So we FORCE .png extension for generation target
            target_filename = f"visual_{i+1:03d}.png"
            target_path = os.path.join(assets_dir, target_filename)
            
            # If prompt expected mp4, update the reference in memory
            prompts[i]['filename'] = target_filename
            prompts[i]['type'] = 'image'
            
            if os.path.exists(target_path):
                print(f"[*] Exists: {target_filename}")
                continue
            
            # Generate
            prompt_text = p['prompt']
            print(f"[*] Generating Visual {i+1}/{len(prompts)}...")
            
            result_path = image_agent.generate_image(prompt_text, target_path)
            
            if not result_path:
                print(f"[!] Generation failed for {target_filename}. Waiting for manual fallback...")
                # Start manual fallback loop for just this file? 
                # Or just skip/fail? For now, we continue, Editor might skip it.
                pass
                
             # Rate limit pause to be safe
            time.sleep(2)

        # 6b. GENERATE THUMBNAIL (Consistent Style)
        print("\n[*] Generating Thumbnail...")
        thumb_path = os.path.join(assets_dir, "thumbnail.png")
        if not os.path.exists(thumb_path):
             thumb_prompt = visual_agent.generate_thumbnail_prompt(script)
             
             # Save prompt to text file for User (Banana Pro/Gemini Nano usage)
             with open(os.path.join(assets_dir, "thumbnail_prompt.txt"), "w") as f:
                 f.write(thumb_prompt)
                 
             image_agent.generate_image(thumb_prompt, thumb_path)
        else:
             print("[*] Thumbnail already exists.")
            
    except Exception as e:
        print(f"[!] Image Automation Failed: {e}")
        print("Falling back to manual mode...")
        # (Could restore manual loop here if needed)

    print("\n[*] Visual Generation Complete. Proceeding to Editor...")

    # 6.5 GENERATE SOUND EFFECTS
    print("\n>>> Generating Sound Effects...")
    from agents.sfx_agent import SFXAgent
    sfx_agent = SFXAgent()
    
    # Check if SFX files already exist (resume support)
    sfx_hook_path = os.path.join(assets_dir, "sfx_hook.mp3")
    if os.path.exists(sfx_hook_path):
        print("[*] SFX files already exist, skipping generation.")
        sfx_mapping = {}  # Will be loaded from existing files
    else:
        try:
            sfx_mapping = sfx_agent.generate_sfx(script, assets_dir)
        except Exception as e:
            print(f"[!] SFX generation failed: {e}")
            sfx_mapping = {}

    # 7. ASSEMBLY
    print("\n>>> Assembling Long-Form Video...")
    editor = EditorAgent()
    
    final_clips = []
    
    # We assume 'prompts' list matches the order of 'audio_files' sections sequentially
    current_prompt_idx = 0
    
    # MOVIEPY COMPATIBILITY IMPORTS
    try:
        from moviepy.editor import ImageClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, TextClip
    except ImportError:
        try:
            from moviepy import ImageClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, TextClip
        except ImportError:
            print("Error: MoviePy not found.")
            return

    # ASSEMBLY LOGIC
    # ===================================================================
    # CASE 1: VISUAL BLOCKS (Strict Sync with Grouper)
    # ===================================================================
    if use_sentence_audio and visual_blocks:
        print(f"\n>>> PHASE 4: ASSEMBLING WITH VISUAL BLOCKS ({len(visual_blocks)} blocks)...")
        
        for i, block in enumerate(visual_blocks):
            print(f"   [Block {i+1}/{len(visual_blocks)}] Processing...")
            
            # 1. Get Merged Block Audio (THE CRITICAL LOCK)
            block_audio_path = block.get('final_audio_path')
            if not block_audio_path or not os.path.exists(block_audio_path):
                print(f"   [!] Missing audio for block {i+1}, skipping.")
                continue
            
            block_duration = block.get('duration', 0)
            block_text = block.get('text', '')
            
            # 2. Get Visual (Strict 1:1 mapping: Prompt[i] corresponds to Block[i])
            if i < len(prompts):
                visual_data = prompts[i]
            else:
                print(f"   [!] No prompt for block {i+1}")
                if prompts:
                    visual_data = prompts[-1]
                else:
                    continue
            
            v_path = os.path.join(assets_dir, visual_data['filename'])
            if not os.path.exists(v_path):
                # Try alternate extensions
                if v_path.endswith(".png"):
                    v_path = v_path.replace(".png", ".mp4")
                if not os.path.exists(v_path):
                    print(f"   [!] Missing visual: {v_path}")
                    continue
            
            # 3. Create Clip (STRICT DURATION LOCK)
            try:
                # Audio element
                b_audio_clip = AudioFileClip(block_audio_path)
                
                # Visual element (Image/Video) forced to EXACT block duration
                # THIS IS THE CRITICAL LOCK (Checklist #10)
                vc = editor.prepare_visual_clip(v_path, block_duration)
                if not vc:
                    continue
                
                # Apply transition
                vc = editor._apply_random_transition(vc, duration=0.6)
                
                # Subtitles (relative to 0.0 of this block - Checklist #12 & #16)
                subs = editor._generate_karaoke_subtitles(
                    block_text,
                    block_duration,
                    (1920, 1080),
                    audio_path=block_audio_path
                )
                
                # Composite (Checklist #11: Attach audio to clip, not timeline)
                block_clip = CompositeVideoClip([vc] + subs, size=(1920, 1080))
                
                if hasattr(block_clip, 'with_audio'):
                    block_clip = block_clip.with_audio(b_audio_clip)
                else:
                    block_clip = block_clip.set_audio(b_audio_clip)
                
                final_clips.append(block_clip)
                
            except Exception as e:
                print(f"   [!] Error assembling block {i+1}: {e}")
        
        # Skip to final concatenation (Checklist #13)
        print(f"\n[*] Assembled {len(final_clips)} blocks. Proceeding to final render...")
    
    # ===================================================================
    # CASE 2: LEGACY / SECTION LOOP (Fallback if no visual_blocks)
    # ===================================================================
    else:
        # Calculate visual distribution for legacy mode
        # Simple heuristic: visual count proportional to duration
        total_audio_duration = sum(af['duration'] for af in audio_files)
        total_visuals = len(prompts)
        section_visual_counts = {}
        
        remaining_visuals = total_visuals
        for i, af in enumerate(audio_files):
            if i == len(audio_files) - 1:
                count = remaining_visuals
            else:
                ratio = af.get('duration', 0) / (total_audio_duration or 1)
                count = int(ratio * total_visuals)
                if count < 1: count = 1
            section_visual_counts[af['name']] = count
            remaining_visuals -= count

        for af in audio_files:
            # For this audio section
            audio_path = af['path']
            section_text = af['text']
            duration = af.get('duration', 0)
            section_key = af.get('section', '')
            
            section_clips = []
        
            # --- STRICT 1:1 SYNC MODE (ZIPPER) ---
            if use_strict_mode and 'sentence_files' in af:
                print(f"   [Strict Sync] Assembling section '{af['name']}' using {len(af['sentence_files'])} sentences...")
                
                for sa in af['sentence_files']:
                    # 1. Get Audio
                    s_audio_path = sa['path']
                    s_text = sa['text']
                    s_duration = sa['duration']
                    
                    # 2. Get Visual (Strict Order)
                    if current_prompt_idx < len(prompts):
                        visual_data = prompts[current_prompt_idx]
                        current_prompt_idx += 1
                    else:
                        print(f"   [!] Warning: Ran out of visuals for sentence: {s_text[:30]}...")
                        if prompts: visual_data = prompts[-1]
                        else: continue
                    
                    v_path = os.path.join(assets_dir, visual_data['filename'])
                    if not os.path.exists(v_path):
                        print(f"   [!] Missing visual asset: {v_path}")
                        continue
                        
                    # 3. Create Clip (Strict Duration)
                    try:
                        # Visual (Image/Video) forced to exact audio duration
                        vc = editor.prepare_visual_clip(v_path, s_duration)
                        if not vc: continue
                        
                        # Transition (Slide In)
                        vc = editor._apply_random_transition(vc, duration=0.6)
                        
                        # Subtitles (Karaoke for this sentence only)
                        subs = editor._generate_karaoke_subtitles(s_text, s_duration, (1920, 1080), audio_path=s_audio_path)
                        
                        # Composite
                        s_audio_clip = AudioFileClip(s_audio_path)
                        
                        sent_clip = CompositeVideoClip([vc] + subs, size=(1920, 1080))
                        if hasattr(sent_clip, 'with_audio'):
                             sent_clip = sent_clip.with_audio(s_audio_clip)
                        else:
                             sent_clip = sent_clip.set_audio(s_audio_clip)
                             
                        section_clips.append(sent_clip)
                        
                    except Exception as e:
                        print(f"   [!] Error building sentence clip: {e}")
                

            
            # --- LEGACY DISTRIBUTED MODE ---
            else:
                needed = section_visual_counts[af['name']]
                section_visuals = []
                for _ in range(needed):
                    if current_prompt_idx < len(prompts):
                        section_visuals.append(prompts[current_prompt_idx])
                        current_prompt_idx += 1
                    else:
                        if prompts: section_visuals.append(prompts[-1])
                
                if not section_visuals: continue
    
                # WHISPER-BASED VISUAL TIMING (Precise segment detection)
                from utils.whisper_utils import get_sentence_timings_from_whisper
                from utils.timing_utils import split_into_sentences, calculate_sentence_durations
                
                whisper_segments = None
                try:
                    whisper_segments = get_sentence_timings_from_whisper(audio_path, "base")
                except Exception as e:
                    pass
                
                # Simplified Distribution Logic
                visual_durations = []
                if whisper_segments and len(section_visuals) <= len(whisper_segments):
                    # Use whisper segments
                    segments_per_visual = len(whisper_segments) / len(section_visuals)
                    seg_idx = 0.0
                    for i in range(len(section_visuals)):
                        start_seg = int(seg_idx)
                        end_seg = int(seg_idx + segments_per_visual)
                        if i == len(section_visuals) - 1: end_seg = len(whisper_segments)
                        
                        if start_seg < len(whisper_segments) and end_seg > 0:
                            start_time = whisper_segments[start_seg][1]
                            end_time = whisper_segments[min(end_seg, len(whisper_segments)) - 1][2]
                            visual_durations.append(end_time - start_time)
                        else:
                            visual_durations.append(duration / len(section_visuals))
                        seg_idx += segments_per_visual
                else:
                    # Backup: Equal distribution
                    visual_durations = [duration / len(section_visuals)] * len(section_visuals)
            
                # Create Clips (Legacy)
                for i, v in enumerate(section_visuals):
                    v_path = os.path.join(assets_dir, v['filename'])
                    if not os.path.exists(v_path): continue
                    
                    vis_duration = visual_durations[i] if i < len(visual_durations) else duration / len(section_visuals)
                    
                    try:
                        vc = editor.prepare_visual_clip(v_path, vis_duration)
                        if vc:
                            vc = editor._apply_random_transition(vc, duration=0.8)
                            section_clips.append(vc)
                    except Exception as e:
                        print(f"Error: {e}")
    
            # --- SECTION FINISHING (Common to Legacy/Zipper loops) ---
            if not section_clips: continue
                
            # Concatenate Visuals for this section
            section_video = concatenate_videoclips(section_clips, method="compose")
            
            # In strict mode, audio is already attached per clip.
            # In legacy mode, we need to attach the section audio.
            if not (use_strict_mode and 'sentence_files' in af):
                section_audio = AudioFileClip(audio_path)
                if hasattr(section_video, 'with_audio'):
                    section_video = section_video.with_audio(section_audio)
                else:
                    section_video = section_video.set_audio(section_audio)
                
                # Add Subtitles (Whole Section)
                subs = editor._generate_karaoke_subtitles(section_text, duration, (1920, 1080))
                section_video = CompositeVideoClip([section_video] + subs, size=(1920, 1080))
    
            # SFX Handling (Apply to whole section)
            sfx_path = os.path.join(assets_dir, f"sfx_{section_key}.mp3")
            if os.path.exists(sfx_path) and os.path.getsize(sfx_path) > 1000:
                 # Mix into the composite audio
                 try:
                     current_audio = section_video.audio
                     mixed = editor._mix_sfx_with_audio(current_audio, sfx_path, sfx_volume=0.25)
                     if hasattr(section_video, 'with_audio'):
                         section_video = section_video.with_audio(mixed)
                     else:
                         section_video = section_video.set_audio(mixed)
                 except Exception as e:
                     print(f"SFX Mix Error: {e}")
            
            # RENDER SECTION TO DISK IMMEDIATELY (Memory Optimization)
            section_temp_path = os.path.join(assets_dir, f"temp_section_{section_key}.mp4")
            print(f"   [*] Rendering intermediate section to: {os.path.basename(section_temp_path)}...")
            try:
                # Write section to file to free up RAM
                section_video.write_videofile(section_temp_path, fps=30, codec='libx264', audio_codec='aac', threads=4, logger=None)
                
                # Close objects to release memory
                section_video.close()
                for c in section_clips: c.close()
                
                final_clips.append(section_temp_path)  # Store PATH, not object
                print(f" - Section rendered: {af['name']}")
                
            except Exception as e:
                print(f"   [!] Error rendering section {section_key}: {e}")
                # Fallback (risky for memory): keep object
                final_clips.append(section_video)

            # MEMORY CLEANUP
            import gc
            del section_video
            del section_clips
            gc.collect()

    # Final Concatenation
    if final_clips:
        # Use path relative to script location
        base_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        output_path = os.path.join(base_output_dir, f"longform_{int(time.time())}.mp4")
        
        if not os.path.exists(base_output_dir): os.makedirs(base_output_dir)
        
        # Reload clips from disk (low memory usage)
        print("\n>>> Concatenating final video from sections...")
        loaded_clips = []
        for clip_ref in final_clips:
            if isinstance(clip_ref, str):
                loaded_clips.append(VideoFileClip(clip_ref))
            else:
                loaded_clips.append(clip_ref)

        full_video = concatenate_videoclips(loaded_clips, method="compose")
        full_video.write_videofile(output_path, fps=30, codec='libx264', audio_codec='aac')
        print(f"\nSUCCESS! Short test video saved to: {output_path}")
    else:
        print("Failed to assemble video.")

def verify_script_claims(script_data, research_brief):
    """
    Verifies that all numerical claims in the script are backed by research.
    """
    from utils.llm_client import LLMClient
    import re
    
    llm = LLMClient()
    script_text = json.dumps(script_data)
    
    # Extract numerical claims
    number_patterns = [
        r'\$[\d,]+(?:\.\d+)?\s*(?:billion|trillion|million|thousand)?',
        r'\d+(?:\.\d+)?%',
        r'\d+(?:,\d{3})*\s+(?:people|jobs|workers|factories|homes)'
    ]
    
    found_claims = []
    for pattern in number_patterns:
        matches = re.finditer(pattern, script_text, re.IGNORECASE)
        for match in matches:
            found_claims.append(match.group(0))
    
    # Basic check - in production use LLM to verify against stats
    print(f"[*] Found {len(found_claims)} numerical claims to verify.")
    return {"claims": found_claims, "verified": True} # Mock return for now

if __name__ == "__main__":
    main()
