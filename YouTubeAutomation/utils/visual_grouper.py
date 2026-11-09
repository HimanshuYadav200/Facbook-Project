"""
Visual Grouper - Strict Sync Architecture
Transforms N short sentence audio files (1-3s each) into ~target_count visual blocks (4-6s each)

Algorithm: "Shortest Pair" iterative merge
- Start with N blocks (1 sentence each)
- Repeatedly merge the two adjacent blocks with shortest combined duration
- Stop when target_count is reached
- Physically merge audio files into block_XX.mp3

Reference: User's Strict Sync Checklist (Phase 2: Grouping)
"""

import os

# MoviePy compatibility
try:
    from moviepy.editor import AudioFileClip, concatenate_audioclips
except ImportError:
    try:
        from moviepy import AudioFileClip, concatenate_audioclips
    except ImportError:
        AudioFileClip = None
        concatenate_audioclips = None


def group_audio_segments(audio_segments, target_count=None, min_duration=5.0, output_dir=None, merge_audio=True):
    """
    Groups granular sentence audio into larger visual blocks using "shortest pair" algorithm.
    
    Args:
        audio_segments: List of dicts [{'path', 'duration', 'text', 'section', ...}, ...]
        target_count: Target number of visual blocks (e.g., 100). If None, uses min_duration logic.
        min_duration: Minimum block duration (used if target_count is None)
        output_dir: Directory to save merged block_XX.mp3 files
        merge_audio: If True, physically concatenates audio files into single block files
        
    Returns:
        List of block dicts: [{'text', 'duration', 'final_audio_path', 'audio_files', 'section'}, ...]
    """
    if not audio_segments:
        return []

    print(f"\n[VISUAL GROUPER] Processing {len(audio_segments)} sentence audio files...")
    
    # Step 1: Initialize Blocks - Each sentence becomes its own block
    blocks = []
    for seg in audio_segments:
        blocks.append({
            'text': seg.get('text', ''),
            'duration': seg.get('duration', 0),
            'audio_files': [seg],  # List of source file dicts
            'section': seg.get('section', 'unknown')
        })
    
    print(f"    Initial: {len(blocks)} blocks (1 sentence each)")
    
    # Step 2: Determine target count
    if target_count is None:
        # Auto-calculate based on min_duration
        total_duration = sum(b['duration'] for b in blocks)
        target_count = max(1, int(total_duration / min_duration))
        print(f"    Auto target: {target_count} blocks (for {total_duration:.1f}s total, ~{min_duration}s each)")
    
    # Ensure target_count is reasonable
    target_count = max(1, min(target_count, len(blocks)))
    
    # Step 3: Iterative Merge - "Shortest Pair" Algorithm
    # Repeatedly merge the two adjacent blocks with minimum combined duration
    print(f"    Merging to target: {target_count} blocks...")
    
    while len(blocks) > target_count:
        # Find the pair with minimum combined duration
        min_pair_duration = float('inf')
        merge_idx = -1
        
        for i in range(len(blocks) - 1):
            pair_dur = blocks[i]['duration'] + blocks[i + 1]['duration']
            if pair_dur < min_pair_duration:
                min_pair_duration = pair_dur
                merge_idx = i
        
        if merge_idx < 0:
            break  # Safety: no valid pair found
        
        # Merge: Left block absorbs Right block
        left = blocks[merge_idx]
        right = blocks.pop(merge_idx + 1)
        
        left['text'] += " " + right['text']
        left['duration'] += right['duration']
        left['audio_files'].extend(right['audio_files'])
        # Keep the section from left (or could merge logic if needed)
    
    # Log stats
    durations = [b['duration'] for b in blocks]
    avg_dur = sum(durations) / len(durations) if durations else 0
    min_dur = min(durations) if durations else 0
    max_dur = max(durations) if durations else 0
    
    print(f"    Result: {len(blocks)} visual blocks")
    print(f"    Duration stats: min={min_dur:.1f}s, avg={avg_dur:.1f}s, max={max_dur:.1f}s")
    
    # Step 4: Physical Audio Merge
    if merge_audio and output_dir:
        if AudioFileClip is None:
            print("    [!] MoviePy not available for audio merge")
        else:
            _merge_block_audio_files(blocks, output_dir)
    
    return blocks


def _merge_block_audio_files(blocks, output_dir):
    """
    Physically concatenates the individual sentence MP3s into a single block MP3.
    Creates audio_block_01.mp3, audio_block_02.mp3, etc.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"    [*] Merging audio files into {output_dir}...")
    
    for i, block in enumerate(blocks):
        filename = f"audio_block_{i+1:03d}.mp3"
        out_path = os.path.join(output_dir, filename)
        
        # Resume support: skip if already exists
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            block['final_audio_path'] = out_path
            block['filename'] = filename
            continue
        
        # Load individual sentence clips
        clips = []
        for af in block['audio_files']:
            path = af.get('path', '')
            if os.path.exists(path):
                try:
                    clips.append(AudioFileClip(path))
                except Exception as e:
                    print(f"        [!] Failed to load {path}: {e}")
            else:
                print(f"        [!] Missing: {path}")
        
        if not clips:
            print(f"        [!] No valid clips for block {i+1}")
            block['final_audio_path'] = None
            continue
        
        # Apply crossfades for smooth transitions
        # Fade duration: 50ms (0.05s) - enough to smooth, not noticeable
        CROSSFADE_DURATION = 0.05
        
        crossfaded_clips = []
        for idx, clip in enumerate(clips):
            modified_clip = clip
            
            # Apply fade-in to all clips except the first
            if idx > 0:
                try:
                    modified_clip = modified_clip.audio_fadein(CROSSFADE_DURATION)
                except:
                    # Fallback if audio_fadein not available
                    pass
            
            # Apply fade-out to all clips except the last
            if idx < len(clips) - 1:
                try:
                    modified_clip = modified_clip.audio_fadeout(CROSSFADE_DURATION)
                except:
                    # Fallback if audio_fadeout not available
                    pass
            
            crossfaded_clips.append(modified_clip)
        
        # Concatenate and save
        try:
            merged = concatenate_audioclips(crossfaded_clips)
            merged.write_audiofile(out_path, logger=None)
            
            # Update block metadata
            block['final_audio_path'] = out_path
            block['filename'] = filename
            block['duration'] = merged.duration  # Use actual merged duration (most accurate)
            
            # Clean up to prevent memory leaks
            merged.close()
            for c in clips:
                c.close()
                
        except Exception as e:
            print(f"        [!] Merge failed for block {i+1}: {e}")
            # Fallback: use first audio file
            if block['audio_files']:
                block['final_audio_path'] = block['audio_files'][0].get('path')
            else:
                block['final_audio_path'] = None
    
    # Summary
    success = sum(1 for b in blocks if b.get('final_audio_path'))
    print(f"    [*] Merged {success}/{len(blocks)} block audio files")


def calculate_target_count(total_sentences, target_visual_duration=5.0, avg_sentence_duration=2.5):
    """
    Helper to calculate a reasonable target_count for grouping.
    
    Args:
        total_sentences: Number of sentence audio files
        target_visual_duration: Desired average block duration (e.g., 5 seconds)
        avg_sentence_duration: Average duration of individual sentences
        
    Returns:
        Recommended target_count
    """
    total_duration = total_sentences * avg_sentence_duration
    return max(1, int(total_duration / target_visual_duration))
