import google.generativeai as genai
import os
import sys

# Add parent directory to path to allow importing config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class LLMClient:
    def __init__(self):
        self.dev_mode = os.environ.get("DEV_MODE") == "True"
        if not config.GOOGLE_API_KEY and not self.dev_mode:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        if config.GOOGLE_API_KEY:
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(config.TEXT_MODEL_NAME)
        else:
            self.model = None

    def generate_text(self, prompt):
        """Generates text based on the prompt."""
        if self.dev_mode and not self.model:
            print("[DEV] Returning mock text response.")
            return "Inflation is rising again in 2025 due to supply chain shocks."

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating text: {e}")
            return None
    
    def generate_json(self, prompt, structure_example=None):
        """Generates text and attempts to parse it as JSON (simple helper)."""
        if self.dev_mode and not self.model:
             print("[DEV] Returning mock JSON response.")
             import json
             
             # Smart Mocking based on prompt content
             if "AI Art Director" in prompt:
                 # It's requesting Image Prompts
                 # Return list of strings matching the script size (approx 5)
                 return json.dumps([
                     " Cinematic shot of red stock market chart crashing.",
                     " Photorealistic side by side comparison of 2008 and 2025.",
                     " Detailed shot of a house with a for sale sign.",
                     " Close up of a gold bar on a table.",
                     " Clean Youtube subscribe button on dark background."
                 ])
             
             else:
                 # Default to Script Structure
                 return json.dumps({
                     "hook": {"text": "Is the market crashing?", "visual_idea": "Red chart crashing"},
                     "body": [
                         {"text": "Experts say 2025 looks like 2008.", "visual_idea": "Side by side charts"},
                         {"text": "Housing prices are stalling.", "visual_idea": "House with for sale sign"}
                     ],
                     "climax": {"text": "But there is one safe haven.", "visual_idea": "Gold bar"},
                     "outro": {"text": "Follow for more.", "visual_idea": "Subscribe button"}
                 })

        prompt = f"{prompt}\n\nPlease output valid JSON only. Do not use markdown code blocks."
        if structure_example:
            prompt += f"\nExample structure:\n{structure_example}"
        
        text = self.generate_text(prompt)
        # Basic cleanup if model adds markdown
        if text:
            cleaned_text = text.replace("```json", "").replace("```", "").strip()
            return cleaned_text
        return None
