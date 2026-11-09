import os
import requests
import random
import time
import json
import re

class FetcherAgent:
    def __init__(self):
        # Expanded subreddits with viral potential
        self.subreddits = [
            # Original list
            "personalfinance",
            "povertyfinance",
            "debtfree",
            "layoffs",
            "scams",
            "entrepreneur",
            "financialindependence",
            # NEW: High-drama financial subreddits
            "wallstreetbets",
            "antiwork",
            "LegalAdvice",
            "RealEstate",
            "StudentLoans",
            "CreditCards",
            "Frugal",
            "investing"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _extract_numbers(self, text):
        """
        Extracts dollar amounts, percentages, and years from text.
        Returns count of specific numbers (viral stories have specific numbers).
        """
        # Pattern for money: $1,234.56 or $1234
        money_pattern = r'\$\s*[\d,]+(?:\.\d{2})?'
        # Pattern for percentages: 15% or 15.5%
        percent_pattern = r'\d+(?:\.\d+)?%'
        # Pattern for years/time periods
        year_pattern = r'\b(\d+)\s*years?\b'
        
        money_matches = re.findall(money_pattern, text)
        percent_matches = re.findall(percent_pattern, text)
        year_matches = re.findall(year_pattern, text)
        
        return len(money_matches) + len(percent_matches) + len(year_matches)

    def _calculate_viral_score(self, post_data):
        """
        Calculates a 'viral potential' score based on:
        - Upvote count (primary)
        - Number of comments (engagement)
        - Specific numbers in text (credibility)
        - Title emotional keywords (shock value)
        - Length (enough substance)
        """
        score = 0
        
        # 1. Upvote weight (most important)
        upvotes = post_data.get("ups", 0)
        score += upvotes * 10
        
        # 2. Comment engagement
        comments = post_data.get("num_comments", 0)
        score += comments * 5
        
        # 3. Text length (needs substance but not too long)
        text = post_data.get("selftext", "")
        text_length = len(text)
        if 500 < text_length < 3000:  # Sweet spot
            score += 200
        elif 300 < text_length < 500:
            score += 100
        
        # 4. Specific numbers (viral stories have exact amounts)
        number_count = self._extract_numbers(text + post_data.get("title", ""))
        score += number_count * 50
        
        # 5. Emotional keywords in title
        title = post_data.get("title", "").lower()
        emotional_keywords = [
            "lost everything", "nightmare", "destroyed", "ruined", "scammed",
            "never expected", "shocking", "insane",
            "debt", "bankruptcy", "fired", "laid off", "evicted",
            "owe", "sued", "collections", "credit score",
            "finally", "escaped", "paid off", "debt-free",
            "mistake", "learned", "regret", "warning",
            "$", "%", "k", "million"
        ]
        
        for keyword in emotional_keywords:
            if keyword in title:
                score += 30
        
        # 6. Penalty for removed content
        if post_data.get("removed_by_category"):
            score = 0
        
        return score

    def fetch_story(self, niche=None, min_viral_score=500):
        """
        Fetches a viral story related to the niche from Reddit.
        Uses viral scoring to find the BEST story, not just the first.
        """
        print(f"[*] Fetching VIRAL stories from Reddit...")
        print(f"[*] Scanning {len(self.subreddits)} subreddits for top content...")
        
        candidates = []
        
        for sub in self.subreddits:
            try:
                # Fetch top posts of the month for viral content
                url = f"https://www.reddit.com/r/{sub}/top.json?t=month&limit=15"
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get("data", {}).get("children", [])
                    
                    for post in posts:
                        post_data = post["data"]
                        
                        if post_data.get("stickied"):
                            continue
                        
                        text = post_data.get("selftext", "")
                        title = post_data.get("title", "")
                        
                        # Must have substantial text
                        if len(text) < 300:
                            continue
                        
                        # Calculate viral score
                        viral_score = self._calculate_viral_score(post_data)
                        
                        if viral_score >= min_viral_score:
                            candidates.append({
                                "title": title,
                                "text": text,
                                "subreddit": sub,
                                "upvotes": post_data["ups"],
                                "comments": post_data.get("num_comments", 0),
                                "url": post_data["url"],
                                "viral_score": viral_score
                            })
                else:
                    print(f"[!] Failed to fetch from r/{sub}: {response.status_code}")
                
                # Be polite to API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"[!] Error fetching from r/{sub}: {e}")

        if not candidates:
            print("[!] No stories found matching viral criteria")
            return None

        # Load history to avoid duplicates
        history_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "history_stories.txt")
        used_urls = set()
        if os.path.exists(history_path):
            with open(history_path, "r", encoding="utf-8") as f:
                used_urls = set(line.strip() for line in f if line.strip())

        # Filter out used stories
        fresh_candidates = [c for c in candidates if c['url'] not in used_urls]
        
        if not fresh_candidates:
            print("[!] All high-scoring stories have already been used! resetting candidates (with duplicates)...")
            fresh_candidates = candidates
        
        # Sort by viral score
        fresh_candidates.sort(key=lambda x: x["viral_score"], reverse=True)
        
        # Display top 5 candidates
        top_n = min(5, len(fresh_candidates))
        print(f"\n[*] Found {len(fresh_candidates)} fresh candidates. Highlighting Top {top_n}:")
        for i, story in enumerate(fresh_candidates[:top_n], 1):
            print(f"    {i}. r/{story['subreddit']}: {story['title'][:50]}...")
            print(f"       Score: {story['viral_score']} | Upvotes: {story['upvotes']}")
        
        # Select randomly from top N to ensure variety
        best_story = random.choice(fresh_candidates[:top_n])
        
        print(f"\n[OK] SELECTED: '{best_story['title'][:60]}...'")
        print(f"    From r/{best_story['subreddit']} | Viral Score: {best_story['viral_score']}")
        
        # Save to history
        try:
            with open(history_path, "a", encoding="utf-8") as f:
                f.write(best_story['url'] + "\n")
        except: pass
        
        return best_story

if __name__ == "__main__":
    agent = FetcherAgent()
    story = agent.fetch_story()
    if story:
        print(json.dumps({
            "title": story["title"],
            "subreddit": story["subreddit"],
            "viral_score": story["viral_score"],
            "text_preview": story["text"][:200] + "..."
        }, indent=2))

