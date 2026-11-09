"""
Timing Utilities for Sentence-Level Visual Sync

Provides functions to calculate per-sentence duration based on:
1. Character count proportional distribution
2. Word count proportional distribution
3. Minimum duration enforcement (no jarring cuts)
4. Word-level timing using Whisper (for subtitle highlighting)
"""

import re
import os
from typing import List, Tuple, Dict, Optional


def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into sentences, handling common edge cases.
    """
    if not text:
        return []
    
    # Simple sentence splitting on . ! ? but preserve abbreviations
    # Handle common patterns like "Mr." "Dr." "$3.3" etc.
    text = text.strip()
    
    # Replace common abbreviations temporarily
    text = text.replace("Mr.", "Mr##")
    text = text.replace("Mrs.", "Mrs##")
    text = text.replace("Dr.", "Dr##")
    text = text.replace("U.S.", "US##")
    text = text.replace("...", "###")
    
    # Handle decimal numbers (e.g., $3.3 trillion)
    text = re.sub(r'(\d)\.(\d)', r'\1##\2', text)
    
    # Split on sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Restore abbreviations
    result = []
    for s in sentences:
        s = s.replace("##", ".")
        s = s.replace("###", "...")
        s = s.strip()
        if s:
            result.append(s)
    
    return result


def calculate_sentence_durations(
    sentences: List[str], 
    total_duration: float,
    min_duration: float = 2.0,
    max_duration: float = 10.0
) -> List[float]:
    """
    Calculates duration for each sentence proportionally based on character count.
    
    Args:
        sentences: List of sentence strings
        total_duration: Total audio duration for all sentences
        min_duration: Minimum duration per sentence (avoid jarring cuts)
        max_duration: Maximum duration per sentence (avoid boring holds)
    
    Returns:
        List of durations corresponding to each sentence
    """
    if not sentences:
        return []
    
    if len(sentences) == 1:
        return [total_duration]
    
    # Calculate character counts
    char_counts = [len(s) for s in sentences]
    total_chars = sum(char_counts)
    
    if total_chars == 0:
        # Equal distribution if somehow all empty
        equal_dur = total_duration / len(sentences)
        return [equal_dur] * len(sentences)
    
    # Proportional distribution
    durations = []
    for count in char_counts:
        proportion = count / total_chars
        dur = total_duration * proportion
        durations.append(dur)
    
    # Enforce min/max constraints
    # This is iterative to handle edge cases
    for i in range(len(durations)):
        if durations[i] < min_duration:
            durations[i] = min_duration
        elif durations[i] > max_duration:
            durations[i] = max_duration
    
    # Normalize to match total_duration
    current_total = sum(durations)
    if current_total > 0 and abs(current_total - total_duration) > 0.1:
        scale = total_duration / current_total
        durations = [d * scale for d in durations]
    
    return durations


def get_sentence_timing(
    text: str, 
    total_duration: float
) -> List[Tuple[str, float, float]]:
    """
    Main function: Returns list of (sentence, start_time, end_time) tuples.
    
    Args:
        text: Full section text
        total_duration: Audio duration for this section
    
    Returns:
        List of tuples: (sentence_text, start_time, end_time)
    """
    sentences = split_into_sentences(text)
    
    if not sentences:
        return [(text, 0.0, total_duration)]
    
    durations = calculate_sentence_durations(sentences, total_duration)
    
    result = []
    current_time = 0.0
    
    for sentence, duration in zip(sentences, durations):
        end_time = current_time + duration
        result.append((sentence, current_time, end_time))
        current_time = end_time
    
    return result


# ===== WORD-LEVEL TIMING FUNCTIONS (for subtitle highlighting) =====

def get_word_timings_for_audio(audio_path: str, model_size: str = "base") -> Optional[List[Dict]]:
    """
    Uses OpenAI Whisper to extract word-level timestamps from audio.
    
    Args:
        audio_path: Path to audio file (mp3/wav)
        model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
    
    Returns:
        List of dicts: [{"word": str, "start": float, "end": float}, ...]
        Returns None if Whisper unavailable or fails.
    """
    if not os.path.exists(audio_path):
        return None
    
    try:
        import whisper
        
        # Global cache to prevent reloading model 100+ times
        global _WHISPER_MODEL_CACHE
        if '_WHISPER_MODEL_CACHE' not in globals():
            _WHISPER_MODEL_CACHE = {}
            
        if model_size not in _WHISPER_MODEL_CACHE:
            print(f"    [INFO] Loading Whisper model '{model_size}' into memory (this happens once)...")
            _WHISPER_MODEL_CACHE[model_size] = whisper.load_model(model_size)
            
        model = _WHISPER_MODEL_CACHE[model_size]
        
        # Transcribe with word timestamps
        result = model.transcribe(
            audio_path, 
            word_timestamps=True,
            language="en"
        )
        
        # Extract word timings from segments
        word_timings = []
        
        if "segments" in result:
            for segment in result["segments"]:
                if "words" in segment:
                    for word_info in segment["words"]:
                        word_timings.append({
                            "word": word_info.get("word", "").strip(),
                            "start": word_info.get("start", 0.0),
                            "end": word_info.get("end", 0.0)
                        })
        
        return word_timings if word_timings else None
        
    except ImportError:
        print("[!] Whisper not installed. Using estimation fallback.")
        return None
    except Exception as e:
        print(f"[!] Whisper error: {e}")
        return None


def estimate_word_timings(text: str, duration: float) -> List[Dict]:
    """
    Estimates word-level timing based on character length.
    Fallback when Whisper is unavailable.
    
    Args:
        text: Text to split into words
        duration: Total duration for the text
    
    Returns:
        List of dicts: [{"word": str, "start": float, "end": float}, ...]
    """
    words = text.split()
    if not words:
        return []
    
    # Calculate character counts (including spaces conceptually)
    char_counts = [len(w) for w in words]
    total_chars = sum(char_counts)
    
    if total_chars == 0:
        # Equal distribution
        word_dur = duration / len(words)
        result = []
        current = 0.0
        for word in words:
            result.append({
                "word": word,
                "start": current,
                "end": current + word_dur
            })
            current += word_dur
        return result
    
    # Proportional distribution
    result = []
    current = 0.0
    
    for word, char_count in zip(words, char_counts):
        proportion = char_count / total_chars
        word_dur = duration * proportion
        
        # Enforce minimum word duration (0.15s for readability)
        word_dur = max(0.15, word_dur)
        
        result.append({
            "word": word,
            "start": current,
            "end": current + word_dur
        })
        current += word_dur
    
    # Scale to fit duration
    if result and result[-1]["end"] != duration:
        scale = duration / result[-1]["end"]
        for item in result:
            item["start"] *= scale
            item["end"] *= scale
    
    return result


if __name__ == "__main__":
    # Test
    test_text = "September 10th, 2001. Most Americans went to bed that night with no idea their world was about to change forever. The next morning, $3.3 trillion would vanish from the U.S. economy. And that financial wound? It's still bleeding today."
    
    timings = get_sentence_timing(test_text, 30.0)
    
    print("Sentence Timing Analysis:")
    print("-" * 50)
    for i, (sent, start, end) in enumerate(timings):
        print(f"{i+1}. [{start:.1f}s - {end:.1f}s] ({end-start:.1f}s)")
        print(f"   {sent[:60]}...")
        print()
    
    # Test word estimation
    print("\nWord Timing (Estimated):")
    word_timings = estimate_word_timings("Hello world test", 3.0)
    for wt in word_timings:
        print(f"  {wt['word']}: {wt['start']:.2f}s - {wt['end']:.2f}s")

