
def validate_script_structure(data):
    """
    Validates that the script JSON follows the required structure:
    {
        "hook": {"text":..., "visual_idea":...},
        "body": [ ... ],
        "climax": {"text":..., "visual_idea":...}
    }
    Returns: (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Script data is not a dictionary."

    required_keys = ["hook", "body", "climax"]
    for k in required_keys:
        if k not in data:
            return False, f"Missing required section: {k}"

    if not isinstance(data["body"], list):
        return False, "'body' section must be a list of scenes."

    # Max scenes check (Soft limit 20 to prevent giant scripts)
    if len(data["body"]) > 20:
        return False, f"Too many body scenes ({len(data['body'])}). Limit is 20."

    return True, ""

def validate_visual_style(prompt_text):
    """
    Checks for forbidden style keywords in visual prompts.
    Returns: (is_valid, violation_word)
    """
    # Words that indicate non-vector/illustration style
    forbidden = ["photographic", "hyperrealistic", "unreal engine", "8k photo"]
    text_lower = prompt_text.lower()
    
    for word in forbidden:
        if word in text_lower:
            return False, word
    
    # Special check for "shading" - only flag if it's NOT "no shading"
    if "shading" in text_lower and "no shading" not in text_lower:
        return False, "shading"
            
    return True, ""

def check_prohibited_content(text):
    """
    Checks for prohibited 'hype' words or financial advice triggers.
    Returns: (is_valid, found_phrases_list)
    """
    prohibited_phrases = [
        "guaranteed returns", 
        "can't lose", 
        "risk-free", 
        "get rich quick", 
        "moon shot",
        "100x", 
        "financial freedom in 30 days",
        "buy now"
    ]
    
    violations = []
    text_lower = text.lower()
    
    for phrase in prohibited_phrases:
        if phrase in text_lower:
            violations.append(phrase)
            
    return len(violations) == 0, violations

# --- SEMANTIC EXTRACTION FOR VISUAL FALLBACK ---
import re

def extract_scene_semantics(invalid_prompt, scene_context=""):
    """
    Extracts key elements (Subjects, Numbers, Emotions) from a prompt 
    that failed validation, to preserve context in the fallback.
    """
    cleaned = re.sub(
        r'\b(photographic|realistic|3d|detailed|shading|gradient|4k|8k|render)\b',
        '', invalid_prompt, flags=re.IGNORECASE
    )
    
    # Pattern 1: Financial Amounts (critical)
    amounts = re.findall(r'(\$[\d,]+(?:\.\d{2})?)', invalid_prompt)
    
    # Pattern 2: Main Subjects (simple noun extraction heuristic)
    # Look for words after "of / showing / with"
    subjects = re.findall(r'\b(?:of|showing|with)\s+(?:a |an |the )?([\w\s]+?)(?:\.|,|$)', cleaned, re.IGNORECASE)
    
    # Pattern 3: Emotions
    emotions = re.findall(r'\b(worried|happy|sad|frustrated|excited|angry|shocked)\b', cleaned, re.IGNORECASE)
    
    # Build Description
    parts = []
    if emotions: parts.append(emotions[0])
    if subjects: parts.append(subjects[0].strip())
    elif scene_context: parts.append(scene_context) # Use original script text if no subject found
    
    desc = " ".join(parts)
    
    # Text Overlay suggestion
    text_overlay = ""
    if amounts:
        desc += f" holding/showing {amounts[0]}"
        text_overlay = f" (Text Overlay: '{amounts[0]}' in Big Font)"
        
    return desc, text_overlay

# --- RETRY BUDGET SYSTEM ---

class RetryBudget:
    def __init__(self, max_total=10, max_per_agent=4):
        self.max_total = max_total
        self.max_per_agent = max_per_agent
        self.total_used = 0
        self.agent_usage = {}
    
    def can_retry(self, agent_name):
        if self.total_used >= self.max_total:
            return False, "Global Budget Exhausted"
        if self.agent_usage.get(agent_name, 0) >= self.max_per_agent:
            return False, f"Agent {agent_name} Budget Exhausted"
        return True, ""
        
    def record_retry(self, agent_name):
        self.total_used += 1
        self.agent_usage[agent_name] = self.agent_usage.get(agent_name, 0) + 1

# Singleton
_BUDGET = RetryBudget()

def reset_retry_budget():
    global _BUDGET
    _BUDGET = RetryBudget(max_total=10, max_per_agent=4)

def validate_with_retry(generate_fn, validator_fn, max_retries=3, agent_name="UnknownAgent"):
    global _BUDGET
    
    last_error = ""
    
    for attempt in range(max_retries):
        # Check Budget BEFORE generating (save API cost)
        if attempt > 0: # First attempt is free/mandatory
            allowed, reason = _BUDGET.can_retry(agent_name)
            if not allowed:
                print(f"[!] Retry blocked: {reason}. Using last failed result.")
                break
                
        try:
            if attempt > 0:
                print(f"    [Retry {attempt}/{max_retries}] Fixing issues: {last_error}")
                _BUDGET.record_retry(agent_name)
            
            result = generate_fn(last_error if attempt > 0 else None)
            
            if result is None:
                last_error = "Generation returned None"
                continue
                
            is_valid, error = validator_fn(result)
            
            if is_valid:
                return result
            
            last_error = error
            
        except Exception as e:
            last_error = str(e)
            
    print(f"[!] Max retries reached. Last error: {last_error}")
    return None


# --- VIRAL PATTERN VALIDATION ---

def validate_viral_elements(script_data: dict) -> tuple:
    """
    Validates that script contains viral pattern elements.
    Returns: (is_valid, list_of_warnings)
    
    Checks for:
    - Specific numbers (at least 3)
    - Stickman references in visuals
    - Escalation phrases
    - Hook contains a number
    """
    warnings = []
    
    # Extract all text and visuals
    all_text = script_data.get('hook', {}).get('text', '')
    all_visuals = [script_data.get('hook', {}).get('visual_idea', '')]
    
    for scene in script_data.get('body', []):
        all_text += ' ' + scene.get('text', '')
        all_visuals.append(scene.get('visual_idea', ''))
    
    all_text += ' ' + script_data.get('climax', {}).get('text', '')
    all_visuals.append(script_data.get('climax', {}).get('visual_idea', ''))
    
    # Check 1: Specific numbers (need 3+)
    number_pattern = r'\$[\d,]+(?:\.\d{2})?|\d+%|\d+\s*(?:years?|months?|billion|million|trillion|thousand)'
    numbers = re.findall(number_pattern, all_text, re.IGNORECASE)
    
    if len(numbers) < 3:
        warnings.append(f"Only {len(numbers)} specific numbers found (need 3+)")
    
    # Check 2: Characters in visuals (should be in most)
    missing_character = [v for v in all_visuals if not any(x in v.lower() for x in ['man', 'woman', 'boss', 'banker', 'investor', 'character']) and v]
    if len(missing_character) > 5:  # Allow some flexibility
        warnings.append(f"{len(missing_character)} visuals missing explicit character reference")
    
    # Check 3: Escalation phrases
    escalation_phrases = ['but here', 'kicker', 'worse', "that's when", 'what he didn', 'guess what']
    has_escalation = any(phrase in all_text.lower() for phrase in escalation_phrases)
    if not has_escalation:
        warnings.append("Missing escalation phrases ('But here's the kicker...', 'Then it got worse...')")
    
    # Check 4: Hook has number
    hook_text = script_data.get('hook', {}).get('text', '')
    if not re.search(number_pattern, hook_text, re.IGNORECASE):
        warnings.append("Hook doesn't contain a specific number")
    
    # Return
    is_valid = len(warnings) == 0
    
    if warnings:
        print(f"[!] Viral Pattern Warnings: {warnings}")
    else:
        print("[OK] Script passes viral pattern checks")
    
    return (is_valid, warnings)
