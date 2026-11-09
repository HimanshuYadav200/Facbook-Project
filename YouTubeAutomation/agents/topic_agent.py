from utils.llm_client import LLMClient
import re

class TopicAgent:
    def __init__(self):
        self.llm = LLMClient()

    def get_trending_topic(self, niche="geopolitics"):
        """
        Generates macro-economic geopolitical topics (CFH Style).
        Queries trends for: Sovereign debt, Energy policy, Trade wars, Collapse.
        """
        # CHILL FINANCIAL HISTORIAN PATTERNS
        VIRAL_PATTERNS_CFH = {
            "financial_collapse": [
                "How {Country} Lost {Amount} in 24 Hours",
                "The {Bank} That Bankrupted a Nation",
                "Why the {Currency} is Mathematically Doomed",
                "The {Amount} Debt Bubble You Can't See"
            ],
            "business_failure": [
                "Why {Industry} died in {Country} (Financial Autopsy)",
                "The Real Reason {Country} Can't Afford {Policy}",
                "Who Actually Owns {Country}'s Debt?",
                "The Day the {Market} Stopped"
            ],
            "economic_mechanics": [
                "How {Country} is Faking its GDP",
                "The Ponzi Scheme Behind {Country}'s Growth",
                "Why {Country} is richer than you think (Asset Quality)"
            ]
        }
        
        # High RPM Finance Keywords
        keywords = [
            "sovereign debt crisis", "central bank balance sheet", "hyperinflation",
            "currency devaluation", "bond market collapse", "real estate bubble",
            "pension fund insolvency", "corporate bankruptcy", "imf bailout"
        ]

        print(f"[TOPIC AGENT] Searching for High-RPM '{niche}' topics...")
        
        # Simplified Trend Search (Mocking the external API call for now to ensure reliability)
        # In production this would query NewsAPI/Google Trends
        
        candidates = []
        
        # 1. Generate hypothetical topics based on patterns + current events context
        import random
        countries = ["Germany", "China", "Japan", "UK", "Argentina", "USA"]
        markets = ["Housing Market", "Bond Market", "Stock Exchange", "Crypto Sector"]
        amounts = ["$400 Billion", "$3 Trillion", "€800 Billion"]
        currencies = ["Yen", "Euro", "Dollar", "Pound"]
        banks = ["Central Bank", "Deutsche Bank", "SoftBank", "Evergrande"]

        pattern_type = random.choice(list(VIRAL_PATTERNS_CFH.keys()))
        templates = VIRAL_PATTERNS_CFH[pattern_type]
        template = random.choice(templates)
        
        # Logic to fill template intelligently (Simulated for this Agent)
        
        topic = template.format(
            Country=random.choice(countries),
            Amount=random.choice(amounts),
            Bank=random.choice(banks),
            Company="Evergrande",
            Currency=random.choice(currencies),
            Industry="Car Industry" if random.random() > 0.5 else "Tech Sector",
            Policy="Universal Basic Income",
            Market=random.choice(markets),
            System="Fractional Reserve Banking"
        )

        
        # Clean up formatting brackets
        topic = topic.replace("{", "").replace("}", "")
        
        print(f"[*] Generated Viral Topic: {topic}")
        return topic

    def validate_topic_virality(self, topic):
        """
        Scores a topic on viral potential (0-100).
        """
        score = 0
        topic_lower = topic.lower()
        
        # Check for specific numbers
        number_patterns = [
            r'\$[\d,]+',
            r'\d+%',
            r'\d+\s*(billion|million|trillion|thousand)',
            r'\d+\s*(years?|months?|days?)',
        ]
        
        for pattern in number_patterns:
            if re.search(pattern, topic, re.IGNORECASE):
                score += 25
                break
        
        # Check for emotional hooks
        emotional_words = [
            'hidden', 'secret', 'destroying', 'costing', 'trap',
            'nightmare', 'disaster', 'crisis', 'shocking', 'never',
            'ruined', 'saved', 'lost', 'mistake', 'warning'
        ]
        
        for word in emotional_words:
            if word in topic_lower:
                score += 15
                break
        
        # Check for parenthetical clarification (viral pattern)
        if '(' in topic and ')' in topic:
            score += 10
        
        # Check for question mark (curiosity)
        if '?' in topic:
            score += 10
        
        # Check for specificity (not vague)
        vague_words = ['tips', 'tricks', 'guide', 'basics', 'introduction']
        if not any(word in topic_lower for word in vague_words):
            score += 15
        
        # Length check (sweet spot 40-80 chars)
        if 40 <= len(topic) <= 80:
            score += 10
        
        # Penalty for being too long or too short
        if len(topic) < 20 or len(topic) > 100:
            score -= 15
        
        return min(100, max(0, score))


if __name__ == "__main__":
    agent = TopicAgent()
    topic = agent.get_trending_topic()
    print(f"\nTopic: {topic}")
