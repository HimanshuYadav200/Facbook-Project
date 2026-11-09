"""
Whisper Utilities for Word-Level Audio Transcription

Uses OpenAI Whisper to extract word-level timestamps from audio files.
This enables precise visual-audio synchronization.
"""

import os
from typing import List, Tuple, Optional, Dict
import json


def transcribe_audio(audio_path: str, model_size: str = "base") -> Optional[Dict]:
    """
    Transcribes audio using Whisper and returns word-level timestamps.
    
    Args:
        audio_path: Path to the audio file (mp3, wav, etc.)
        model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
    
    Returns:
        Dict with 'text', 'segments' (sentence-level), and 'words' (word-level)
    """
    try:
        import whisper
        
        print(f"[Whisper] Loading model: {model_size}")
        model = whisper.load_model(model_size)
        
        print(f"[Whisper] Transcribing: {os.path.basename(audio_path)}")
        result = model.transcribe(
            audio_path,
            word_timestamps=True,
            language="en"
        )
        
        return result
        
    except Exception as e:
        print(f"[Whisper] Error: {e}")
        return None


def get_word_timings(audio_path: str, model_size: str = "base") -> List[Tuple[str, float, float]]:
    """
    Gets word-level timings from audio.
    
    Returns:
        List of tuples: (word, start_time, end_time)
    """
    result = transcribe_audio(audio_path, model_size)
    
    if not result:
        return []
    
    word_timings = []
    
    # Extract from segments with word-level data
    if "segments" in result:
        for segment in result["segments"]:
            if "words" in segment:
                for word_data in segment["words"]:
                    word = word_data.get("word", "").strip()
                    start = word_data.get("start", 0)
                    end = word_data.get("end", 0)
                    if word:
                        word_timings.append((word, start, end))
    
    return word_timings


def get_sentence_timings_from_whisper(audio_path: str, model_size: str = "base") -> List[Tuple[str, float, float]]:
    """
    Gets sentence-level timings using Whisper's segment detection.
    Whisper naturally segments by sentence/phrase.
    
    Returns:
        List of tuples: (sentence_text, start_time, end_time)
    """
    result = transcribe_audio(audio_path, model_size)
    
    if not result:
        return []
    
    sentence_timings = []
    
    if "segments" in result:
        for segment in result["segments"]:
            text = segment.get("text", "").strip()
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            if text:
                sentence_timings.append((text, start, end))
    
    return sentence_timings


def save_transcription_cache(audio_path: str, result: Dict, cache_dir: Optional[str] = None):
    """
    Saves transcription result to cache file for reuse.
    """
    if cache_dir is None:
        cache_dir = os.path.dirname(audio_path)
    
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    cache_path = os.path.join(cache_dir, f"{base_name}_whisper.json")
    
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    print(f"[Whisper] Cached transcription: {cache_path}")
    return cache_path


def load_transcription_cache(audio_path: str, cache_dir: Optional[str] = None) -> Optional[Dict]:
    """
    Loads cached transcription if available.
    """
    if cache_dir is None:
        cache_dir = os.path.dirname(audio_path)
    
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    cache_path = os.path.join(cache_dir, f"{base_name}_whisper.json")
    
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return None


def transcribe_with_caching(audio_path: str, model_size: str = "base") -> Optional[Dict]:
    """
    Transcribes audio with caching support to avoid re-processing.
    """
    # Check cache first
    cached = load_transcription_cache(audio_path)
    if cached:
        print(f"[Whisper] Using cached transcription for {os.path.basename(audio_path)}")
        return cached
    
    # Generate new transcription
    result = transcribe_audio(audio_path, model_size)
    
    if result:
        save_transcription_cache(audio_path, result)
    
    return result


if __name__ == "__main__":
    # Test with hook audio
    import sys
    
    test_audio = "assets/run_20260111_081251/audio_hook.mp3"
    
    if os.path.exists(test_audio):
        print("Testing Whisper transcription...")
        print("-" * 50)
        
        # Get sentence timings
        sentences = get_sentence_timings_from_whisper(test_audio, "base")
        
        print(f"\nFound {len(sentences)} segments:")
        for i, (text, start, end) in enumerate(sentences):
            print(f"{i+1}. [{start:.2f}s - {end:.2f}s] {text[:60]}...")
        
        # Get word timings (first 20)
        words = get_word_timings(test_audio, "base")
        
        print(f"\nFirst 20 words with timestamps:")
        for word, start, end in words[:20]:
            print(f"  [{start:.2f}s - {end:.2f}s] '{word}'")
    else:
        print(f"Test file not found: {test_audio}")
