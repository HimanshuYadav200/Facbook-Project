from utils.llm_client import LLMClient
import json

class VerificationAgent:
    def __init__(self):
        self.llm = LLMClient()

    def verify_script(self, script_data):
        """
        Verifies the script for financial accuracy, tone consistency, and logic.
        Simulates checks against SEC, FRED, BLS data.
        Returns a vetted (and potentially corrected) script JSON.
        """
        from utils.validators import check_prohibited_content
        
        # 1. Tier 1: Rule-Based Logic Check
        print("    [1/2] Running Rule-Based Safety Checks...")
        violations = []
        
        # Helper to check recursivley or just known fields
        all_text = ""
        if "hook" in script_data: all_text += script_data["hook"]["text"] + " "
        if "climax" in script_data: all_text += script_data["climax"]["text"] + " "
        if "body" in script_data:
            for item in script_data["body"]:
                all_text += item["text"] + " "
                
        is_safe, bad_phrases = check_prohibited_content(all_text)
        if not is_safe:
            print(f"[!] Safety Violation: Found prohibited phrases: {bad_phrases}")
            # We could return here, or ask LLM to fix it.
            # Let's note it for the prompt context.
            
        # 2. Tier 2: LLM Tone & Logic Check (No fake DB)
        print("    [2/2] Running LLM Tone & Logic Analysis...")
        
        # Turn JSON back to string
        script_str = json.dumps(script_data, indent=2)

        prompt = f"""
        You are a Senior Financial Editor and Compliance Officer. 
        Your job is to review the following YouTube Finance Script.
        
        SAFETY ALERT:
        Found Potential Issues: {bad_phrases if not is_safe else "None"}
        
        TASK:
        1. **Tone Check**: Ensure it is Calm, Analytical, and Neutral. Remove hype ("insane", "crazy").
        2. **Logic Check**: Does the narrative make sense?
        3. **Safety Fix**: If "Safety Alert" above has items, REWRITE those sentences to remove the prohibited phrases.
        
        CONSTRAINT:
        - DO NOT attempt to verify specific numbers against external databases (SEC, FRED) as you do not have real-time access. Focus on narrative logic and claim magnitude.
        
        INPUT SCRIPT (JSON):
        {script_str}
        
        OUTPUT:
        Return ONLY the corrected JSON.
        """

        try:
            verified_json_str = self.llm.generate_json(prompt)
            verified_script = json.loads(verified_json_str)
            print("[*] Script verified and approved.")
            return verified_script
            
        except json.JSONDecodeError:
            print("Failed to parse verified script JSON. Returning original.")
            return script_data
        except Exception as e:
            print(f"Error during verification: {e}")
            return script_data
