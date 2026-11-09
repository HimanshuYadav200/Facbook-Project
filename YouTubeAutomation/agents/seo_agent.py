"""
SEO Agent - Generates YouTube SEO metadata (title, description, tags, hashtags)
"""

import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.llm_client import LLMClient


class SEOAgent:
    def __init__(self):
        self.llm = LLMClient()
    
    def generate_seo(self, script_data: dict, assets_dir: str) -> dict:
        """
        Generates YouTube SEO metadata based on the script content.
        Returns dict with title, description, tags, hashtags, thumbnail suggestions.
        """
        print("\n[SEO AGENT] Generating YouTube SEO metadata...")
        
        # Extract key content from script
        title = script_data.get("title", "Untitled Video")
        hook_text = script_data.get("hook", {}).get("text", "")
        context_text = script_data.get("context", {}).get("text", "")
        close_text = script_data.get("close", {}).get("text", "")
        
        # Build prompt for LLM
        prompt = f"""
        You are an SEO Expert for a High-Quality Documentary Channel (like "Economics Explained" or "Polymatter").
        
        VIDEO TITLE: {title}
        
        CONTENT CONTEXT:
        Hook: {hook_text[:500]}
        Body: {context_text[:800]}...
        Conclusion: {close_text[:300]}
        
        TASK:
        Generate the YouTube Metadata in STRICT JSON format.
        
        REQUIREMENTS:
        1. **DESCRIPTION**: 
           - Must be a "Documentary Description" (Mini-Article).
           - Paragraph 1: High-stakes question/hook (No "In this video...").
           - Paragraph 2: Deep dive summary.
           - Paragraph 3: Specific themes (Corruption, History, etc.).
           - **NO** "\\n" literals in the JSON string content (use actual newlines in the output text later, or standard JSON escaping).
        
        2. **CHAPTERS**:
           - Estimate 5-6 timestamps based on a standard 8-minute flow (0:00 Intro, 02:00 Context, 04:00 Case Study, 06:00 Impact, 08:00 Conclusion).
        
        3. **KEY TOPICS**:
           - Bullet points of concepts covered.
           
        4. **TAGS**:
           - 20-25 high-traffic tags (e.g. "personal finance", "economics", "crisis").
           
        OUTPUT JSON STRUCTURE:
        {{
          "title": "Clickbait yet Classy Title",
          "description_intro": "The paragraphs of the description...",
          "chapters": [
             "0:00 - The Hook",
             "01:30 - The Context",
             ...
          ],
          "key_topics": [
             "Topic 1",
             "Topic 2"
          ],
          "hashtags": ["#Tag1", "#Tag2"],
          "tags": ["tag 1", "tag 2", "tag 3"],
          "thumbnail_text": "Short punchy text for thumbnail"
        }}
        """

        try:
            response = self.llm.generate_json(prompt)
            seo_data = json.loads(response)
                    
            # 1. Save JSON
            seo_path = os.path.join(assets_dir, "seo.json")
            with open(seo_path, "w", encoding="utf-8") as f:
                json.dump(seo_data, f, indent=2, ensure_ascii=False)
            
            # 2. Save DESCRIPTION.TXT (Clean for Paste)
            desc_path = os.path.join(assets_dir, "description.txt")
            with open(desc_path, "w", encoding="utf-8") as f:
                # Construct logic
                f.write(f"{seo_data.get('title', title)}\n\n")
                f.write(f"{seo_data.get('description_intro', '')}\n\n")
                
                f.write("CHAPTERS:\n")
                for chap in seo_data.get('chapters', []):
                    f.write(f"{chap}\n")
                f.write("\n")
                
                f.write("KEY TOPICS COVERED:\n")
                for topic in seo_data.get('key_topics', []):
                    f.write(f"- {topic}\n")
                f.write("\n")
                
                f.write(" ".join(seo_data.get('hashtags', [])))
                
            # 3. Save TAGS.TXT (Comma Separated)
            tags_path = os.path.join(assets_dir, "tags.txt")
            with open(tags_path, "w", encoding="utf-8") as f:
                # Ensure list
                tags = seo_data.get('tags', [])
                if isinstance(tags, str): tags = tags.split(',')
                # Join with comma
                f.write(", ".join(tags))
            
            # 4. Generate & Save THUMBNAIL PROMPT (using VisualAgent logic)
            # This ensures the prompt text is available even if main.py hasn't run yet.
            try:
                from agents.visual_agent import VisualAgent
                vis_agent = VisualAgent()
                # Create a minimal script structure if needed, or pass full script
                # script_data dict is available here
                thumb_prompt = vis_agent.generate_thumbnail_prompt(script_data)
                
                thumb_prompt_path = os.path.join(assets_dir, "thumbnail_prompt.txt")
                with open(thumb_prompt_path, "w", encoding="utf-8") as f:
                    f.write(thumb_prompt)
            except Exception as e:
                print(f"[!] Thumbnail prompt generation in SEO Agent failed: {e}")

            print(f"[*] SEO metadata saved to: seo.json, description.txt, tags.txt, thumbnail_prompt.txt")
            return seo_data

        except Exception as e:
            print(f"[!] SEO generation via LLM failed: {e}")
        
        # Fallback: Generate basic SEO
        return self._generate_fallback_seo(script_data, assets_dir)
    
    def _generate_fallback_seo(self, script_data: dict, assets_dir: str) -> dict:
        """Fallback SEO generation without LLM."""
        title = script_data.get("title", "Finance Analysis Video")
        
        seo_data = {
            "title": title,
            "description_intro": "Deep dive analysis.",
            "tags": ["finance", "economics"],
            "hashtags": ["#Finance"],
            "chapters": ["0:00 - Intro"],
            "key_topics": ["Analysis"],
            "thumbnail_text": "Analysis"
        }
        
        # Save placeholder files
        with open(os.path.join(assets_dir, "seo.json"), "w") as f: json.dump(seo_data, f)
        with open(os.path.join(assets_dir, "description.txt"), "w") as f: f.write(title)
        with open(os.path.join(assets_dir, "tags.txt"), "w") as f: f.write("finance, economics")
        
        print(f"[*] Fallback SEO metadata saved.")
        return seo_data


if __name__ == "__main__":
    # Test with specific user session
    session_dir = "assets/run_20260117_235946"
    
    # Path relative to project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_session_path = os.path.join(base_dir, session_dir)
    script_path = os.path.join(full_session_path, "script.json")
    
    if os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            script = json.load(f)
        
        agent = SEOAgent()
        seo = agent.generate_seo(script, full_session_path)
        print("\n[TEST] Generated SEO for: run_20260117_235946")
    else:
        print(f"[!] Script not found at {script_path}")
