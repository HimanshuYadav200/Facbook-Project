
import json
import re

class MetaphorQualityAnalyzer:
    """
    Analyzes visual prompts to ensure they match CFH style.
    Provides quality scores and improvement suggestions.
    """
    
    def __init__(self):
        # CFH-style benchmark keywords
        self.metaphor_indicators = {
            "symbols": [
                "giant", "massive", "enormous", "crumbling", "exploding",
                "crushing", "burning", "falling", "rising", "chains",
                "weight", "clock", "scales", "flag", "symbol"
            ],
            "emotions": [
                "shocked", "panicked", "desperate", "angry", "terrified",
                "sweating", "yelling", "gripping", "running", "shielding",
                "pointing", "ducking", "screaming"
            ],
            "atmosphere": [
                "fire", "smoke", "storm", "lightning", "shadows",
                "red lights", "warning", "alarm", "chaos", "destruction",
                "sparks", "cracks", "rubble"
            ],
            "scale": [
                "looking up at", "dwarfed by", "towering", "looming",
                "small figure", "wide shot", "from below", "overhead"
            ]
        }
        
        # Anti-patterns (what to avoid)
        self.literal_indicators = [
            "reading", "sitting at desk", "looking at computer",
            "in office", "holding document", "presentation",
            "meeting room", "standing calmly", "neutral expression"
        ]
    
    def analyze_prompt_quality(self, prompt_text):
        """
        Scores a single prompt on CFH-style quality.
        
        Returns:
            score: 0-100
            breakdown: dict with category scores
            suggestions: list of improvements
        """
        
        prompt_lower = prompt_text.lower()
        
        scores = {
            "metaphor_density": 0,
            "emotional_impact": 0,
            "atmospheric_drama": 0,
            "scale_usage": 0,
            "literal_penalty": 0
        }
        
        # Score metaphor density (0-30 points)
        symbol_count = sum(1 for word in self.metaphor_indicators["symbols"] if word in prompt_lower)
        scores["metaphor_density"] = min(30, symbol_count * 10)
        
        # Score emotional impact (0-25 points)
        emotion_count = sum(1 for word in self.metaphor_indicators["emotions"] if word in prompt_lower)
        scores["emotional_impact"] = min(25, emotion_count * 8)
        
        # Score atmospheric drama (0-25 points)
        atmos_count = sum(1 for word in self.metaphor_indicators["atmosphere"] if word in prompt_lower)
        scores["atmospheric_drama"] = min(25, atmos_count * 8)
        
        # Score scale usage (0-20 points)
        scale_count = sum(1 for phrase in self.metaphor_indicators["scale"] if phrase in prompt_lower)
        scores["scale_usage"] = min(20, scale_count * 10)
        
        # Penalty for literal elements (-30 points)
        literal_count = sum(1 for phrase in self.literal_indicators if phrase in prompt_lower)
        scores["literal_penalty"] = -min(30, literal_count * 15)
        
        total_score = sum(scores.values())
        
        # Generate suggestions
        suggestions = []
        
        if scores["metaphor_density"] < 20:
            suggestions.append("Add physical symbols (giant objects, broken structures)")
        
        if scores["emotional_impact"] < 15:
            suggestions.append("Add character emotions (shocked face, sweating, yelling)")
        
        if scores["atmospheric_drama"] < 15:
            suggestions.append("Add dramatic background (fire, storm, warning lights)")
        
        if scores["scale_usage"] < 10:
            suggestions.append("Use scale contrast (small character vs giant symbol)")
        
        if scores["literal_penalty"] < 0:
            suggestions.append("REMOVE literal office/desk scenes - too boring!")
        
        return {
            "total_score": max(0, total_score),
            "breakdown": scores,
            "suggestions": suggestions,
            "grade": self._score_to_grade(total_score)
        }
    
    def _score_to_grade(self, score):
        """Converts score to letter grade."""
        if score >= 80: return "A (CFH Quality)"
        if score >= 60: return "B (Good)"
        if score >= 40: return "C (Needs Work)"
        if score >= 20: return "D (Too Literal)"
        return "F (Boring Office Scene)"
    
    def analyze_batch(self, prompts):
        """
        Analyzes a full batch of prompts.
        
        Args:
            prompts: List of prompt dicts with "prompt" field
        
        Returns:
            batch_report: Overall quality metrics
        """
        
        results = []
        
        for i, prompt_data in enumerate(prompts):
            prompt_text = prompt_data.get("prompt", "")
            analysis = self.analyze_prompt_quality(prompt_text)
            
            results.append({
                "index": i,
                "filename": prompt_data.get("filename", f"visual_{i+1}"),
                "score": analysis["total_score"],
                "grade": analysis["grade"],
                "suggestions": analysis["suggestions"]
            })
        
        # Aggregate statistics
        scores = [r["score"] for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Grade distribution
        grades = [r["grade"] for r in results]
        grade_counts = {}
        for grade in grades:
            grade_letter = grade.split()[0]  # Extract just "A", "B", etc.
            grade_counts[grade_letter] = grade_counts.get(grade_letter, 0) + 1
        
        # Identify weak prompts
        weak_prompts = [r for r in results if r["score"] < 50]
        
        batch_report = {
            "total_prompts": len(prompts),
            "average_score": avg_score,
            "overall_grade": self._score_to_grade(avg_score),
            "grade_distribution": grade_counts,
            "weak_prompts": weak_prompts,
            "detailed_results": results
        }
        
        return batch_report
    
    def compare_before_after(self, before_prompts, after_prompts):
        """
        Compares prompts before and after metaphor enhancement.
        Shows improvement metrics.
        """
        
        before_report = self.analyze_batch(before_prompts)
        after_report = self.analyze_batch(after_prompts)
        
        improvement = after_report["average_score"] - before_report["average_score"]
        improvement_pct = (improvement / before_report["average_score"] * 100) if before_report["average_score"] > 0 else 0
        
        comparison = {
            "before": {
                "avg_score": before_report["average_score"],
                "grade": before_report["overall_grade"]
            },
            "after": {
                "avg_score": after_report["average_score"],
                "grade": after_report["overall_grade"]
            },
            "improvement": {
                "points": improvement,
                "percentage": improvement_pct
            }
        }
        
        return comparison
    
    def generate_quality_report(self, prompts, output_path=None):
        """
        Generates a detailed quality report.
        Optionally saves to file.
        """
        
        report = self.analyze_batch(prompts)
        
        # Format as readable text
        report_text = f"""
╔══════════════════════════════════════════════════════════════╗
║          VISUAL METAPHOR QUALITY REPORT                      ║
╚══════════════════════════════════════════════════════════════╝

OVERALL METRICS:
  Total Prompts: {report['total_prompts']}
  Average Score: {report['average_score']:.1f}/100
  Overall Grade: {report['overall_grade']}

GRADE DISTRIBUTION:
"""
        
        for grade, count in sorted(report['grade_distribution'].items()):
            pct = count / report['total_prompts'] * 100
            bar = "█" * int(pct / 5)
            report_text += f"  {grade}: {count:2d} ({pct:5.1f}%) {bar}\n"
        
        if report['weak_prompts']:
            report_text += f"\nWEAK PROMPTS REQUIRING ATTENTION ({len(report['weak_prompts'])}):\n"
            
            for weak in report['weak_prompts'][:5]:  # Show top 5
                report_text += f"\n  {weak['filename']} (Score: {weak['score']}/100)\n"
                report_text += f"  Grade: {weak['grade']}\n"
                
                if weak['suggestions']:
                    report_text += "  Suggestions:\n"
                    for suggestion in weak['suggestions']:
                        report_text += f"    • {suggestion}\n"
        
        report_text += "\n" + "="*60 + "\n"
        
        # Save if path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"[*] Quality report saved to: {output_path}")
        
        return report_text
