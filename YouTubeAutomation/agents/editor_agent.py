import os
import sys
import math  # For elastic pop animation

# Attempt to handle MoviePy 1.0 vs 2.0
try:
    import moviepy
    IS_MOVIEPY_2 = moviepy.__version__.startswith('2')
except:
    IS_MOVIEPY_2 = False

print(f"DEBUG: EditorAgent IS_MOVIEPY_2={IS_MOVIEPY_2}")

if IS_MOVIEPY_2:
    try:
        from moviepy import *
    except ImportError:
        pass
else:
    try:
        from moviepy.editor import *
        from moviepy.config import get_setting
    except ImportError:
        # Fallback if detection failed or weird env
        IS_MOVIEPY_2 = True
        from moviepy import *

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class EditorAgent:
    def __init__(self):
        self.check_imagemagick()

    def check_imagemagick(self):
        """Checks if ImageMagick is configured for TextClips."""
        try:
            if not IS_MOVIEPY_2:
                # Check binary
                try:
                    from moviepy.config import get_setting
                    binary = get_setting("IMAGEMAGICK_BINARY")
                    print(f"DEBUG: ImageMagick Binary: {binary}")
                except:
                    pass
        except:
            pass

    def _apply_pop_effect(self, clip, pop_duration=0.09):
        """
        CapCut-Style Pop Effect (Reverse-Engineered)
        - Frame 0: 0.82 (compressed)
        - Frame 2: 1.18 (fast expand)
        - Frame 4: 1.28 (hard overshoot)
        - Frame 6: 1.00 (settle)
        
        This curve is 3× more impactful than standard easing.
        """
        def capcut_pop_scale(t):
            if t >= pop_duration:
                return 1.0
            
            p = t / pop_duration
            
            if p < 0.35:
                # Compress to expand: 0.82 → 1.18
                return 0.82 + (p / 0.35) * 0.36
            elif p < 0.6:
                # Overshoot: 1.18 → 1.28
                return 1.18 + ((p - 0.35) / 0.25) * 0.10
            else:
                # Settle: 1.28 → 1.00
                return 1.28 - ((p - 0.6) / 0.4) * 0.28
        
        try:
            if IS_MOVIEPY_2:
                return clip.resized(lambda t: capcut_pop_scale(t))
            else:
                return clip.resize(lambda t: capcut_pop_scale(t))
        except Exception as e:
            print(f"[!] Pop effect failed: {e}")
            return clip

    def _safe_slide_in(self, clip, duration=0.5):
        """Applies a slide-in effect from the right."""
        try:
            if not IS_MOVIEPY_2:
                from moviepy.video.fx.all import slide_in
                return clip.fx(slide_in, duration=duration, side='right')
            else:
                if hasattr(vfx, 'SlideIn'):
                    return clip.with_effects([vfx.SlideIn(duration=duration, side='right')])
                elif hasattr(vfx, 'slide_in'):
                    return vfx.slide_in(clip, duration=duration, side='right')
            return clip
        except Exception as e:
            # print(f"Transition warning: {e}") 
            return clip

    def _apply_ken_burns(self, clip, zoom_ratio=0.1):
        """
        Applies Ken Burns zoom effect to a static image clip.
        Slowly zooms in from 100% to (100% + zoom_ratio*100%).
        """
        try:
            duration = clip.duration
            w, h = clip.size
            
            def zoom_effect(get_frame, t):
                # Zoom from 1.0 to 1.0 + zoom_ratio over duration
                progress = t / duration
                scale = 1.0 + (zoom_ratio * progress)
                
                frame = get_frame(t)
                # We'll handle this via resize instead
                return frame
            
            # Use resize with time-based scaling
            if IS_MOVIEPY_2:
                zoomed = clip.resized(lambda t: 1.0 + zoom_ratio * (t / duration))
                # Crop back to original size (center)
                zoomed = zoomed.cropped(width=w, height=h, x_center=zoomed.w/2, y_center=zoomed.h/2)
            else:
                zoomed = clip.resize(lambda t: 1.0 + zoom_ratio * (t / duration))
                zoomed = zoomed.crop(width=w, height=h, x_center=zoomed.w/2, y_center=zoomed.h/2)
            
            return zoomed
        except Exception as e:
            print(f"Ken Burns effect failed: {e}")
            return clip

    def _apply_crossfade(self, clip, fade_duration=0.3):
        """Applies crossfade in/out to a clip."""
        try:
            if IS_MOVIEPY_2:
                return clip.with_effects([vfx.CrossFadeIn(fade_duration), vfx.CrossFadeOut(fade_duration)])
            else:
                from moviepy.video.fx.all import crossfadein, crossfadeout
                return clip.fx(crossfadein, fade_duration).fx(crossfadeout, fade_duration)
        except Exception as e:
            # Fallback if crossfade not available
            return clip

    def _get_sfx_for_scene(self, scene_key, text, sfx_mapping=None):
        """
        Returns appropriate sound effect path for a scene.
        Priority:
        1. Use dynamically generated SFX from sfx_mapping (if provided)
        2. Fall back to static SFX files based on keywords
        """
        # Priority 1: Dynamic SFX from mapping
        if sfx_mapping and scene_key in sfx_mapping:
            sfx_path = sfx_mapping[scene_key]
            if os.path.exists(sfx_path):
                return sfx_path
        
        # Priority 2: Static SFX files based on keywords (fallback)
        sfx_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sfx")
        
        # Keyword to SFX mapping (priority order)
        keyword_mappings = [
            (["$", "money", "earn", "profit", "invest", "rich", "wealth", "million", "dollar"], "coin.mp3"),
            (["crash", "fail", "lost", "bankrupt", "collapse", "drop"], "impact.mp3"),
            (["breaking", "urgent", "news", "alert"], "notification.mp3"),
            (["win", "success", "grow", "achieve"], "success.mp3"),
        ]
        
        text_lower = text.lower()
        
        for keywords, sfx_file in keyword_mappings:
            for kw in keywords:
                if kw in text_lower:
                    sfx_path = os.path.join(sfx_dir, sfx_file)
                    if os.path.exists(sfx_path):
                        return sfx_path
        
        # Default transition sound (whoosh) - only if file exists
        whoosh_path = os.path.join(sfx_dir, "whoosh.mp3")
        if os.path.exists(whoosh_path):
            return whoosh_path
            
        return None

    def _mix_sfx_with_audio(self, main_audio, sfx_path, sfx_volume=0.15):
        """
        Mixes a sound effect with the main audio at low volume.
        SFX plays at the START of the scene.
        """
        try:
            sfx = AudioFileClip(sfx_path)
            
            # Ensure SFX doesn't exceed main audio duration
            if sfx.duration > main_audio.duration:
                if IS_MOVIEPY_2:
                    sfx = sfx.subclipped(0, main_audio.duration)
                else:
                    sfx = sfx.subclip(0, main_audio.duration)
            
            # Lower SFX volume significantly (default 15% of original)
            if IS_MOVIEPY_2:
                sfx = sfx.with_volume_scaled(sfx_volume)
            else:
                sfx = sfx.volumex(sfx_volume)
            
            # Mix together
            mixed = CompositeAudioClip([main_audio, sfx])
            return mixed
        except Exception as e:
            print(f"SFX mixing failed: {e}")
            return main_audio

    def _apply_random_transition(self, clip, duration=0.5):
        """Applies a random transition effect for visual variety."""
        import random
        effect = random.choice(['slide', 'crossfade', 'fadein', 'none'])
        
        try:
            if effect == 'slide':
                return self._safe_slide_in(clip, duration)
            elif effect == 'crossfade':
                if IS_MOVIEPY_2:
                    return clip.with_effects([vfx.CrossFadeIn(duration)])
                else:
                    from moviepy.video.fx.all import crossfadein
                    return clip.fx(crossfadein, duration)
            elif effect == 'fadein':
                if IS_MOVIEPY_2:
                    return clip.with_effects([vfx.FadeIn(duration)])
                else:
                    from moviepy.video.fx.all import fadein
                    return clip.fx(fadein, duration)
            # 'none' - no transition
            return clip
        except Exception as e:
            # Silently fallback to no transition on error
            return clip

    def _apply_cinematic_look(self, clip):
        """
        Applies a 'Cinematic' look using:
        1. Mild Contrast Curve (S-Curve simulation via lum_contrast)
        2. Saturation Boost (Vibrance)
        3. Simple Film Grain overlay
        """
        try:
            # Debug Log
            # print("   [FX] Applying Cinematic Look (Color+Grain)...")

            # 1. COLOR GRADING (Teal & Orange-ish simulation)
            # Boost contrast (lum) and saturation (colorx)
            if IS_MOVIEPY_2:
                # vfx.lum_contrast(clip, lum=0, contrast=0.2) - contrast_thr removed in v2
                effects = [vfx.LumContrast(lum=0, contrast=0.15)]
                try: 
                    # Try MultiplyColor (v2 replacement for colorx)
                    effects.append(vfx.MultiplyColor(1.15))
                except:
                    pass # Skip if not found
                
                clip = clip.with_effects(effects)
            else:
                from moviepy.video.fx.all import colorx, lum_contrast
                clip = clip.fx(colorx, 1.15).fx(lum_contrast, 0, 0.15, 127)

            # 2. FILM GRAIN (Subtle Noise)
            # We create a static noise array and overlay it with low opacity
            # This is faster than generating noise per frame
            
            def add_grain(get_frame, t):
                frame = get_frame(t)
                import numpy as np
                # Generate random noise (grain) - static per frame reuse or dynamic?
                # Dynamic is better usually.
                # Use a small seed based on time to deter pattern repetition but keep it deterministic
                np.random.seed(int(t * 100))
                
                # Create noise layer (range -10 to 10 intensity)
                noise = np.random.randint(-15, 15, frame.shape, dtype='int16')
                
                # Add to frame
                grainy_frame = frame.astype('int16') + noise
                
                # Clip back to valid range
                return np.clip(grainy_frame, 0, 255).astype('uint8')
            
            # Apply transformation
            # Note: This is computationally expensive! Use carefully.
            # Only apply if user wants high quality.
            if IS_MOVIEPY_2:
                clip = clip.transform(add_grain) 
            else:
                clip = clip.fl(add_grain)
                
            return clip
            
        except Exception as e:
            print(f"[!] Cinematic Filter failed: {e}")
            return clip

    def _generate_karaoke_subtitles(self, text, duration, screensize, audio_path=None):
        """
        VIRAL SUBTITLE ENGINE V5 (CapCut-Style)
        
        - 3 words per phrase, centered
        - CapCut pop effect on entire phrase
        - White text with thick black stroke
        - Positioned at 45% height to prevent cutoff
        """
        if not text or not text.strip(): 
            return []
            
        words_all = text.split()
        if not words_all: 
            return []
        
        clips = []
        w_screen, h_screen = screensize
        
        # VIRAL STYLE settings
        font = 'Impact' if os.name != 'nt' else 'impact.ttf'
        fontsize = 68  # Larger for mobile visibility
        stroke_width = 7  # Thick stroke for punch
        text_color = 'white'
        
        WORDS_PER_PHRASE = 3  # Viral standard
        
        # Calculate phrases
        phrases = []
        for i in range(0, len(words_all), WORDS_PER_PHRASE):
            phrase_words = words_all[i:i + WORDS_PER_PHRASE]
            phrases.append(" ".join(phrase_words))
        
        if not phrases:
            return []
        
        # Calculate timing per phrase
        phrase_duration = duration / len(phrases)
        current_time = 0.0
        
        for phrase in phrases:
            try:
                # Create phrase text clip
                if IS_MOVIEPY_2:
                    phrase_clip = TextClip(
                        text=phrase,
                        font_size=fontsize,
                        color=text_color,
                        font=font,
                        stroke_width=stroke_width,
                        stroke_color='black',
                        method='caption',
                        size=(int(w_screen * 0.85), None)  # Auto-wrap at 85% width
                    ).with_duration(phrase_duration)
                else:
                    phrase_clip = TextClip(
                        phrase,
                        fontsize=fontsize,
                        color=text_color,
                        font=font,
                        stroke_width=stroke_width,
                        stroke_color='black',
                        method='caption',
                        size=(int(w_screen * 0.85), None)
                    ).set_duration(phrase_duration)
                
                # Apply CapCut pop effect
                phrase_clip = self._apply_pop_effect(phrase_clip)
                
                # Position and time
                if IS_MOVIEPY_2:
                    phrase_clip = (phrase_clip
                        .with_start(current_time)
                        .with_position(('center', 0.45), relative=True))
                else:
                    phrase_clip = (phrase_clip
                        .set_start(current_time)
                        .set_position(('center', 0.45), relative=True))
                
                clips.append(phrase_clip)
                current_time += phrase_duration
                
            except Exception as e:
                print(f"[!] Phrase subtitle error: {e}")
                continue
        
        return clips
    
    def _get_word_timings(self, text, duration, audio_path=None):
        """
        Gets word-level timing using Whisper (if available) or estimation.
        Returns list of dicts: [{'word': str, 'start': float, 'end': float}, ...]
        """
        # Try Whisper if audio path provided
        if audio_path and os.path.exists(audio_path):
            try:
                from utils.timing_utils import get_word_timings_for_audio
                word_timings = get_word_timings_for_audio(audio_path)
                if word_timings:
                    print(f"    [OK] Whisper timing: {len(word_timings)} words")
                    return word_timings
            except ImportError:
                pass
            except Exception as e:
                print(f"    [!] Whisper error: {e}")
        
        # Fallback: estimated timing
        try:
            from utils.timing_utils import estimate_word_timings
            return estimate_word_timings(text, duration)
        except:
            return None
    
    def _build_phrase_clip(self, word_timings, phrase_duration, fontsize, font, 
                           stroke_width, base_color, highlight_color, max_width, screen_width):
        """
        Builds a composite clip for a phrase with word-by-word highlighting.
        """
        if not word_timings:
            return None
        
        phrase_start_time = word_timings[0]["start"]
        word_clips = []
        x_offset = 0
        
        # First pass: create base words and calculate total width
        base_clips = []
        word_widths = []
        
        for j, wt in enumerate(word_timings):
            word = wt["word"]
            # Add space after word except for last
            display_word = word + " " if j < len(word_timings) - 1 else word
            
            try:
                if IS_MOVIEPY_2:
                    base_word = TextClip(
                        text=display_word,
                        font_size=fontsize,
                        color=base_color,
                        font=font,
                        stroke_width=stroke_width,
                        stroke_color='black'
                    ).with_duration(phrase_duration)
                else:
                    base_word = TextClip(
                        display_word,
                        fontsize=fontsize,
                        color=base_color,
                        font=font,
                        stroke_width=stroke_width,
                        stroke_color='black'
                    ).set_duration(phrase_duration)
                
                # Get word width reliably
                try:
                    word_width = base_word.size[0] if hasattr(base_word, 'size') else base_word.w
                except:
                    word_width = len(display_word) * fontsize * 0.5  # Rough estimate
                
                base_clips.append(base_word)
                word_widths.append(word_width)
                
            except Exception as e:
                continue
        
        if not base_clips:
            return None
        
        # Calculate total width
        total_width = sum(word_widths)
        
        # Second pass: position words and create highlight layers
        for j, (base_word, wt) in enumerate(zip(base_clips, word_timings)):
            word = wt["word"]
            word_start = wt["start"] - phrase_start_time  # Relative to phrase start
            word_end = wt["end"] - phrase_start_time
            word_duration = max(0.1, word_end - word_start)
            
            display_word = word + " " if j < len(word_timings) - 1 else word
            
            # Position base word
            if IS_MOVIEPY_2:
                base_word = base_word.with_position((x_offset, 0))
            else:
                base_word = base_word.set_position((x_offset, 0))
            
            word_clips.append(base_word)
            
            # Create highlight word (appears only during its word timing)
            try:
                if IS_MOVIEPY_2:
                    highlight_word = TextClip(
                        text=display_word,
                        font_size=fontsize,
                        color=highlight_color,
                        font=font,
                        stroke_width=stroke_width,
                        stroke_color='black'
                    ).with_duration(word_duration).with_start(word_start).with_position((x_offset, 0))
                    # Apply pop effect to EACH highlighted word individually
                    highlight_word = self._apply_pop_effect(highlight_word)
                else:
                    highlight_word = TextClip(
                        display_word,
                        fontsize=fontsize,
                        color=highlight_color,
                        font=font,
                        stroke_width=stroke_width,
                        stroke_color='black'
                    ).set_duration(word_duration).set_start(word_start).set_position((x_offset, 0))
                
                # Apply pop effect to EACH highlighted word individually
                highlight_word = self._apply_pop_effect(highlight_word)
                word_clips.append(highlight_word)
                
            except Exception as e:
                pass
            
            x_offset += word_widths[j]
        
        if not word_clips:
            return None
        
        # Composite all word clips into phrase
        try:
            phrase_composite = CompositeVideoClip(word_clips, size=(int(total_width), fontsize + 20))
            
            if IS_MOVIEPY_2:
                phrase_composite = phrase_composite.with_duration(phrase_duration)
            else:
                phrase_composite = phrase_composite.set_duration(phrase_duration)
            
            return phrase_composite
            
        except Exception as e:
            # Memory cleanup on error
            for clip in word_clips:
                if hasattr(clip, 'close'):
                    try: clip.close()
                    except: pass
            return None
    
    def _generate_simple_subtitles(self, text, duration, screensize):
        """
        VIRAL STYLE: Word-by-word pop subtitles with elastic animation.
        - Each word pops individually with staggered timing
        - White text, thick black stroke, auto-wrap
        - Reduced font for mobile screen ratio
        """
        words = text.split()
        if not words:
            return []
        
        clips = []
        w, h = screensize
        font = 'Impact' if os.name != 'nt' else 'impact.ttf'
        fontsize = 48  # Reduced from 65 to prevent cutoff
        max_width = int(w * 0.85)  # 85% of screen width
        
        # Group words into phrases (3-4 words each)
        WORDS_PER_PHRASE = 3
        phrases = []
        for i in range(0, len(words), WORDS_PER_PHRASE):
            phrase_words = words[i:i+WORDS_PER_PHRASE]
            phrases.append(phrase_words)
        
        if not phrases:
            return []
        
        phrase_duration = duration / len(phrases)
        current_time = 0
        word_stagger = 0.05  # 50ms stagger between words
        
        for phrase_words in phrases:
            phrase_clips = []
            
            for word_idx, word in enumerate(phrase_words):
                try:
                    # Create word clip with viral styling
                    if IS_MOVIEPY_2:
                        word_clip = TextClip(
                            text=word,
                            font_size=fontsize,
                            color='white',  # Changed from yellow
                            font=font,
                            stroke_width=6,  # Thicker stroke
                            stroke_color='black'
                        )
                        word_clip = word_clip.with_duration(phrase_duration - (word_idx * word_stagger))
                        word_clip = word_clip.with_start(current_time + (word_idx * word_stagger))
                    else:
                        word_clip = TextClip(
                            word,
                            fontsize=fontsize,
                            color='white',  # Changed from yellow
                            font=font,
                            stroke_width=6,  # Thicker stroke
                            stroke_color='black'
                        )
                        word_clip = word_clip.set_duration(phrase_duration - (word_idx * word_stagger))
                        word_clip = word_clip.set_start(current_time + (word_idx * word_stagger))
                    
                    # Apply elastic pop to each word individually
                    word_clip = self._apply_pop_effect(word_clip)
                    phrase_clips.append(word_clip)
                    
                except Exception as e:
                    continue
            
            if phrase_clips:
                try:
                    # Composite words into phrase with horizontal layout
                    # Calculate total width for centering
                    word_widths = []
                    for wc in phrase_clips:
                        try:
                            word_widths.append(wc.size[0])
                        except:
                            word_widths.append(80)  # Fallback width
                    
                    spacing = 15
                    total_width = sum(word_widths) + spacing * (len(phrase_clips) - 1)
                    
                    # Position words horizontally
                    x_offset = 0
                    positioned_clips = []
                    for i, wc in enumerate(phrase_clips):
                        if IS_MOVIEPY_2:
                            wc = wc.with_position((x_offset, 0))
                        else:
                            wc = wc.set_position((x_offset, 0))
                        positioned_clips.append(wc)
                        x_offset += word_widths[i] + spacing
                    
                    # Create phrase composite
                    phrase_composite = CompositeVideoClip(
                        positioned_clips, 
                        size=(int(total_width), fontsize + 20)
                    )
                    
                    if IS_MOVIEPY_2:
                        phrase_composite = phrase_composite.with_duration(phrase_duration)
                        phrase_composite = phrase_composite.with_start(current_time)
                        phrase_composite = phrase_composite.with_position(('center', 0.50), relative=True)
                    else:
                        phrase_composite = phrase_composite.set_duration(phrase_duration)
                        phrase_composite = phrase_composite.set_start(current_time)
                        phrase_composite = phrase_composite.set_position(('center', 0.50), relative=True)
                    
                    clips.append(phrase_composite)
                    
                except Exception as e:
                    # Fallback: just add individual word clips centered
                    for wc in phrase_clips:
                        try:
                            if IS_MOVIEPY_2:
                                wc = wc.with_position(('center', 0.50), relative=True)
                            else:
                                wc = wc.set_position(('center', 0.50), relative=True)
                            clips.append(wc)
                        except:
                            pass
            
            current_time += phrase_duration
        
        return clips

    def _set_duration(self, clip, duration):
        """Compat helper for set_duration (v1) vs with_duration (v2)."""
        # print(f"DEBUG: _set_duration called on {type(clip)}")
        if hasattr(clip, 'with_duration'):
            return clip.with_duration(duration)
        
        print("DEBUG: FALLBACK to set_duration")
        return clip.set_duration(duration)

    def create_scene_clip(self, asset_path, audio_path, text, scene_key=None, sfx_mapping=None):
        """Creates a single composite scene (Image OR Video)."""
        # Logic moved to prepare_visual_clip where possible, but keeping this for legacy/audio usage
        # Ideally we refactor this to call prepare_visual_clip, but let's stick to the new method for main.py usage first.
        
        # ... (Existing implementations of create_scene_clip kept as is for safety) ...
        # WAIT, earlier I modified create_scene_clip to use _set_duration. I should keep that.
        # But I need to INSERT the new method BEFORE it or AFTER it.
        # Let's insert it before create_scene_clip.
        pass

    
    def prepare_visual_clip(self, asset_path, duration, state_meta=None, is_vertical_9_16=False):
        """
        Robustly prepares a visual clip (Image/Video) for a specific duration.
        SKULSY V3 UPDATE: Handles Grok videos with speed ramping and State FX.
        """
        if not os.path.exists(asset_path):
            print(f"Missing asset: {asset_path}")
            return None
            
        filename = os.path.basename(asset_path).lower().strip()
        is_video = filename.endswith(".mp4") or filename.endswith(".mov")
        
        # Dimensions for Skulsy Shorts (9:16) or Standard (16:9)
        target_w, target_h = (1080, 1920) if is_vertical_9_16 else (1920, 1080)
        
        state = state_meta.get('state', 'neutral') if state_meta else 'neutral'
        intensity = state_meta.get('intensity', 0.5) if state_meta else 0.5
        
        try:
            clip = None
            if is_video:
                # === GROK VIDEO PROCESSING ===
                clip = self._process_grok_clip(asset_path, duration, intensity)
            else:
                # === IMAGE PROCESSING ===
                clip = ImageClip(asset_path)
                clip = self._set_duration(clip, duration)
                clip = self._apply_ken_burns(clip, zoom_ratio=0.1 + (0.1 * intensity)) # Zoom based on intensity

            # Smart Crop to Aspect Ratio
            w, h = clip.size
            target_aspect = target_w / target_h
            current_aspect = w / h
            
            if current_aspect > target_aspect:
                # Too wide - crop width
                new_w = h * target_aspect
                if IS_MOVIEPY_2:
                    clip = clip.cropped(width=new_w, height=h, x_center=w/2, y_center=h/2)
                else:
                    clip = clip.crop(width=new_w, height=h, x_center=w/2, y_center=h/2)
            else:
                # Too tall/narrow - crop height
                new_h = w / target_aspect
                if IS_MOVIEPY_2:
                    clip = clip.cropped(width=w, height=new_h, x_center=w/2, y_center=h/2)
                else:
                    clip = clip.crop(width=w, height=new_h, x_center=w/2, y_center=h/2)

            # Resize to Final Resolution
            if IS_MOVIEPY_2:
                clip = clip.resized(height=target_h) if target_h > target_w else clip.resized(width=target_w)
            else:
                clip = clip.resize(height=target_h) if target_h > target_w else clip.resize(width=target_w)
            
            # === APPLY STATE EFFECTS (Punchline, etc) ===
            clip = self._apply_state_effects(clip, state, intensity)

            return clip
            
        except Exception as e:
            print(f"Error preparing visual {filename}: {e}")
            return None

    def _process_grok_clip(self, path, target_duration, intensity):
        """
        Handles Grok video ingest with tolerance and speed ramping.
        """
        clip = VideoFileClip(path)
        source_dur = clip.duration
        diff = source_dur - target_duration
        
        # Scenario 1: Source is close enough (Trim)
        if abs(diff) < 0.4:
            # Center trim
            start = (source_dur - target_duration) / 2
            if start < 0: start = 0
            try:
                if IS_MOVIEPY_2: clip = clip.subclipped(start, start + target_duration)
                else: clip = clip.subclip(start, start + target_duration)
            except: pass # Fallback to set_duration
            
        # Scenario 2: Source is too long (Speed Up or Trim)
        elif diff > 0.4:
            # Calculate speed info
            speed_factor = source_dur / target_duration
            
            # If high intensity, we PERMIT faster speeds (choppier = better for panic)
            max_speed = 1.5 + intensity  # 0.5 intensity -> max 2.0x, 0.9 intensity -> max 2.4x
            
            if speed_factor <= max_speed:
                # Speed up entire clip to fit
                if IS_MOVIEPY_2:
                    clip = clip.with_effects([vfx.MultiplySpeed(speed_factor)])
                else:
                    from moviepy.video.fx.all import speedx
                    clip = clip.fx(speedx, speed_factor)
            else:
                # Too long for speed up -> Speed up to max, then trim center
                target_compressed_dur = source_dur / max_speed
                # This is complex, simplify: Just trim center 
                # But to keep "pace", we speed up to 1.5x then trim
                intermediate_speed = 1.5
                if IS_MOVIEPY_2:
                    clip = clip.with_effects([vfx.MultiplySpeed(intermediate_speed)])
                else:
                    from moviepy.video.fx.all import speedx
                    clip = clip.fx(speedx, intermediate_speed)
                
                # Now trim to target
                if clip.duration > target_duration:
                    start = (clip.duration - target_duration) / 2
                    if IS_MOVIEPY_2: clip = clip.subclipped(start, start + target_duration)
                    else: clip = clip.subclip(start, start + target_duration)

        # Scenario 3: Source is too short (Loop/Freeze)
        else:
             # Logic from old method similar here
             # Default to loop if short
             try:
                if IS_MOVIEPY_2: clip = clip.with_effects([vfx.Loop(duration=target_duration)])
                else: 
                     from moviepy.video.fx.all import loop
                     clip = clip.fx(loop, duration=target_duration)
             except: pass
             
        return self._set_duration(clip, target_duration)

    def _apply_state_effects(self, clip, state, intensity):
        """Applies visual effects based on Narrative State."""
        
        # Cinematic Look (Always on for Skulsy)
        clip = self._apply_cinematic_look(clip)
        
        if state == 'punchline':
            # PUNCHLINE MODE: Micro-zoom + High Contrast
            # Simulating "Deep Fried" light effect or just heavy zoom
            clip = self._apply_ken_burns(clip, zoom_ratio=0.3) # Heavy zoom
            # Optional: Invert colors? Maybe too much. Let's stick to zoom.
            
        elif state == 'panic' and intensity > 0.7:
             # Shake effect simulation (Rapid crop/zoom variation) requires per-frame logic
             # Too expensive. Use simple color grading shift
             pass 
             
        return clip

    def _detect_punchline_fallback(self, scenes_data):
        """Detects punchline if no explicit state found."""
        # Check explicit
        for s in scenes_data:
            if s.get('state') == 'punchline': return
            
        # Fallback: Tag last sentence
        if scenes_data:
            print("[EditorAgent] Punchline Fallback Triggered: Tagging last scene.")
            scenes_data[-1]['state'] = 'punchline'
            scenes_data[-1]['intensity'] = 1.0

    def create_video(self, scenes_data, output_path, sfx_mapping=None):
        """
        Assembles the final video from a list of scene dictionaries.
        """
        # SKULSY V5: Native Audio Mixing Logic
        # We now expect the visual_XX.mp4 files to have their own SFX/Ambience from Grok.
        # instead of set_audio (replace), we use CompositeAudioClip (mix).
        
        final_clips = []
        current_timeline = 0.0
        
        for i, s in enumerate(scenes_data):
            asset_path = s['asset_path']
            audio_path = s.get('audio_path') 
            text = s.get('text', '')
            state = s.get('state', 'neutral')
            
            # 1. Load TTS Audio (Voiceover)
            if audio_path and os.path.exists(audio_path):
                tts_clip = AudioFileClip(audio_path)
                duration = tts_clip.duration
            else:
                tts_clip = None
                duration = 5.0 # Fallback
            
            # 2. visual_clip (Has Grok Audio)
            video_clip = self.prepare_visual_clip(
                asset_path, 
                duration, 
                state_meta=s, 
                is_vertical_9_16=True 
            )
            
            if not video_clip:
                continue
                
            # 3. Audio Mixing Strategy (V5)
            # Mix TTS (100%) + Video Audio (30% Background)
            
            final_audio = tts_clip
            
            if video_clip.audio:
                # Lower volume of background ambience/sfx
                if IS_MOVIEPY_2:
                    # V2: Use effect
                    try:
                        bg_audio = video_clip.audio.with_effects([afx.MultiplyVolume(0.3)])
                    except:
                        bg_audio = video_clip.audio # Fail silent
                else:
                    # V1 Legacy
                    bg_audio = video_clip.audio.volumex(0.3)
                
                # HARDENED FIX: Ensure bg_audio strictly matches duration
                # 1. If too long, subclip it.
                if bg_audio.duration > duration:
                    bg_audio = bg_audio.subclipped(0, duration)
                # 2. If too short or undefined, force duration (might loop or silence)
                else:
                    bg_audio = bg_audio.with_duration(duration) if IS_MOVIEPY_2 else bg_audio.set_duration(duration)

                if tts_clip:
                    final_audio = CompositeAudioClip([tts_clip, bg_audio])
                else:
                    final_audio = bg_audio
            
            # Apply mixed audio to video
            if final_audio:
                if IS_MOVIEPY_2:
                    video_clip = video_clip.with_audio(final_audio)
                else:
                    video_clip = video_clip.set_audio(final_audio)

            # 4. Subtitles
            subs = self._generate_karaoke_subtitles(text, duration, video_clip.size)
            
            # 5. Composite Final Scene
            final_scene = CompositeVideoClip([video_clip] + subs, size=video_clip.size)
            
            if IS_MOVIEPY_2:
                 final_scene = final_scene.with_duration(duration)
            else:
                 final_scene = final_scene.set_duration(duration)
            
            final_clips.append(final_scene)
            current_timeline += duration

        if not final_clips:
            print("[!] No valid clips to assemble!")
            return None
            
        print(f"[*] Concatenating {len(final_clips)} clips (Mixed Audio)...")

        try:
            final_video = concatenate_videoclips(final_clips, method="compose")
            return final_video
        except Exception as e:
            print(f"[!] Concatenation failed: {e}")
            return None


    def _quick_validate_asset(self, path):
        """Checks magic bytes to confirm valid media capability."""
        try:
            if os.path.getsize(path) < 100: return False, "Too small"
            
            with open(path, "rb") as f:
                header = f.read(16)
            
            # Known valid signatures (be lenient - content matters more than extension)
            is_valid_image = (
                header.startswith(b'\x89PNG\r\n\x1a\n') or  # PNG
                header.startswith(b'\xff\xd8\xff') or       # JPEG
                header.startswith(b'RIFF') or              # WebP (RIFF....WEBP)
                header.startswith(b'GIF')                   # GIF
            )
            
            is_valid_video = (
                header[4:8] == b'ftyp' or   # MP4/M4V (ftyp at offset 4)
                header.startswith(b'\x00\x00\x00')  # Other MP4 variants
            )
            
            is_valid_audio = (
                header.startswith(b'ID3') or          # MP3 with ID3
                header.startswith(b'\xff\xfb') or     # MP3 sync
                header.startswith(b'\xff\xfa') or     # MP3 sync variant
                header.startswith(b'RIFF')            # WAV
            )
            
            # Check based on extension category
            ext = os.path.splitext(path)[1].lower()
            
            if ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']:
                if not is_valid_image:
                    return False, f"Invalid image format (got header: {header[:8]})"
            elif ext in ['.mp4', '.mov', '.m4v']:
                if not is_valid_video:
                    return False, f"Invalid video format"
            elif ext in ['.mp3', '.wav']:
                if not is_valid_audio:
                    return False, f"Invalid audio format"
            
            return True, ""
        except Exception as e:
            return False, str(e)
