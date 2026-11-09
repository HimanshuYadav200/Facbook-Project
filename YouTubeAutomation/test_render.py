"""
Quick Test Render v3 - WHISPER-BASED visual timing
Uses Whisper transcription for precise sentence-level visual sync.
"""
import os
import sys
import time
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.editor_agent import EditorAgent
from utils.whisper_utils import get_sentence_timings_from_whisper, transcribe_with_caching

# MoviePy imports
try:
    from moviepy import ImageClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, TextClip
except ImportError:
    from moviepy.editor import ImageClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, TextClip

def main():
    session_id = "run_20260111_081251"
    assets_dir = os.path.join("assets", session_id)
    
    # Load script
    script_path = os.path.join(assets_dir, "script.json")
    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)
    
    # Load prompts
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
    
    print(f"[*] Loaded {len(prompts)} prompts")
    
    # HOOK SECTION
    audio_path = os.path.join(assets_dir, "audio_hook.mp3")
    section_text = script.get("hook", {}).get("text", "")
    
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    
    print(f"[*] Hook Duration: {total_duration:.1f}s")
    
    # WHISPER TRANSCRIPTION FOR PRECISE TIMING
    print("\n[*] Using Whisper for precise segment timing...")
    whisper_segments = get_sentence_timings_from_whisper(audio_path, "base")
    
    if whisper_segments:
        print(f"[*] Whisper found {len(whisper_segments)} segments:")
        for i, (text, start, end) in enumerate(whisper_segments):
            print(f"   {i+1}. [{start:.2f}s - {end:.2f}s] ({end-start:.2f}s) {text[:40]}...")
    else:
        print("[!] Whisper failed, falling back to equal distribution")
        # Create fake segments for fallback
        HOOK_VISUALS = 9
        seg_dur = total_duration / HOOK_VISUALS
        whisper_segments = [(f"Segment {i}", i*seg_dur, (i+1)*seg_dur) for i in range(HOOK_VISUALS)]
    
    # Get first 9 visuals for hook (or match to segment count)
    num_visuals = min(9, len(whisper_segments))
    section_visuals = prompts[:num_visuals]
    
    # Update filenames to match actual files
    for v in section_visuals:
        base = os.path.splitext(v['filename'])[0]
        for ext in ['.jpeg', '.jpg', '.png', '.mp4', '.mov']:
            test_path = os.path.join(assets_dir, base + ext)
            if os.path.exists(test_path):
                v['filename'] = base + ext
                break
    
    print(f"\n[*] Using {len(section_visuals)} visuals")
    
    # MAP VISUALS TO WHISPER SEGMENTS
    # Each visual gets the duration of its corresponding Whisper segment
    if len(section_visuals) <= len(whisper_segments):
        # Direct 1:1 mapping (or group segments if fewer visuals)
        visual_timings = []
        segments_per_visual = len(whisper_segments) / len(section_visuals)
        
        seg_idx = 0.0
        for i in range(len(section_visuals)):
            start_seg = int(seg_idx)
            end_seg = int(seg_idx + segments_per_visual)
            if i == len(section_visuals) - 1:
                end_seg = len(whisper_segments)
            
            # Start time is from first segment, end time is from last segment in group
            start_time = whisper_segments[start_seg][1]
            end_time = whisper_segments[end_seg - 1][2]
            duration = end_time - start_time
            
            visual_timings.append((start_time, end_time, duration))
            seg_idx += segments_per_visual
    else:
        # More visuals than segments - distribute evenly within each segment
        visual_timings = []
        visuals_per_seg = len(section_visuals) / len(whisper_segments)
        
        for seg_idx, (text, seg_start, seg_end) in enumerate(whisper_segments):
            seg_dur = seg_end - seg_start
            num_vis_in_seg = int(visuals_per_seg) if seg_idx < len(whisper_segments) - 1 else len(section_visuals) - len(visual_timings)
            
            if num_vis_in_seg > 0:
                vis_dur = seg_dur / num_vis_in_seg
                for j in range(num_vis_in_seg):
                    v_start = seg_start + j * vis_dur
                    v_end = v_start + vis_dur
                    visual_timings.append((v_start, v_end, vis_dur))
                    if len(visual_timings) >= len(section_visuals):
                        break
            
            if len(visual_timings) >= len(section_visuals):
                break
    
    # Ensure we have the right count
    while len(visual_timings) < len(section_visuals):
        # Pad with last segment
        last = visual_timings[-1] if visual_timings else (0, total_duration / len(section_visuals), total_duration / len(section_visuals))
        visual_timings.append(last)
    
    print(f"\n[*] Visual Timings (Whisper-based):")
    for i, (v, (start, end, dur)) in enumerate(zip(section_visuals, visual_timings)):
        print(f"   {v['filename']}: {start:.2f}s - {end:.2f}s ({dur:.2f}s)")
    
    editor = EditorAgent()
    
    section_clips = []
    for i, v in enumerate(section_visuals):
        v_path = os.path.join(assets_dir, v['filename'])
        if not os.path.exists(v_path):
            print(f"[!] Missing: {v['filename']}")
            continue
        
        start_time, end_time, vis_duration = visual_timings[i]
        vis_duration = max(2.0, vis_duration)  # Enforce minimum
        
        print(f"  Creating clip {i+1}/{len(section_visuals)}: {v['filename']} ({vis_duration:.2f}s)")
        
        try:
            vc = editor.prepare_visual_clip(v_path, vis_duration)
            if vc:
                vc = editor._apply_random_transition(vc, duration=0.5)
                section_clips.append(vc)
        except Exception as e:
            print(f"  [!] Error: {e}")
    
    if not section_clips:
        print("No clips created!")
        return
    
    print(f"\n[*] Concatenating {len(section_clips)} clips...")
    section_video = concatenate_videoclips(section_clips, method="compose")
    
    print("[*] Generating subtitles...")
    subs = editor._generate_karaoke_subtitles(section_text, total_duration, (1920, 1080))
    print(f"    Created {len(subs)} subtitle clips")
    
    print("[*] Compositing...")
    final_section = CompositeVideoClip([section_video] + subs, size=(1920, 1080))
    
    # Mix SFX
    section_audio = audio
    sfx_path = os.path.join(assets_dir, "sfx_hook.mp3")
    if os.path.exists(sfx_path):
        print("[*] Mixing SFX...")
        section_audio = editor._mix_sfx_with_audio(section_audio, sfx_path, sfx_volume=0.25)
    
    # Attach audio
    if hasattr(final_section, 'with_audio'):
        final_section = final_section.with_audio(section_audio)
    else:
        final_section = final_section.set_audio(section_audio)
    
    # Output
    output_path = os.path.join("output", f"test_whisper_sync_{int(time.time())}.mp4")
    if not os.path.exists("output"):
        os.makedirs("output")
    
    print(f"\n[*] Rendering to: {output_path}")
    print("    This should take ~2-5 minutes...")
    
    final_section.write_videofile(output_path, fps=30, codec='libx264', audio_codec='aac')
    
    print(f"\n=== SUCCESS ===")
    print(f"Test video saved to: {output_path}")
    print("\nCheck: Visuals now use WHISPER segment timing!")
    print("Each visual duration matches what the narrator actually speaks.")

if __name__ == "__main__":
    main()
