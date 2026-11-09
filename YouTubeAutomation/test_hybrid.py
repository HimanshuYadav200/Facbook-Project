"""
Test Hybrid Sentence Audio + Visual Sync

This test:
1. Uses AudioAgent.generate_sentence_audio() to create per-sentence audio
2. Each visual gets duration = exact sentence audio duration
3. Perfect 1:1 sync between visuals and spoken sentences
"""
import os
import sys
import time
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.audio_agent import AudioAgent
from agents.editor_agent import EditorAgent

# MoviePy imports
try:
    from moviepy import CompositeVideoClip, concatenate_videoclips, concatenate_audioclips, AudioFileClip
except ImportError:
    from moviepy.editor import CompositeVideoClip, concatenate_videoclips, concatenate_audioclips, AudioFileClip

def main():
    session_id = "run_20260111_081251"
    assets_dir = os.path.join("assets", session_id)
    
    # Load script
    script_path = os.path.join(assets_dir, "script.json")
    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)
    
    # Load visual prompts
    prompts_path = os.path.join(assets_dir, "visual_requests.txt")
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
    
    print(f"[*] Loaded {len(prompts)} visual prompts")
    
    # TEST: Generate sentence-level audio for HOOK section only
    print("\n=== HYBRID APPROACH TEST (Hook Section Only) ===")
    
    # Create a mini script with just hook
    hook_script = {"hook": script.get("hook", {})}
    
    audio_agent = AudioAgent()
    
    # Check if sentence audio already exists
    first_sentence_audio = os.path.join(assets_dir, "audio_hook_01.mp3")
    
    if os.path.exists(first_sentence_audio):
        print("[*] Sentence audio files exist, loading...")
        
        # Load existing sentence audio metadata
        sentence_audio = []
        from utils.timing_utils import split_into_sentences
        
        sentences = split_into_sentences(script["hook"]["text"])
        
        for si, sent in enumerate(sentences):
            filename = f"audio_hook_{si+1:02d}.mp3"
            path = os.path.join(assets_dir, filename)
            
            if os.path.exists(path):
                clip = AudioFileClip(path)
                dur = clip.duration
                if hasattr(clip, 'close'): clip.close()
                
                sentence_audio.append({
                    "name": filename,
                    "path": path,
                    "text": sent,
                    "duration": dur,
                    "section": "hook",
                    "sentence_index": si
                })
        
        print(f"[*] Loaded {len(sentence_audio)} sentence audio files")
    else:
        print("[*] Generating sentence audio (requires VPN + ElevenLabs)...")
        sentence_audio = audio_agent.generate_sentence_audio(hook_script, assets_dir)
    
    if not sentence_audio:
        print("[!] No sentence audio generated. Check VPN and API.")
        return
    
    # Display sentence audio info
    print(f"\n[*] Sentence Audio ({len(sentence_audio)} files):")
    total_hook_duration = 0
    for sa in sentence_audio:
        print(f"   {sa['name']}: {sa['duration']:.2f}s - {sa['text'][:40]}...")
        total_hook_duration += sa['duration']
    print(f"   TOTAL: {total_hook_duration:.2f}s")
    
    # Now map visuals 1:1 with sentences
    # Get first N visuals where N = number of sentences
    num_sentences = len(sentence_audio)
    section_visuals = prompts[:num_sentences]
    
    # Fix filenames
    for v in section_visuals:
        base = os.path.splitext(v['filename'])[0]
        for ext in ['.jpeg', '.jpg', '.png', '.mp4', '.mov']:
            test_path = os.path.join(assets_dir, base + ext)
            if os.path.exists(test_path):
                v['filename'] = base + ext
                break
    
    print(f"\n[*] Mapping {num_sentences} sentences to {len(section_visuals)} visuals")
    
    editor = EditorAgent()
    
    # Create clips with EXACT sentence audio duration
    section_clips = []
    for i, (sa, v) in enumerate(zip(sentence_audio, section_visuals)):
        v_path = os.path.join(assets_dir, v['filename'])
        
        if not os.path.exists(v_path):
            print(f"[!] Missing visual: {v['filename']}")
            continue
        
        # EXACT duration from sentence audio
        vis_duration = sa['duration']
        
        print(f"  Clip {i+1}: {v['filename']} ({vis_duration:.2f}s) <- \"{sa['text'][:30]}...\"")
        
        try:
            vc = editor.prepare_visual_clip(v_path, vis_duration)
            if vc:
                vc = editor._apply_random_transition(vc, duration=0.4)
                section_clips.append(vc)
        except Exception as e:
            print(f"    Error: {e}")
    
    if not section_clips:
        print("No clips created!")
        return
    
    print(f"\n[*] Concatenating {len(section_clips)} clips...")
    section_video = concatenate_videoclips(section_clips, method="compose")
    
    print("[*] Generating subtitles...")
    hook_text = script["hook"]["text"]
    subs = editor._generate_karaoke_subtitles(hook_text, total_hook_duration, (1920, 1080))
    print(f"    Created {len(subs)} subtitle clips")
    
    print("[*] Compositing video + subtitles...")
    final_section = CompositeVideoClip([section_video] + subs, size=(1920, 1080))
    
    # Concatenate sentence audio into single track
    print("[*] Concatenating sentence audio...")
    audio_clips = [AudioFileClip(sa['path']) for sa in sentence_audio]
    combined_audio = concatenate_audioclips(audio_clips)
    
    # Attach audio
    if hasattr(final_section, 'with_audio'):
        final_section = final_section.with_audio(combined_audio)
    else:
        final_section = final_section.set_audio(combined_audio)
    
    # Output
    output_path = os.path.join("output", f"test_hybrid_sync_{int(time.time())}.mp4")
    if not os.path.exists("output"):
        os.makedirs("output")
    
    print(f"\n[*] Rendering to: {output_path}")
    final_section.write_videofile(output_path, fps=30, codec='libx264', audio_codec='aac')
    
    print(f"\n=== SUCCESS ===")
    print(f"Test video: {output_path}")
    print("\nThis video has PERFECT 1:1 sentence-visual sync!")
    print("Each visual's duration = exact spoken sentence duration.")

if __name__ == "__main__":
    main()
