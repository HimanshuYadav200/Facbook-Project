
class IterativeScriptGenerator:
    """
    Orchestrates Script Agent + Quality Validator loop.
    Replaces linear generation with a feedback-driven cycle.
    """
    
    def __init__(self, script_agent, validator):
        self.script_agent = script_agent
        self.validator = validator
        self.max_iterations = 4
    
    def generate_validated_script(self, topic, research_data, pattern="what_if"):
        """
        Generate script with iterative quality refinement.
        """
        print(f"\n{'='*60}")
        print(f"ITERATIVE SCRIPT GENERATION: {topic} (Pattern: {pattern})")
        print(f"{'='*60}\n")
        
        iteration = 1
        script_data = None
        validation_result = None
        
        while iteration <= self.max_iterations:
            print(f"\n--- ITERATION {iteration} ---")
            
            # Generate script (or regenerate with feedback)
            if iteration == 1:
                # First attempt
                script_data = self.script_agent.generate_skulsy_script(topic, research_data, pattern=pattern)
            else:
                # Regenerate with feedback from validator
                script_data = self.script_agent.regenerate_with_feedback(
                    topic, 
                    research_data, 
                    validation_result["feedback"],
                    pattern=pattern
                )
            
            if not script_data:
                print(f"[ERROR] Script generation failed at iteration {iteration}")
                break
            
            # Validate
            validation_result = self.validator.validate_script(
                script_data, 
                research_data, 
                iteration=iteration
            )
            
            # Display results
            self._display_validation_results(validation_result)
            
            # Check if passed
            if validation_result["passed"]:
                print(f"\n✓ SCRIPT PASSED QUALITY CHECK (Score: {validation_result['overall_score']})")
                print(f"  Quality Tier: {validation_result['quality_tier']}")
                break
            else:
                print(f"\n✗ Script needs improvement (Score: {validation_result['overall_score']})")
                
                # Check if we should continue
                if iteration < self.max_iterations:
                     print(f"  Attempting iteration {iteration + 1}...")
                else:
                     print(f"  Max iterations reached.")
                
                iteration += 1
        
        # Final result assembly
        if script_data and validation_result:
            script_data["quality_metadata"] = {
                "final_score": validation_result["overall_score"],
                "iterations_needed": iteration if validation_result["passed"] else self.max_iterations,
                "dimension_scores": validation_result["dimension_scores"],
                "quality_tier": validation_result["quality_tier"],
                "passed": validation_result["passed"]
            }
            
            if not validation_result["passed"]:
                print(f"\n[WARNING] Failed to generate passing script after {self.max_iterations} iterations")
                print("Returning best attempt (may not meet quality threshold)")
                
            return script_data
        
        return None
    
    def _display_validation_results(self, result):
        """Pretty print validation results"""
        print(f"\n  Overall Score: {result['overall_score']}/100 ({result['quality_tier']})")
        print(f"  Dimension Breakdown:")
        for dim, score in result['dimension_scores'].items():
            bar_len = int(score / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(f"    {dim.capitalize():12s} [{bar}] {score}/100")
        
        if result["feedback"]:
            print(f"\n  Feedback Summary:")
            if result["feedback"].get("priority_fixes"):
                print(f"    Priority Fixes: {len(result['feedback']['priority_fixes'])}")
                for fix in result["feedback"]["priority_fixes"]:
                    print(f"      - {fix['issue']}")
