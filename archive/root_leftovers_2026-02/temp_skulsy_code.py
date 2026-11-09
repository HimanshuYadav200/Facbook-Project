
import json

class ScriptAgent:
    def generate_skulsy_script(self, topic, research_brief=None):
        """
        SKULSY ENGINE V4: Retention-Optimized Architecture
        """
        print(f"[*] Generating SKULSY ENGINE V4 script: {topic}")
        
        # PHASE 1: Extract the core scenario (Prevents hallucination)
        # If research_brief exists, it replaces the extraction phase
        scenario_prompt = self._extract_scenario(topic, research_brief)
        
        # PHASE 2: Generate with retention mechanics
        script_data = self._generate_retention_optimized_script(scenario_prompt, research_brief)
        
        if not script_data:
            print("[!] Skulsy V4 Generation Failed.")
            return None

        # PHASE 3: Auto-Enhance & Final Polish
        validated = self._validate_and_enhance(script_data)
        
        return validated

    def _extract_scenario(self, topic, research_brief=None):
        """
        Pre-process topic into structured scenario.
        This prevents timeline anchor confusion by establishing facts first.
        """
        print(f"    - Phase 1: Extracting Scenario from '{topic}'...")
        
        # NEW: Use Research Brief if available (Ground Truth)
        if research_brief and 'topic_decomposition' in research_brief:
            print("    [*] Using verified research data for scenario.")
            td = research_brief['topic_decomposition']
            
            # Construct scenario directly from verified research
            scenario = {
                "decision": td.get('action', 'invested'),
                "asset": td.get('subject', topic),
                "start_year": td.get('timeframe_start', '2010'),
                "end_year": td.get('timeframe_end', '2025'),
                "key_events": td.get('key_events', [])
            }
            
            # If explicit narrative hooks exist, use them
            if 'narrative_hooks' in research_brief:
                hooks = research_brief['narrative_hooks']
                if hooks:
                    scenario['suggested_hook'] = hooks[0]
            
            return scenario

        prompt = f"""
        Extract the core financial scenario from: "{topic}"
        
        Return JSON:
        {{
            "decision": "What action? (bought stock, sold property, etc)",
            "asset": "What specifically? (Amazon stock, Bitcoin, etc)",
            "start_year": "When did this begin? (YYYY)",
            "end_year": "When does regret/vindication hit? (YYYY)",
            "key_events": ["List 2-3 major events in this timeline"]
        }}
        
        Example:
        Topic: "What if Skulsy bought Apple in 2002"
        Output: {{
            "decision": "bought stock",
            "asset": "Apple (AAPL)",
            "start_year": "2002",
            "end_year": "2024",
            "key_events": ["iPod launch 2001", "iPhone launch 2007", "Became trillion dollar company 2018"]
        }}
        """
        
        try:
            return json.loads(self.llm.generate_json(prompt))
        except:
            # Fallback to raw topic if extraction fails
            return {"raw_topic": topic}

    def _generate_retention_optimized_script(self, scenario, research_brief=None):
        """
        Core generation with retention psychology baked in.
        """
        print(f"    - Phase 2: Generating Retention Script...")
        
        # Build examples dynamically
        examples = self._get_retention_examples()
        
        # Prepare Research Data String
        research_context = ""
        if research_brief:
            research_context = "\n=== VERIFIED RESEARCH DATA (USE THESE NUMBERS) ===\n"
            
            if 'core_facts' in research_brief:
                research_context += "Core Facts:\n"
                for i, fact in enumerate(research_brief['core_facts'][:5]):
                    research_context += f"- {fact}\n"
            
            if 'narrative_hooks' in research_brief:
                research_context += "\nNarrative Hooks (Choose one):\n"
                for hook in research_brief['narrative_hooks']:
                    research_context += f"- {hook}\n"
                    
            if 'data_points' in research_brief:
                 research_context += "\nKey Data Points:\n"
                 # Simplify data points for prompt
                 for point in research_brief.get('data_points', [])[:5]:
                     research_context += f"- {point.get('date')}: {point.get('value')}\n"

        prompt = f"""
You are writing a 40-45 second viral short for "Skulsy" - a deadpan skeleton who simulates financial regret.

=== THE SCENARIO ===
{json.dumps(scenario, indent=2)}
{research_context}

=== SKULSY'S VOICE ===
- Deadpan narrator, not Skulsy speaking
- "He bought. He sold. He waited." (short, punchy)
- Dark humor through understatement
- NO advice, just consequences
- USE THE RESEARCHED NUMBERS ACCURATELY.

=== RETENTION MECHANICS (CRITICAL) ===

1. HOOK FORMULA (0-3s):
   - Option A: Specific number shock ("What if Skulsy invested $5,000 in Bitcoin in 2010?")
   - Option B: Relatable mistake ("Skulsy panic-sold at the worst possible moment")
   - Option C: Unexpected contrast ("Skulsy chose the 'safe' option")
   
   ❌ BAD: "What if Skulsy made an investment decision"
   ✅ GOOD: "What if Skulsy put his rent money into GameStop"

2. THE SURPRISE RULE (8-25s):
   - Every 4-6 seconds: Insert a micro-surprise
   - Surprise types:
     * Unexpected number ("The stock dropped 80%")
     * Ironic timing ("He sold the day before the rally")
     * Contrast flip ("He thought he was diversifying. He wasn't.")
   
   Formula: Setup expectation → Subvert it immediately

3. STAKES ESCALATION (25-35s):
   - DON'T plateau emotionally
   - Keep raising stakes: "He lost money" → "He lost his savings" → "He lost his chance"

4. PUNCHLINE CALLBACK (40-45s):
   - Must reference the hook
   - Add new information that recontextualizes everything
   
   Example:
   Hook: "Skulsy bought Zoom stock in March 2020"
   Punchline: "He sold in April 2020. Before the lockdowns hit."

=== TIMELINE INTEGRATION (NOT A CHECKBOX) ===

Timeline anchors are NOT separate facts - they're story beats.

❌ BAD (Feels forced): "In 2002, he bought stock. The price was $12."
✅ GOOD (Anchor = Story): "2002. Skulsy bought at $12, convinced tech was dead."

RULES:
- Anchors appear in Setup + 2-3 key moments + Punchline
- Gaps between anchors: 3-8 years (allows "time passing" feeling)
- Use phrases: "By 2008", "Three years later", "Fifteen years passed"

=== OUTPUT STRUCTURE ===

{{
    "title": "Short title for video",
    "hook_variant": "number_shock | relatable_mistake | contrast",
    "sentences": [
        {{
            "text": "The exact sentence spoken",
            "state": "hook | optimism | doubt | panic | regret | punchline",
            "intensity": 0.0-1.0,
            "timeline_anchor": "2002" or "2008-2010" or null,
            "retention_trigger": "surprise | stakes | callback | pattern_break",
            "visual_cue": "What Grok should show (Must include 'Skulsy')"
        }}
    ],
    "beat_map": {{
        "hook": [0.0, 3.0],
        "setup": [3.0, 8.0],
        "timeline": [8.0, 25.0],
        "consequence": [25.0, 40.0],
        "punchline": [40.0, 45.0]
    }}
}}

=== EXAMPLES (LEARN FROM THESE) ===
{examples}

NOW WRITE THE SCRIPT.
- 12-15 sentences total (Strict Pacing)
- At least 3 timeline anchors (naturally integrated)
- Every sentence earns its place (no filler)
- Punchline must callback to hook
"""

        def _generate(prev_error=None):
            current_prompt = prompt
            if prev_error:
                current_prompt += f"\n\n❌ PREVIOUS ERROR: {prev_error}\n\nFIX: {self._get_fix_hint(prev_error)}"
            
            try:
                response = self.llm.generate_json(current_prompt)
                return json.loads(response)
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON parse failed: {e}")
                return None
            except Exception as e:
                print(f"[ERROR] Generation failed: {e}")
                return None
        
        from utils.validators import validate_with_retry
        return validate_with_retry(
            _generate, 
            self._validate_retention_script, 
            max_retries=3, 
            agent_name="SkulsyEngineV4"
        )

    def _get_retention_examples(self):
        """
        Provide 2-3 perfect examples for few-shot learning.
        """
        return """
EXAMPLE 1: Bitcoin 2011 (High Retention)
{
    "title": "Skulsy's $100 Bitcoin Mistake",
    "hook_variant": "number_shock",
    "sentences": [
        {
            "text": "What if Skulsy spent $100 on Bitcoin in 2011?",
            "state": "hook",
            "intensity": 0.7,
            "timeline_anchor": "2011",
            "retention_trigger": "number_shock",
            "visual_cue": "Skulsy holding $100 bill, Bitcoin logo in background"
        },
        {
            "text": "At $1 per coin, he'd own 100 Bitcoins.",
            "state": "optimism",
            "intensity": 0.3,
            "timeline_anchor": null,
            "retention_trigger": "pattern_break",
            "visual_cue": "Skulsy looking at laptop, Bitcoin counter showing 100"
        },
        {
            "text": "By 2013, Bitcoin hit $1,000.",
            "state": "optimism",
            "intensity": 0.5,
            "timeline_anchor": "2013",
            "retention_trigger": "surprise",
            "visual_cue": "Green chart climbing, calendar flipping to 2013"
        },
        {
            "text": "His $100 became $100,000.",
            "state": "growth",
            "intensity": 0.6,
            "timeline_anchor": null,
            "retention_trigger": "stakes",
            "visual_cue": "Calculator showing $100,000, Skulsy neutral expression"
        },
        {
            "text": "He sold everything.",
            "state": "doubt",
            "intensity": 0.7,
            "timeline_anchor": null,
            "retention_trigger": "pattern_break",
            "visual_cue": "Skulsy clicking 'SELL ALL' button"
        },
        {
            "text": "Called it a bubble that had to pop.",
            "state": "doubt",
            "intensity": 0.5,
            "timeline_anchor": null,
            "retention_trigger": "surprise",
            "visual_cue": "Skulsy looking smug, arms crossed"
        },
        {
            "text": "By 2017, Bitcoin reached $20,000.",
            "state": "regret",
            "intensity": 0.8,
            "timeline_anchor": "2017",
            "retention_trigger": "stakes",
            "visual_cue": "Chart rocketing up, Skulsy watching from sidelines"
        },
        {
            "text": "His 100 coins would've been worth $2 million.",
            "state": "regret",
            "intensity": 0.9,
            "timeline_anchor": null,
            "retention_trigger": "stakes",
            "visual_cue": "Calculator showing $2,000,000, Skulsy static stare"
        },
        {
            "text": "Instead, he walked away with $100k.",
            "state": "regret",
            "intensity": 0.7,
            "timeline_anchor": null,
            "retention_trigger": "contrast",
            "visual_cue": "Split screen: $100k vs $2M"
        },
        {
            "text": "And watched from the sidelines.",
            "state": "punchline",
            "intensity": 0.8,
            "timeline_anchor": null,
            "retention_trigger": "callback",
            "visual_cue": "Skulsy sitting alone, Bitcoin chart in distance"
        }
    ],
    "beat_map": {
        "hook": [0.0, 2.5],
        "setup": [2.5, 8.0],
        "timeline": [8.0, 24.0],
        "consequence": [24.0, 38.0],
        "punchline": [38.0, 42.0]
    }
}
"""

    def _validate_retention_script(self, data):
        """
        Advanced validation with retention psychology checks.
        """
        if not data or "sentences" not in data:
            return False, "Missing sentences"
        
        sentences = data["sentences"]
        
        # 1. Length check
        if not (11 <= len(sentences) <= 16):
            return False, f"Script has {len(sentences)} sentences. Need 11-16 for 45s pacing."
        
        # 2. Timeline anchor distribution
        anchors = [s.get('timeline_anchor') for s in sentences if s.get('timeline_anchor')]
        if len(anchors) < 3:
            return False, f"Only {len(anchors)} timeline anchors. Need at least 3 for time progression feel."
        
        # Check anchors in latter half
        anchor_indices = [i for i, s in enumerate(sentences) if s.get('timeline_anchor')]
        if max(anchor_indices) < len(sentences) * 0.6:
            return False, "Timeline anchors missing in latter half - no time progression in climax"
        
        # 3. Intensity peak rule (Must have 0.9+)
        intensities = [s.get('intensity', 0) for s in sentences]
        peaks = sum(1 for i in intensities if i >= 0.9)
        if peaks == 0:
            return False, "No emotional peak (0.9+). Script will feel flat."
        
        # 4. State progression check
        states = [s.get('state') for s in sentences]
        if 'punchline' not in states:
            return False, "Missing punchline state"
        
        return True, ""

    def _validate_and_enhance(self, script_data):
        """
        Post-generation enhancement pass (Auto-Fixer).
        """
        sentences = script_data.get('sentences', [])
        
        # FIX 1: Ensure punchline is last
        punchline_idx = next((i for i, s in enumerate(sentences) if s.get('state') == 'punchline'), None)
        if punchline_idx and punchline_idx != len(sentences) - 1:
            print(f"    [FIX] Moving punchline from index {punchline_idx} to end")
            punchline = sentences.pop(punchline_idx)
            sentences.append(punchline)
        
        # FIX 2: Ensure intensity doesn't crash mid-script
        for i in range(len(sentences) - 1):
            curr = sentences[i].get('intensity', 0.5)
            nxt = sentences[i+1].get('intensity', 0.5)
            
            # Don't allow drop > 0.3 in middle of script
            if i > 3 and i < len(sentences) - 2:
                if nxt < curr - 0.3:
                    print(f"    [FIX] Smoothing intensity drop at sentence {i+1}")
                    sentences[i+1]['intensity'] = max(curr - 0.1, nxt)
        
        script_data['sentences'] = sentences
        return script_data

    def _get_fix_hint(self, error):
        """Provide specific fix instructions based on error type"""
        error_lower = error.lower()
        if 'timeline' in error_lower:
            return "Add more year anchors. Use: 'By 2008', 'Three years later', 'In 2015'"
        elif 'intensity' in error_lower:
            return "Add one sentence with intensity 0.9-1.0 at the climax (before punchline)"
        else:
            return "Check JSON structure matches the EXACT output format provided."
