from utils.llm_client import LLMClient
import json

class VisualAgent:
    """
    Enhanced Visual Agent with CFH-style metaphor system.
    
    Key Features:
    - Converts abstract concepts into physical symbols
    - Adds emotional character reactions
    - Uses scale and drama for impact
    - Maintains visual consistency across scenes
    """
    
    def __init__(self):
        self.llm = LLMClient()
        
        # Character consistency tracker
        self.primary_character = None

        # --- VISUAL STYLE CONSTANTS ---
        self.STYLE_PREFIX = (
            "Cinematic YouTube explainer thumbnail illustration in clean vector cartoon style, "
            "editorial political and economic illustration, bold outlines, flat shading with subtle gradients, "
            "high contrast dramatic lighting, professional YouTube finance channel aesthetic, "
            "Foreground: a stylized cartoon character in a business suit, expressive face, dramatic reaction, "
            "consistent character design across images, Scene: "
        )
        
        self.STYLE_SUFFIX = (
            ", Background: symbolic elements related to geopolitics and economics, fire, smoke, cracked structures, "
            "money, national symbols, cinematic depth and clear visual hierarchy, "
            "Mood: tense, dramatic, serious, thought-provoking, Composition: thumbnail-friendly, central subject, "
            "rule of thirds, designed to maximize YouTube click-through rate, Ultra high quality, sharp focus, 16:9"
        )
    
    
    def generate_image_prompts(self, script_data, num_prompts=20, sentences=None, skulsy_mode=False):
        """
        Generates visual prompts. Supports standard Metaphor mode and new Skulsy Mode.
        """
        topic = script_data.get('title', '')
        
        if skulsy_mode:
            print("[VisualAgent] Entering Skulsy Grok Mode...")
            self.primary_character = "Skulsy the Skeleton"
            # In Skulsy mode, 'sentences' input is expected (list of dicts with state/intensity)
            return self._generate_grok_prompts(sentences)
            
        self.primary_character = self._define_primary_character(topic)
        print(f"[VisualAgent] Primary Character: {self.primary_character}")
        
        if sentences:
            return self._generate_metaphor_prompts_strict(sentences, script_data)
        else:
            return self._generate_metaphor_prompts_distributed(script_data, num_prompts)

    def generate_dual_layer_prompts(self, sentences):
        """
        SKULSY V5: Dual-Layer Prompt Generation.
        Layer 1 (Image): Static Scene, Lighting, Character Pose (for Whisk/Imagen).
        Layer 2 (Video): Motion, Physics, Camera Move (for Grok).
        
        Returns: list of dicts with 'image_prompt' and 'video_prompt'.
        """
        prompts = []
        
        for i, s in enumerate(sentences):
            text = s.get('text', '')
            state = s.get('state', 'neutral')
            anchor = s.get('timeline_anchor')
            visual_cue = s.get('visual_cue', '')
            
            # --- LAYER 1: REFERENCE IMAGE (The Look) ---
            # Focus: Lighting, Composition, Detail, Style
            img_prompt = "Cinematic 2D vector illustration in an adult animated sitcom style. "
            img_prompt += "Thick black outlines, flat pastel colors, simple rounded character proportions, clean geometric shapes. "
            img_prompt += f"SUBJECT: Skulsy the skeleton {visual_cue}. "
            img_prompt += f"EMOTION: {self._get_expression(state)}. "
            if anchor:
                img_prompt += f"SETTING: {anchor}-era environment with period-authentic details. "
            img_prompt += "LIGHTING: High contrast lighting with dramatic shadows. "
            img_prompt += "STYLE: Professional animated series screenshot, sharp focus, clean composition, 4K-quality vector art."
            
            # --- LAYER 2: VIDEO MOTION (The Action) ---
            # Focus: Movement, Camera, Physics - NO LIPSYNC
            vid_prompt = "Animate this scene. "
            vid_prompt += f"ACTION: {visual_cue}. "
            vid_prompt += "CAMERA: Slow cinematic output zoom. "
            vid_prompt += "AUDIO: Ambient room tone, subtle movement sounds. " 
            vid_prompt += "CONSTRAINT: Character keeps mouth CLOSED. No talking. No lip-sync."
            
            prompts.append({
                "filename": f"visual_{i+1:02d}.mp4",
                "image_filename": f"ref_{i+1:02d}.png",
                "type": "video_with_ref",
                "image_prompt": img_prompt,
                "video_prompt": vid_prompt,
                "state": state,
                "anchor": anchor
            })
            
        return prompts

    def _get_expression(self, state):
        return {
            "hook": "shocked, jaw dropped",
            "optimism": "arrogant, smug, holding money",
            "doubt": "sweating, nervous side-eye",
            "panic": "terrified, shaking, eyes popping",
            "regret": "depressed, slumped shoulders, dead inside",
            "punchline": "deadpan stare directly at camera"
        }.get(state, "neutral")

    
    def _define_primary_character(self, topic):
        """
        Defines the recurring character archetype based on topic.
        Ensures visual consistency across the video.
        """
        
        # Map topics to character archetypes
        character_map = {
            "energy": "A middle-aged engineer in a hard hat and work vest",
            "debt": "A stressed businessman in an expensive but wrinkled suit",
            "crisis": "A government official in a dark suit looking exhausted",
            "war": "A military strategist in uniform studying maps",
            "trade": "A worried CEO in a boardroom with charts",
            "housing": "A young professional couple looking at house prices",
            "finance": "A Wall Street trader in shirt and tie, loosened",
            "tech": "A startup founder in casual clothes, bags under eyes"
        }
        
        topic_lower = topic.lower()
        
        # Match keywords
        for keyword, character in character_map.items():
            if keyword in topic_lower:
                return character
        
        # Default
        return "A concerned middle-aged professional in business attire"
    
    def _generate_metaphor_prompts_strict(self, sentences, script_data):
        """
        Generates 1 prompt per sentence with metaphor enhancement.
        """
        
        print(f"[VisualAgent] Generating metaphor-enhanced prompts for {len(sentences)} sentences...")
        
        # Process in batches to avoid token limits
        batch_size = 8
        all_prompts = []
        
        for batch_idx in range(0, len(sentences), batch_size):
            batch = sentences[batch_idx:batch_idx + batch_size]
            
            batch_prompts = self._process_batch_with_metaphors(
                batch, 
                batch_idx,
                script_data
            )
            
            all_prompts.extend(batch_prompts)
        
        return all_prompts
    
    def _process_batch_with_metaphors(self, batch, start_idx, script_data):
        # Processes a batch of sentences through the metaphor enhancement pipeline.
        
        # Build metaphor enhancement prompt using concatenation
        
        # Build metaphor enhancement prompt using concatenation
        mp = f"You are a Visual Metaphor Director for \"Chill Financial Historian\" - a viral YouTube channel.\n\n"
        mp += f"PRIMARY CHARACTER: {self.primary_character}\n"
        mp += "(This character should appear in MOST scenes for visual consistency)\n\n"
        
        mp += "VISUAL STYLE RULES:\n"
        mp += "1. **MAKE ABSTRACT CONCEPTS PHYSICAL**:\n"
        mp += "   - Debt = Heavy chains, crushing weights, giant boulders\n"
        mp += "   - Crisis = Fire, cracks spreading, structures crumbling\n"
        mp += "   - Growth = Trees sprouting, buildings rising, light beams\n"
        mp += "   - Decline = Rust, decay, falling objects, closing doors\n"
        mp += "   - Money = Coins falling, cash burning, vaults opening/closing\n"
        mp += "   - Time = Giant clocks, hourglasses, calendars pages flying\n\n"
        
        mp += "2. **USE SCALE FOR IMPACT**:\n"
        mp += "   - Make symbols GIANT (e.g., \"a massive euro symbol made of crumbling concrete\")\n"
        mp += "   - Make people small in comparison (shows helplessness)\n"
        mp += "   - Use wide shots showing scale contrast\n\n"
        
        mp += "3. **ADD EMOTIONAL REACTIONS**:\n"
        mp += "   - Character expressions: shocked eyes, sweating, hair gripping, yelling\n"
        mp += "   - Body language: running, falling, shielding face, pointing accusingly\n"
        mp += "   - Never neutral - always dramatic emotion\n\n"
        
        mp += "INPUT SENTENCES:\n"
        mp += f"{self._format_batch_for_prompt(batch, start_idx)}\n\n"
        
        mp += "TASK:\n"
        mp += "For each sentence, create a SYMBOLIC visual description.\n\n"
        
        mp += "OUTPUT FORMAT (JSON array):\n"
        mp += "[\n"
        mp += "  {\n"
        mp += f"    \"index\": {start_idx},\n"
        mp += "    \"type\": \"image\",\n"
        mp += "    \"literal_subject\": \"Brief description\",\n"
        mp += "    \"metaphor\": \"Physical symbol\",\n"
        mp += "    \"character_action\": \"Action\",\n"
        mp += "    \"scene_description\": \"Detailed description of CENTRAL ACTION only\",\n"
        mp += "    \"full_prompt\": \"(Optional legacy field)\"\n"
        mp += "  },\n"
        mp += "  ...\n"
        mp += "]\n"
        
        # Call LLM
        try:
            response = self.llm.generate_json(mp)
            batch_results = json.loads(response)
            
            prompts = []
            for item in batch_results:
                idx = item.get('index', start_idx)
                
                # STRICT PROMPT CONSTRUCTION
                scene_core = item.get('scene_description', item.get('full_prompt', ''))
                
                # Cleanup
                scene_core = scene_core.replace("Cinematic vector art", "").replace("16:9", "").strip()
                if scene_core.lower().startswith("scene:"): scene_core = scene_core[6:].strip()
                
                final_prompt = f"{self.STYLE_PREFIX}{scene_core}{self.STYLE_SUFFIX}"
                
                prompts.append({
                    "filename": f"visual_{idx+1:03d}.png",
                    "type": item.get('type', 'image'),
                    "prompt": final_prompt,
                    "metaphor_data": {
                        "literal": item.get('literal_subject', ''),
                        "symbol": item.get('metaphor', ''),
                        "character": item.get('character_action', '')
                    }
                })
            
            return prompts
            
        except Exception as e:
            print(f"  [!] Metaphor batch failed: {e}")
            return self._fallback_literal_prompts(batch, start_idx)
    
    def _fallback_literal_prompts(self, batch, start_idx):
        """Fallback if metaphor generation fails."""
        prompts = []
        for i, sentence in enumerate(batch):
            # Even fallback gets the nice style
            scene = f"Conceptual illustration related to: {sentence[:100]}"
            final_prompt = f"{self.STYLE_PREFIX}{scene}{self.STYLE_SUFFIX}"
            
            prompts.append({
                "filename": f"visual_{start_idx + i + 1:03d}.png",
                "type": "image",
                "prompt": final_prompt
            })
        return prompts
    
    def _format_batch_for_prompt(self, batch, start_idx):
        """Formats batch as numbered list for LLM."""
        return "\n".join([
            f"{start_idx + i}. {sentence}"
            for i, sentence in enumerate(batch)
        ])
    
    def generate_thumbnail_prompt(self, script_data):
        # Generates master thumbnail prompt with maximum metaphor density.
        # This is the "hero shot" - should be the most dramatic visual.
        
        topic = script_data.get('title', '')
        hook = script_data.get('hook', {})
        
        # Extract hook text
        if isinstance(hook, dict):
            hook_text = hook.get('text', '') or hook.get('scenario', '')
        else:
            hook_text = str(hook)[:200]
        
        # Concatenation to ensure safety
        THUMBNAIL_METAPHOR_PROMPT = f"You are designing THE thumbnail for a CFH-style viral video.\n\n"
        THUMBNAIL_METAPHOR_PROMPT += f"TOPIC: {topic}\n"
        THUMBNAIL_METAPHOR_PROMPT += f"HOOK: {hook_text}\n\n"
        
        THUMBNAIL_METAPHOR_PROMPT += "This thumbnail must STOP THE SCROLL. It needs:\n"
        THUMBNAIL_METAPHOR_PROMPT += "1. ONE massive symbolic object (the metaphor)\n"
        THUMBNAIL_METAPHOR_PROMPT += "2. ONE expressive character (emotion visible from thumbnail size)\n"
        THUMBNAIL_METAPHOR_PROMPT += "3. DRAMA (fire, destruction, tension, or shocking contrast)\n\n"
        
        THUMBNAIL_METAPHOR_PROMPT += "METAPHOR SELECTION GUIDE:\n"
        THUMBNAIL_METAPHOR_PROMPT += "- Economic collapse = Crumbling currency symbols, falling buildings\n"
        THUMBNAIL_METAPHOR_PROMPT += "- Energy crisis = Unplugged cables with sparks, dark power plants\n"
        THUMBNAIL_METAPHOR_PROMPT += "- War/conflict = Chess pieces, maps with fire, crossed-out flags\n"
        THUMBNAIL_METAPHOR_PROMPT += "- Debt = Chains, giant weights crushing buildings, avalanche of bills\n"
        THUMBNAIL_METAPHOR_PROMPT += "- Innovation = Light bulbs exploding, rocket launching from rubble\n\n"
        
        THUMBNAIL_METAPHOR_PROMPT += "TASK:\n"
        THUMBNAIL_METAPHOR_PROMPT += "Design the single most clickable image for this topic.\n\n"
        
        THUMBNAIL_METAPHOR_PROMPT += "OUTPUT JSON:\n"
        THUMBNAIL_METAPHOR_PROMPT += "{\n"
        THUMBNAIL_METAPHOR_PROMPT += "  \"central_metaphor\": \"A giant euro symbol made of crumbling concrete, cracks spreading\",\n"
        THUMBNAIL_METAPHOR_PROMPT += f"  \"character\": \"{self.primary_character} standing at base looking up in shock, mouth open\",\n"
        THUMBNAIL_METAPHOR_PROMPT += "  \"background\": \"Burning factory smokestacks in background, orange glow\",\n"
        THUMBNAIL_METAPHOR_PROMPT += "  \"color_scheme\": \"Dark blues and greys with intense orange fire accents\",\n"
        THUMBNAIL_METAPHOR_PROMPT += "  \"composition\": \"Character bottom-right, metaphor dominates left 2/3, rule of thirds\",\n"
        THUMBNAIL_METAPHOR_PROMPT += "  \"master_prompt\": \"Full detailed Imagen prompt here...\"\n"
        THUMBNAIL_METAPHOR_PROMPT += "}\n"
        
        try:
            response = self.llm.generate_json(THUMBNAIL_METAPHOR_PROMPT)
            data = json.loads(response)
            
            # Build ultra-detailed prompt
            master_prompt = self._build_master_thumbnail_prompt(data)
            
            # Save breakdown for manual tweaking
            import os
            # Note: We don't have direct access to assets_dir here, we'll just return prompt
            # But we can try to save if we find a way to pass assets_dir, 
            # for now let's just return the prompt as required.
            
            return master_prompt
            
        except Exception as e:
            print(f"[!] Thumbnail metaphor generation failed: {e}")
            return self._fallback_thumbnail_prompt(topic)
    
    def _build_master_thumbnail_prompt(self, metaphor_data):
        # Builds the ultra-detailed master prompt for thumbnail.
        # Optimized for Imagen/Midjourney/high-end generators.
        
        # Using explicit concatenation to avoid f-string parsing issues
        t = "[MAIN SUBJECT]\n"
        t += f"{metaphor_data.get('central_metaphor', 'Dramatic symbolic object')}.\n"
        t += f"{metaphor_data.get('character', self.primary_character)}.\n\n"
        
        t += "[COMPOSITION]\n"
        t += "16:9 landscape orientation, YouTube thumbnail optimized.\n"
        t += f"{metaphor_data.get('composition', 'Rule of thirds, character on right third, symbol on left')}.\n"
        t += "Dramatic perspective looking up at the symbol (emphasizes scale and threat).\n\n"
        
        t += "[STYLE]\n"
        t += "Premium editorial vector illustration in the style of The Economist magazine covers.\n"
        t += "Clean bold outlines, flat shading with complex gradients.\n"
        t += "Reference: Grand Theft Auto loading screens meet Kurzgesagt but more mature and dramatic.\n"
        t += "High-stakes geopolitical documentary aesthetic.\n\n"
        
        t += "[LIGHTING & COLOR]\n"
        t += f"{metaphor_data.get('color_scheme', 'Deep midnight blue with explosive red and gold highlights')}.\n"
        t += "Dramatic Rembrandt lighting with strong rim light on character.\n"
        t += "Volumetric fog and atmospheric depth.\n\n"
        
        t += "[BACKGROUND]\n"
        t += f"{metaphor_data.get('background', 'Industrial landscape with smoke and fire')}.\n"
        t += "Depth of field: Sharp focus on character and central symbol, background slightly atmospheric.\n\n"
        
        t += "[MOOD]\n"
        t += "Tense, foreboding, high-stakes.\n"
        t += "This is a moment of realization - the \"oh no\" moment.\n"
        t += "Viewer should feel: \"I need to know what happened.\"\n\n"
        
        t += "[TECHNICAL]\n"
        t += "Ultra HD resolution, ultra sharp, trending on ArtStation.\n"
        t += "Professional YouTube finance channel quality.\n"
        t += "Designed for maximum click-through rate at thumbnail size.\n"
        t += "Text-ready (space for title overlay on left or top third).\n"
        
        return t.strip()
    
    def _fallback_thumbnail_prompt(self, topic):
        # Simple fallback thumbnail.
        return f"Dramatic vector art thumbnail for video about {topic}. Shocked character, symbolic imagery, high contrast, 16:9."
    
    def _generate_metaphor_prompts_distributed(self, script_data, num_prompts, viral_context=None):
        # Legacy mode: Distributed prompts across script sections.
        # Still uses metaphor enhancement.
        
        # Extract all text from script
        all_text = ""
        
        if "hook" in script_data:
            all_text += "HOOK: " + str(script_data["hook"]) + "\n\n"
        
        if "sections" in script_data:
            for section in script_data["sections"]:
                title = section.get('title', '')
                sentences = section.get('sentences', [])
                all_text += f"SECTION: {title}\n"
                all_text += "\n".join(sentences) + "\n\n"
        
        # Generate metaphor concepts for each section
        # Using explicit concatenation to avoid f-string syntax errors
        DISTRIBUTED_METAPHOR_PROMPT = "You are a Visual Metaphor Director.\n\n"
        DISTRIBUTED_METAPHOR_PROMPT += "SCRIPT CONTENT:\n"
        DISTRIBUTED_METAPHOR_PROMPT += f"{all_text[:3000]}\n\n"
        DISTRIBUTED_METAPHOR_PROMPT += f"CHARACTER: {self.primary_character}\n\n"
        
        DISTRIBUTED_METAPHOR_PROMPT += f"Generate {num_prompts} distinct visual metaphors for this script.\n"
        DISTRIBUTED_METAPHOR_PROMPT += "Each should represent a KEY MOMENT using physical symbols.\n\n"
        
        DISTRIBUTED_METAPHOR_PROMPT += f"OUTPUT JSON array of {num_prompts} prompts:\n"
        DISTRIBUTED_METAPHOR_PROMPT += "[\n"
        DISTRIBUTED_METAPHOR_PROMPT += "  {\n"
        DISTRIBUTED_METAPHOR_PROMPT += "    \"filename\": \"visual_01.png\",\n"
        DISTRIBUTED_METAPHOR_PROMPT += "    \"type\": \"image\",\n"
        DISTRIBUTED_METAPHOR_PROMPT += "    \"scene_concept\": \"Hook - The shock moment\",\n"
        DISTRIBUTED_METAPHOR_PROMPT += "    \"metaphor\": \"Exploding price chart\",\n"
        DISTRIBUTED_METAPHOR_PROMPT += "    \"prompt\": \"Full Imagen prompt...\"\n"
        DISTRIBUTED_METAPHOR_PROMPT += "  },\n"
        DISTRIBUTED_METAPHOR_PROMPT += "  ...\n"
        DISTRIBUTED_METAPHOR_PROMPT += "]\n"
        
        try:
            response = self.llm.generate_json(DISTRIBUTED_METAPHOR_PROMPT)
            return json.loads(response)
        except Exception as e:
            print(f"[!] Distributed metaphor failed: {e}")
            # Return basic prompts
            return [
                {
                    "filename": f"visual_{i+1:02d}.png",
                    "type": "image",
                    "prompt": f"Scene {i+1} for {script_data.get('title', 'video')}"
                }
                for i in range(num_prompts)
            ]
    
    def analyze_visual_consistency(self, generated_prompts):
        # Post-generation analysis to ensure visual consistency.
        # Checks that the primary character appears frequently enough.
        
        character_mentions = 0
        for prompt_data in generated_prompts:
            prompt_text = prompt_data.get('prompt', '').lower()
            
            # Check if character archetype is mentioned
            if any(word in prompt_text for word in ['businessman', 'engineer', 'official', 'professional', 'character']):
                character_mentions += 1
        
        consistency_ratio = character_mentions / len(generated_prompts) if generated_prompts else 0
        
        print(f"  [*] Visual Consistency Check:")
        print(f"      - Character appearances: {character_mentions}/{len(generated_prompts)} ({consistency_ratio:.0%})")
        
        if consistency_ratio < 0.6:
            print(f"      [!] WARNING: Low character consistency. Recommend re-generation.")
        
        return consistency_ratio

    def _save_visual_requests(self, prompts, assets_dir):
        """Saves the generated prompts to a text file for review/image gen."""
        import os
        req_path = os.path.join(assets_dir, "visual_requests.txt")
        
        with open(req_path, "w", encoding="utf-8") as f:
            f.write("=== VISUAL PROMPT REQUESTS ===\n")
            f.write(f"Character: {self.primary_character}\n\n")
            
            for p in prompts:
                f.write(f"[{p['filename']}]\n")
                f.write(f"TYPE: {p['type']}\n")
                
                if 'metaphor_data' in p:
                    md = p['metaphor_data']
                    f.write(f"LITERAL: {md.get('literal', '')}\n")
                    f.write(f"METAPHOR: {md.get('symbol', '')}\n")
                    f.write(f"ACTION: {md.get('character', '')}\n")
                
                f.write(f"PROMPT: {p['prompt']}\n")
                f.write("-" * 40 + "\n")
                
        print(f"[*] Visual requests saved to: {req_path}")

    def _save_dual_layer_requests(self, prompts, assets_dir):
        """
        Saves separate prompt files for Image Gen and Grok Video Gen.
        """
        import os
        img_path = os.path.join(assets_dir, "image_prompts.txt")
        grok_path = os.path.join(assets_dir, "grok_prompts.txt")
        whisk_path = os.path.join(assets_dir, "whisk_prompts.txt")
        
        # 1. Save Image Prompts (Whisk/Imagen) - Formatted with headers
        with open(img_path, "w", encoding="utf-8") as f:
            f.write("=== STEP 1: REFERENCE IMAGE GENERATION ===\n")
            f.write("Generate these images to use as start-frames for Grok.\n\n")
            
            for p in prompts:
                f.write(f"[{p['image_filename']}] (For scene {p['filename']})\n")
                f.write(f"PROMPT: {p['image_prompt']}\n")
                f.write("-" * 60 + "\n")
        
        # 2. Save Grok Prompts (Video)
        with open(grok_path, "w", encoding="utf-8") as f:
            f.write("=== STEP 2: GROK VIDEO GENERATION ===\n")
            f.write("Upload the generated 'ref_XX.png' as the start image, then use this prompt.\n\n")
            
            for p in prompts:
                f.write(f"[{p['filename']}] (Use {p['image_filename']} as reference)\n")
                f.write(f"PROMPT: {p['video_prompt']}\n")
                f.write("-" * 60 + "\n")
        
        # 3. Save Whisk Prompts (Clean, one per line - for easy copy-paste)
        with open(whisk_path, "w", encoding="utf-8") as f:
            for p in prompts:
                f.write(p['image_prompt'] + "\n")
                
        print(f"[*] Saved Image Prompts -> {img_path}")
        print(f"[*] Saved Grok Prompts -> {grok_path}")
        print(f"[*] Saved Whisk Prompts (clean) -> {whisk_path}")

    def generate_images_auto(self, prompts, assets_dir):
        """
        Auto-generates 9:16 images via Gemini API.
        
        Args:
            prompts: List of dicts from generate_dual_layer_prompts() 
                     (each has 'image_prompt', 'image_filename')
            assets_dir: Where to save generated images
            
        Returns:
            dict with 'succeeded' (list of indices) and 'failed' (list of indices)
        """
        import os
        import time
        
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            print("[!] google-genai SDK not installed. Run: pip install google-genai")
            return {"succeeded": [], "failed": list(range(len(prompts)))}
        
        import config as cfg
        
        client = genai.Client(api_key=cfg.GOOGLE_API_KEY)
        # Must use gemini-2.5-flash-image for image generation
        # (gemini-3-pro-image-preview is for text+image, not generate_content with Image modality)
        model_name = "gemini-2.5-flash-image"
        
        succeeded = []
        failed = []
        
        for i, p in enumerate(prompts):
            # Output as visual_XX.png (matching pipeline expectation)
            out_filename = f"visual_{i+1:02d}.png"
            out_path = os.path.join(assets_dir, out_filename)
            
            # Skip if already exists
            if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                print(f"   [✓] {out_filename} already exists, skipping.")
                succeeded.append(i)
                continue
            
            prompt_text = p.get('image_prompt', '')
            if not prompt_text:
                print(f"   [!] No prompt for index {i}, skipping.")
                failed.append(i)
                continue
            
            # Append 9:16 vertical format hint to prompt
            prompt_text += " Vertical 9:16 aspect ratio, portrait orientation, mobile-optimized."
            
            print(f"   [{i+1}/{len(prompts)}] Generating {out_filename}...")
            
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt_text],
                    config=types.GenerateContentConfig(
                        response_modalities=['Image'],
                        image_config=types.ImageConfig(
                            aspect_ratio="9:16",
                        )
                    )
                )
                
                # Extract image from response using safe accessor
                image_saved = False
                
                # Use response.parts (safe accessor from SDK)
                parts = getattr(response, 'parts', None)
                if parts:
                    for part in parts:
                        if hasattr(part, 'inline_data') and part.inline_data is not None:
                            image = part.as_image()
                            image.save(out_path)
                            image_saved = True
                            print(f"   [✓] Saved {out_filename}")
                            break
                
                if image_saved:
                    succeeded.append(i)
                else:
                    # Debug: check why no image
                    block_reason = ""
                    if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                        block_reason = f" (blocked: {response.prompt_feedback})"
                    print(f"   [!] No image in response for {out_filename}{block_reason}")
                    failed.append(i)
                    
            except Exception as e:
                print(f"   [!] Failed to generate {out_filename}: {e}")
                failed.append(i)
            
            # Rate limit: small delay between API calls
            if i < len(prompts) - 1:
                time.sleep(2)
        
        print(f"\n[IMAGE GEN] Results: {len(succeeded)} succeeded, {len(failed)} failed")
        return {"succeeded": succeeded, "failed": failed}
