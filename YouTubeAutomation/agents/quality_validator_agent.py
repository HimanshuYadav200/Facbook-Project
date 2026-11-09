
import json
import statistics
import re
import os

class QualityValidatorAgent:
    """
    Quality Validator V5 (Expert Mode)
    Scores scripts across 5 dimensions: Retention, Accuracy, Narrative, Pacing, Viral.
    Dynamically loads pattern definitions to validate beat maps.
    """
    
    def __init__(self):
        self.min_passing_score = 75  # Strict threshold
        self.max_iterations = 3
        # Path to skills directory for loading patterns
        self.skills_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".agent", "skills", "script_patterns")

    def validate_script(self, script_data, research_data, pattern_name="what_if", iteration=1):
        """
        Main validation entry point.
        """
        print(f"\n[QUALITY VALIDATOR V5] Iteration {iteration} (Pattern: {pattern_name})")
        
        # Load pattern definition for dynamic validation
        pattern_def = self._load_pattern_definition(pattern_name)
        
        # Calculate scores across all dimensions
        scores = {
            "retention": self._score_retention(script_data, pattern_def),
            "accuracy": self._score_accuracy(script_data, research_data),
            "narrative": self._score_narrative(script_data),
            "pacing": self._score_pacing(script_data, pattern_def),
            "viral": self._score_viral(script_data)
        }
        
        # Weighted overall score (V5 Weights)
        overall = (
            scores["retention"] * 0.30 +
            scores["accuracy"] * 0.30 +  # Increased importance
            scores["narrative"] * 0.15 +
            scores["pacing"] * 0.15 +
            scores["viral"] * 0.10
        )
        
        # Generate feedback if below threshold
        feedback = {}
        passed = overall >= self.min_passing_score
        
        if not passed:
            feedback = self._generate_feedback(scores, script_data, research_data, pattern_def)
        
        return {
            "passed": passed,
            "overall_score": round(overall, 2),
            "dimension_scores": scores,
            "feedback": feedback,
            "iteration": iteration,
            "quality_tier": self._get_quality_tier(overall)
        }

    def _load_pattern_definition(self, pattern_name):
        """Load the specific pattern file to get beat map and structure"""
        try:
            filename = f"PATTERN_{pattern_name}.md"
            path = os.path.join(self.skills_dir, filename)
            
            if not os.path.exists(path):
                # Fallback to base structure if pattern not found
                return None
                
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract beat map from markdown (simple parsing)
            # Looking for JSON block or specific headers. 
            # Ideally the pattern file has a machine-readable section.
            # For now, we use a simple heuristic map based on pattern type.
            
            # V5 patterns have a JSON example at the bottom. We can try to parse that
            # or define hardcoded maps for known patterns.
            
            # Helper for known patterns
            maps = {
                "what_if": {"hook": (0,3), "setup": (3,10), "timeline": (10,28), "consequence": (28,38), "punchline": (38,42)},
                "mistake": {"hook": (0,3), "setup": (3,8), "timeline": (8,20), "consequence": (20,35), "punchline": (35,45)},
                "explainer": {"hook": (0,3), "setup": (3,10), "timeline": (10,25), "consequence": (25,35), "punchline": (35,45)},
                "success": {"hook": (0,3), "setup": (3,8), "timeline": (8,25), "consequence": (25,35), "punchline": (35,45)},
                "comparison": {"hook": (0,3), "setup": (3,10), "timeline": (10,32), "consequence": (32,38), "punchline": (38,45)},
                "timeline": {"hook": (0,3), "setup": (3,8), "timeline": (8,32), "consequence": (32,38), "punchline": (38,45)},
                "reaction": {"hook": (0,3), "setup": (3,8), "timeline": (8,20), "consequence": (20,32), "punchline": (32,45)}
            }
            return maps.get(pattern_name, maps["what_if"])
            
        except Exception as e:
            print(f"Error loading pattern definition: {e}")
            return None

    def _score_retention(self, script_data, pattern_def):
        """Score retention psychology metrics"""
        sentences = script_data.get("sentences", [])
        
        # Hook Strength (0-100)
        hook = sentences[0]["text"] if sentences else ""
        hook_score = self._evaluate_hook_strength(hook)
        
        # Surprise Density (count pattern breaks)
        surprises = sum(1 for s in sentences if s.get("retention_trigger") in ["surprise", "pattern_break"])
        surprise_score = min(100, (surprises / 3) * 100)  # V5 Target: 3 surprises
        
        # Emotional Arc Slope
        intensities = [s.get("intensity", 0.5) for s in sentences]
        if len(intensities) > 1:
            arc_slope = (max(intensities) - intensities[0]) / len(intensities)
            arc_score = min(100, (arc_slope / 0.10) * 100) # V5 Target: 0.10 slope
        else:
            arc_score = 0
            
        # Punchline Callback
        punchline = next((s for s in sentences if s.get("state") == "punchline"), None)
        callback_score = 100 if punchline and self._has_callback(hook, punchline["text"]) else 0
        
        retention = (
            hook_score * 0.35 +
            surprise_score * 0.25 +
            arc_score * 0.20 +
            callback_score * 0.20
        )
        return round(retention, 2)
    
    def _score_accuracy(self, script_data, research_data):
        """Score factual accuracy against research"""
        if not research_data: return 100 # No research to check against
             
        sentences = script_data.get("sentences", [])
        script_text = " ".join([s["text"] for s in sentences])
        
        # Use simple string extraction for robustness
        research_nums = self._extract_research_numbers(research_data)
        script_nums = self._extract_numbers_from_text(script_text)
        
        # Check precision
        precision = self._calculate_number_precision(script_nums, research_nums)
        
        # Check citation rate (fuzzy match keywords)
        core_facts = research_data.get("core_facts", [])
        cited_facts = 0
        for fact in core_facts:
            fact_str = str(fact) if not isinstance(fact, dict) else fact.get('statement', '')
            keywords = [w for w in fact_str.split() if len(w) > 4 and w.lower() not in ['skulsy']]
            if any(k.lower() in script_text.lower() for k in keywords):
                cited_facts += 1
        
        citation_rate = (cited_facts / len(core_facts) * 100) if core_facts else 0
        
        # CRITICAL FAIL: Wrong numbers kill the score
        if precision < 80: # Allow slight variance
            print(f"    [CRITICAL] Number precision low: {precision}%")
            return precision # Cap score at precision level
            
        accuracy = (
            citation_rate * 0.40 +
            precision * 0.60
        )
        return round(accuracy, 2)
    
    def _score_narrative(self, script_data):
        """Score narrative craft"""
        sentences = script_data.get("sentences", [])
        
        # Show vs Tell
        action_verbs = ["bought", "sold", "watched", "waited", "lost", "gained", "clicked", "saw", "held"]
        show_count = sum(1 for s in sentences if any(verb in s["text"].lower() for verb in action_verbs))
        show_ratio = (show_count / len(sentences)) * 100 if sentences else 0
        
        # Deadpan check
        script_text = " ".join([s["text"] for s in sentences])
        has_violations = any(x in script_text.lower() for x in ["!", "you should", "remember", "crazy", "insane"])
        deadpan_score = 0 if has_violations else 100
        
        narrative = (show_ratio * 0.60 + deadpan_score * 0.40)
        return round(narrative, 2)
    
    def _score_pacing(self, script_data, pattern_def):
        """Score pacing against beat map (pattern-aware word count)"""
        sentences = script_data.get("sentences", [])
        
        # Word count - check if parable pattern (longer scripts)
        total_words = sum(len(s["text"].split()) for s in sentences)
        is_parable = any(s.get("state") == "analysis" and '"' in s.get("text", "") for s in sentences)
        
        if is_parable or total_words > 300:
            # Parable pattern: 350-500 words target
            word_score = 100 if 300 <= total_words <= 520 else 50
        else:
            # Standard patterns: 150-260 words target
            word_score = 100 if 150 <= total_words <= 260 else 50
        
        # Beat Timing
        timing_score = 100
        if pattern_def:
            beat_map = script_data.get("beat_map", {})
            timing_score = self._validate_beat_timing(beat_map, pattern_def)
            
        pacing = (word_score * 0.40 + timing_score * 0.60)
        return round(pacing, 2)
    
    def _score_viral(self, script_data):
        """Score viral potential"""
        sentences = script_data.get("sentences", [])
        script_text = " ".join([s["text"] for s in sentences])
        
        # Specificity
        specific_words = ["$100", "2008", "Bitcoin", "Amazon", "50%"] # Generic check
        has_specifics = any(re.search(r'\d', s["text"]) for s in sentences)
        specificity_score = 100 if has_specifics else 0
        
        # Contrast
        contrast_words = ["but", "instead", "however", "while"]
        contrast_count = sum(1 for w in contrast_words if w in script_text.lower())
        contrast_score = min(100, (contrast_count / 2) * 100)
        
        viral = (specificity_score * 0.60 + contrast_score * 0.40)
        return round(viral, 2)

    def _check_timeline_coherence(self, anchors):
        """Verify timeline is chronologically sound"""
        if not anchors: return True
        
        years = []
        for anchor in anchors:
            # Robust year extraction
            matches = re.findall(r'\b(?:19|20)\d{2}\b', str(anchor))
            if matches:
                 years.append(int(matches[0]))
        
        return years == sorted(years)

    def _validate_anchor_spacing(self, anchors):
        """Check if year gaps are proportional"""
        if len(anchors) < 2: return 100
        
        years = []
        for anchor in anchors:
            matches = re.findall(r'\b(?:19|20)\d{2}\b', str(anchor))
            if matches:
                 years.append(int(matches[0]))
        
        if len(years) < 2: return 100
        
        gaps = [years[i+1] - years[i] for i in range(len(years) - 1)]
        valid_gaps = all(3 <= gap <= 10 for gap in gaps) # Relaxed to 10 years
        return 100 if valid_gaps else 60

    def _generate_feedback(self, scores, script_data, research_data, pattern_def):
        """Generate actionable feedback"""
        feedback = {
            "priority_fixes": [],
            "suggestions": [],
            "specific_edits": []
        }
        
        # PRIORITY: Accuracy
        if scores["accuracy"] < 80:
             feedback["priority_fixes"].append({
                 "issue": "Accuracy Low: Numbers or Facts mismatch.",
                 "action": "Ensure all numbers ($ amounts, years) MATCH the research EXACTLY."
             })
             
        # PRIORITY: Retention
        if scores["retention"] < 75:
             feedback["priority_fixes"].append({
                 "issue": "Retention Logic Weak.",
                 "action": "Ensure Hook has a number, create 3 surprise moments, and ensure Punchline callbacks to Hook."
             })
             
        # Suggestion: Pacing
        if scores["pacing"] < 80:
             total_words = sum(len(s["text"].split()) for s in script_data.get("sentences", []))
             is_long = total_words > 300
             target = "350-500 words" if is_long else "200-250 words"
             feedback["suggestions"].append({
                 "issue": "Pacing off.",
                 "action": f"Adjust word count to {target} and align beats with timeframe."
             })
             
        return feedback

    # --- HELPER METHODS ---
    
    def _evaluate_hook_strength(self, hook_text):
        score = 0
        if re.search(r'\d', hook_text): score += 50 # Contains number
        if len(hook_text.split()) < 15: score += 30 # Concise
        if "?" in hook_text or "mistake" in hook_text.lower(): score += 20 # Question/Trigger
        return score

    def _has_callback(self, hook, punchline):
        # Check for shared significant words
        hook_words = set(w.lower() for w in hook.split() if len(w) > 3)
        punch_words = set(w.lower() for w in punchline.split() if len(w) > 3)
        return len(hook_words.intersection(punch_words)) > 0

    def _extract_research_numbers(self, research_data):
        # Return list of numbers found in research
        text = str(research_data)
        # Extract $amounts, years, percentages
        return re.findall(r'\$?\d+[,\.]?\d*%?', text)

    def _extract_numbers_from_text(self, text):
        return re.findall(r'\$?\d+[,\.]?\d*%?', text)

    def _calculate_number_precision(self, script_nums, research_nums):
        if not research_nums: return 100
        # Simple set intersection approximation
        script_set = set(n.replace(',','') for n in script_nums)
        research_set = set(n.replace(',','') for n in research_nums)
        
        # We care that SCRIPT numbers come FROM RESEARCH.
        # Not that ALL research numbers are used.
        valid_count = 0
        for s_num in script_set:
            if s_num in research_set:
                valid_count += 1
            else:
                # Allow for rounding logic or slight formatting diffs?
                # For V5 strictness, we penalize hallucinations.
                pass
                
        if not script_set: return 0
        return (valid_count / len(script_set)) * 100

    def _validate_beat_timing(self, beat_map, target_map):
        score = 0
        total_beats = len(target_map)
        for beat, target_range in target_map.items():
            if beat in beat_map:
                actual = beat_map[beat]
                # Tolerance check
                if abs(actual[0] - target_range[0]) < 5 and abs(actual[1] - target_range[1]) < 5:
                    score += 1
        return (score / total_beats) * 100
    
    def _get_quality_tier(self, score):
        if score >= 90: return "ELITE"
        if score >= 80: return "GOOD"
        if score >= 70: return "PASSABLE"
        return "FAIL"
