import os
import json
import time
from agents.editor_agent import EditorAgent
from agents.audio_agent import AudioAgent
try:
    from moviepy.editor import AudioFileClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips
except ImportError:
    from moviepy import AudioFileClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips

def test_partial_assembly():
    assets_dir = os.path.join(os.getcwd(), "YouTubeAutomation", "assets")
    script_path = os.path.join(assets_dir, "script.json")
    prompts_path = os.path.join(assets_dir, "visual_requests.txt")
    
    print(f"[*] Testing Assembly in: {assets_dir}")
    
    # 1. Load Script
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)
        
    # 2. Load Visual Prompts
    prompts = []
    if os.path.exists(prompts_path):
        with open(prompts_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        current = {}
        for line in lines:
            line = line.strip()
            if line.startswith("FILE:"): current['filename'] = line.replace("FILE:", "").strip()
            elif line.startswith("TYPE:"): current['type'] = line.replace("TYPE:", "").strip()
            elif line.startswith("PROMPT:"): current['prompt'] = line.replace("PROMPT:", "").strip()
            elif line.startswith("---") and 'filename' in current:
                prompts.append(current)
                current = {}
        if 'filename' in current: prompts.append(current)
    
    print(f"[*] Loaded {len(prompts)} visual prompts.")
    
    # 3. Load Audio & Group by Section
    audio_agent = AudioAgent()
    # This returns all sentence files (checking disk)
    all_sentence_files = audio_agent.generate_sentence_audio(script, assets_dir)
    
    # Group logic (copied from main.py)
    section_totals = {}
    for sa in all_sentence_files:
        section = sa['section']
        if section not in section_totals:
            section_totals[section] = {'duration': 0, 'files': [], 'text': ""}
        
        section_totals[section]['duration'] += sa['duration']
        section_totals[section]['text'] += " " + sa['text']
        section_totals[section]['files'].append(sa)
    
    audio_files = []
    for section, data in section_totals.items():
        # Make a dummy 'audio_section.mp3' entry for the list structure, 
        # but the real data is in 'sentence_files'
        audio_files.append({
            'name': f"audio_{section}.mp3",
            'path': data['files'][0]['path'], 
            'text': data['text'].strip(),
            'duration': data['duration'],
            'section': section,
            'sentence_files': data['files']
        })
        
    print(f"[*] Grouped into {len(audio_files)} sections.")
    
    # 4. SLICE - TEST ONLY FIRST 2 SECTIONS (Hook + Thesis/Intro)
    test_sections = audio_files[:2]
    print(f"[*] Testing Assembly for: {[x['section'] for x in test_sections]}")
    
    editor = EditorAgent()
    final_clips = []
    current_prompt_idx = 0
    
    # 5. Assembly Loop
    for af in test_sections:
        section_key = af['section']
        print(f"\n>>> Assembling Section: {section_key}")
        
        section_clips = []
        
        # Strict Sync Loop
        for sa in af['sentence_files']:
            s_audio_path = sa['path']
            s_text = sa['text']
            s_duration = sa['duration']
            
            # Get Visual
            if current_prompt_idx < len(prompts):
                visual_data = prompts[current_prompt_idx]
                # FORCE FILENAME SYNC (Disk has 02d, Txt has 003d)
                visual_data['filename'] = f"visual_{current_prompt_idx+1:02d}.png"
                current_prompt_idx += 1
            else:
                break
                
            v_path = os.path.join(assets_dir, visual_data['filename'])
            if not os.path.exists(v_path):
                print(f"   [!] Missing visual: {v_path}")
                continue
                
            print(f"   - {os.path.basename(v_path)} ({s_duration:.1f}s) -> '{s_text[:20]}...'")
            
            try:
                # Video Clip
                vc = editor.prepare_visual_clip(v_path, s_duration)
                if not vc: continue
                
                # Transition
                vc = editor._apply_random_transition(vc, duration=0.6)
                
                # Subtitles
                subs = editor._generate_karaoke_subtitles(s_text, s_duration, (1920, 1080), audio_path=s_audio_path)
                
                # Composite
                sent_clip = CompositeVideoClip([vc] + subs, size=(1920, 1080))
                s_audio = AudioFileClip(s_audio_path)
                
                if hasattr(sent_clip, 'with_audio'):
                    sent_clip = sent_clip.with_audio(s_audio)
                else:
                    sent_clip = sent_clip.set_audio(s_audio)
                
                section_clips.append(sent_clip)
                
            except Exception as e:
                print(f"   [!] Error: {e}")
        
        if not section_clips: continue
        
        # Concatenate Section
        print("   [*] Concatenating section...")
        section_video = concatenate_videoclips(section_clips, method="compose")
        
        # Render Temp
        out_path = os.path.join(assets_dir, f"test_render_{section_key}.mp4")
        section_video.write_videofile(out_path, fps=24, codec='libx264', audio_codec='aac', threads=4, logger=None)
        
        final_clips.append(out_path)
        section_video.close()
        for c in section_clips: c.close()

    print("\n[*] Partial Test Complete!")
    print(f"Generated: {final_clips}")

if __name__ == "__main__":
    test_partial_assembly()
