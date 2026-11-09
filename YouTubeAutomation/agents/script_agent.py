import os
import json
import re
from utils.llm_client import LLMClient
from agents.quality_validator_agent import QualityValidatorAgent
from utils.validators import validate_with_retry

class ScriptAgent:
    """
    Skulsy Engine V5 (Expert Mode)
    - Pattern-Based Generation (7 Patterns)
    - Strict Number Locking (Anti-Hallucination)
    - Auto-Enhancement Loop (QualityValidator Feedback)
    """

    def __init__(self):
        self.llm = LLMClient()
        self.validator = QualityValidatorAgent()
        # Define skills directory
        self.skills_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".agent", "skills")
        self.patterns_dir = os.path.join(self.skills_dir, "script_patterns")
        self.base_structure_path = os.path.join(self.skills_dir, "BASE_VIRAL_STRUCTURE.md")
        self.humanizer_path = os.path.join(self.skills_dir, "humanizer", "SKILL.md")
        # Load humanizer rules once at init
        self.humanizer_rules = self._load_humanizer_condensed()

    def generate_skulsy_script(self, topic, research_brief=None, pattern="what_if"):
        """
        Main entry point for V5 Engine.
        """
        print(f"[*] Skulsy V5: Generating script for '{topic}' using pattern '{pattern}'...")
        
        # 1. Load Instructions
        base_skill = self._load_file(self.base_structure_path)
        pattern_skill = self._load_file(os.path.join(self.patterns_dir, f"PATTERN_{pattern}.md"))
        
        if not base_skill or not pattern_skill:
             print("[!] Critical Error: Pattern files missing. Check .agent/skills directory.")
             return None

        # 2. Extract Scenario & Lock Numbers
        scenario = self._extract_scenario(topic, research_brief)
        locked_numbers = self._extract_locked_numbers(research_brief.get('core_facts', []) if research_brief else [])
        
        # 3. Generate Initial Draft
        script_data = self._generate_draft(
            scenario, 
            research_brief, 
            pattern, 
            pattern_skill, 
            base_skill, 
            locked_numbers
        )
        
        if not script_data:
            return None

        # 4. Auto-Enhance Loop (The V5 "Quality Guarantee")
        final_script = self._validate_and_enhance(script_data, research_brief, pattern)
        
        return final_script

    def _load_humanizer_condensed(self):
        """
        Loads condensed humanizer rules for LLM injection.
        Returns key rules only (not the full SKILL.md) to save tokens.
        """
        try:
            # Return condensed version directly (faster than parsing full file)
            return """
=== HUMANIZER RULES (REMOVE AI TRACES) ===

BANNED WORDS (Never use):
- Verbs: delve, unleash, embark, navigate, foster, leverage, elevate, empower
- Nouns: landscape, tapestry, testament, paradigm, ecosystem, game-changer
- Adjectives: bustling, vibrant, pivotal, robust, multifaceted, transformative
- Connectors: Moreover, Furthermore, In conclusion, It is important to note

REPLACEMENTS:
- "delve into" → "look at"
- "leverage" → "use"
- "In conclusion" → [just end with a punchy line]

STYLE RULES:
1. Mix short sentences (under 5 words) with longer ones. Like this.
2. Use fragments occasionally. For effect.
3. Sound like bar talk - would you say this to a friend?
4. Be opinionated - no "there are pros and cons"
5. Delete quotables - if it sounds like a pullquote, rewrite it
"""
        except:
            return ""

    def _generate_draft(self, scenario, research_brief, pattern_name, pattern_content, base_content, locked_numbers, prev_error=None):
        """
        Generates the first draft using the V5 Prompt Structure.
        Adjusts length and rules based on pattern type.
        """
        
        # Prepare Context
        research_context = self._format_research_context(research_brief, locked_numbers)
        
        # Pattern-specific adjustments
        is_parable = pattern_name == 'parable'
        if is_parable:
            length_instruction = "Write a 90-120 second viral finance story (350-500 words)."
            voice_instruction = """VOICE RULES (PARABLE MODE):
1. USE DIALOGUE. At least 40% of text must be in quotes.
2. TWO CHARACTERS: Skulsy + a second character (business owner, seller, etc.).
3. Skulsy speaks as the MENTOR figure (calm, analytical, uses questions).
4. The second character must voice at least ONE objection the viewer would have.
5. Include 2-3 progressive STEPS that build on each other.
6. End with a one-line business principle (NOT advice, NOT preachy).
7. NO exclamation marks. NO 'follow us' CTAs."""
            min_sentences = 10
            hook_variants = 'parable_encounter | problem_setup'
        else:
            length_instruction = "Write a 45-second viral finance short."
            voice_instruction = "DEADPAN VOICE ONLY. No exclamation marks. No dialogue."
            min_sentences = 8
            hook_variants = 'number_shock | relatable_mistake | contrast | curiosity_gap'
        
        prompt = f"""
You are the Skulsy Script Engine (V5). {length_instruction}

=== THE SCENARIO ===
{json.dumps(scenario, indent=2)}

{research_context}

=== BASE STRUCTURE RULES ===
{base_content}

=== PATTERN RULES ({pattern_name.upper()}) ===
{pattern_content}

=== {voice_instruction} ===

=== STRICT OUTPUT FORMAT (JSON) ===
{{
    "title": "Short Title",
    "hook_variant": "{hook_variants}",
    "sentences": [
        {{
            "text": "Exact spoken sentence.",
            "state": "hook | setup | analysis | timeline | insight | punchline",
            "intensity": 0.1-1.0,
            "timeline_anchor": "YYYY" (or null),
            "retention_trigger": "surprise | stakes | pattern_break | callback | objection | progressive_reveal | math_reveal | principle",
            "visual_cue": "Description of visual"
        }}
    ],
    "beat_map": {{
        "hook": [0.0, 3.0],
        "setup": [3.0, 8.0],
        ... (align with pattern definition)
    }}
}}

CRITICAL:
1. USE THE LOCKED NUMBERS EXACTLY.
2. Follow the Beat Map in the pattern file.
3. {voice_instruction}
"""
        # Wrapper for validator
        def _call_llm(error_msg=None):
            current_prompt = prompt
            if error_msg:
                current_prompt += f"\n\n[PREVIOUS ATTEMPT FAILED]: {error_msg}\nFIX THE JSON STRUCTURE."
            try:
                return json.loads(self.llm.generate_json(current_prompt))
            except Exception as e:
                print(f"LLM Error: {e}")
                return None

        # Use retry logic for JSON structure
        def _check_structure(data):
            if not isinstance(data, dict): return False, "Root must be dict"
            if "sentences" not in data or not isinstance(data["sentences"], list): return False, "Missing sentences list"
            if len(data["sentences"]) < min_sentences: return False, f"Too few sentences (need at least {min_sentences})"
            return True, ""

        return validate_with_retry(_call_llm, _check_structure, max_retries=3, agent_name="ScriptAgentV5-Draft")

    def _validate_and_enhance(self, script_data, research_brief, pattern_name):
        """
        The V5 Feedback Loop:
        1. Score draft with QualityValidator
        2. If < passing, re-prompt LLM with specific feedback
        3. Repeat up to MAX_LOOPS
        4. CRITICAL: Always return the BEST scoring version, not the last one!
        """
        MAX_LOOPS = 2
        current_script = script_data
        best_script = script_data
        best_score = 0
        
        for i in range(MAX_LOOPS):
            # 1. Validate
            validation = self.validator.validate_script(current_script, research_brief, pattern_name=pattern_name, iteration=i+1)
            current_score = validation.get("overall_score", 0)
            
            # Track best version
            if current_score > best_score:
                best_score = current_score
                best_script = current_script.copy() if hasattr(current_script, 'copy') else dict(current_script)
                print(f"    [NEW BEST] Score: {best_score}")
            
            if validation["passed"]:
                print(f"[*] Script PASSED quality check (Score: {current_score})")
                best_script["quality_score"] = current_score
                return best_script
            
            # 2. Prepare Fix Prompt - EXTRACT NUMBERS FROM CURRENT SCRIPT
            print(f"[!] Script FAILED quality check (Score: {current_score}). Enhancing...")
            feedback = validation["feedback"]
            
            # Extract all numbers from current script to LOCK them
            script_text = " ".join([s.get("text", "") for s in current_script.get("sentences", [])])
            locked_nums = re.findall(r'\$[\d,]+\.?\d*|\d+%|\d{4}|\d+(?:,\d{3})*(?:\.\d+)?', script_text)
            locked_nums_str = ", ".join(set(locked_nums)) if locked_nums else "None detected"
            
            fix_prompt = f"""
The previous script draft failed quality validation.
SCORE: {current_score}/100. BEST SO FAR: {best_score}/100

=== PRIORITY FIXES (MUST ADDRESS) ===
{json.dumps(feedback.get('priority_fixes', []), indent=2)}

=== SUGGESTIONS ===
{json.dumps(feedback.get('suggestions', []), indent=2)}

{self.humanizer_rules}

=== LOCKED NUMBERS (DO NOT CHANGE THESE) ===
{locked_nums_str}
THESE NUMBERS MUST APPEAR EXACTLY AS-IS IN YOUR OUTPUT.
If you remove or change any of these numbers, the script will be REJECTED.

=== ORIGINAL SCRIPT ===
{json.dumps(current_script, indent=2)}

TASK: Improve the script's pacing and style while PRESERVING ALL NUMBERS EXACTLY.
Return the full corrected JSON with the same structure.
"""
            # 3. Re-generate
            try:
                new_data = json.loads(self.llm.generate_json(fix_prompt))
                if self._check_basic_structure(new_data):
                    # VALIDATE: Check if enhanced script still has the locked numbers
                    new_text = " ".join([s.get("text", "") for s in new_data.get("sentences", [])])
                    new_nums = re.findall(r'\$[\d,]+\.?\d*|\d+%|\d{4}|\d+(?:,\d{3})*(?:\.\d+)?', new_text)
                    
                    # Count how many original numbers are preserved
                    preserved = sum(1 for n in locked_nums if n in new_nums)
                    preservation_rate = (preserved / len(locked_nums) * 100) if locked_nums else 100
                    
                    if preservation_rate >= 80:  # At least 80% of numbers preserved
                        current_script = new_data
                        print(f"    [ENHANCED] Number preservation: {preservation_rate:.0f}%")
                    else:
                        print(f"    [REJECTED] Enhancement lost numbers ({preservation_rate:.0f}% preserved). Keeping previous.")
                else:
                    print("[!] Fix attempt returned invalid JSON. Keeping previous version.")
            except Exception as e:
                print(f"[!] Fix attempt failed: {e}")
        
        print(f"[!] Max enhancement loops reached. Returning BEST version (Score: {best_score}).")
        best_script["quality_score"] = best_score
        return best_script

    def _extract_locked_numbers(self, core_facts):
        """
        Parses research facts to find numbers that MUST be preserved.
        """
        locked = {}
        text = str(core_facts)
        # Extract distinct dollar amounts and years
        prices = re.findall(r'\$[\d,]+\.?\d*', text)
        years = re.findall(r'\b(?:19|20)\d{2}\b', text)
        
        # Store them for prompt injection
        for p in prices: locked[p] = "Price/Value"
        for y in years: locked[y] = "Year"
        
        return locked

    def _format_research_context(self, research_brief, locked_numbers):
        if not research_brief: return ""
        
        context = "=== RESEARCH DATA ===\n"
        if "core_facts" in research_brief:
             for f in research_brief["core_facts"]:
                 context += f"- {f}\n"
                 
        if locked_numbers:
            context += "\n=== LOCKED NUMBERS (DO NOT CHANGE/ROUND) ===\n"
            for num, type_ in locked_numbers.items():
                context += f"- {num} ({type_})\n"
                
        return context

    def _extract_scenario(self, topic, research_brief):
        # reuse V4 logic or simple pass-through
        if research_brief and 'topic_decomposition' in research_brief:
             return research_brief['topic_decomposition']
        return {"topic": topic, "note": "No deep research provided, relying on LLM knowledge"}

    def _load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return None

    def _check_basic_structure(self, data):
        return isinstance(data, dict) and "sentences" in data
