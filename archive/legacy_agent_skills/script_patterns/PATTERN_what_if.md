# Script Pattern: What If

**Inherits**: BASE_VIRAL_STRUCTURE.md

**Pattern Type**: Hypothetical Decision → Outcome Reveal

**Emotional Arc**: Curiosity → Anticipation → Regret → Reflection

---

## Pattern Overview

Skulsy explores a hypothetical financial decision from the past. We watch what WOULD have happened if he'd made a specific choice, then reveal what actually happened (or didn't happen).

**Core Question**: "What if [DECISION] had been made?"

**Viewer Psychology**: FOMO + hindsight bias + "I could've been rich" fantasy

---

## Pattern Structure (45 seconds)

### Beat 1: The Hypothetical Setup (0-8s)

**Goal**: Establish the "what if" scenario with specific parameters

**Tone**: Neutral curiosity, matter-of-fact

**Hook Formula** (from Base):
"What if Skulsy [ACTION] [AMOUNT] in [ASSET] at [PRICE] in [YEAR]?"

**Requirements**:
- Exact dollar amount Skulsy would have invested
- Exact price of asset at that time
- Specific year (not "early 2000s")

**Example**:
"What if Skulsy put $10,000 into Amazon stock at $5 in 2001?"

**State**: `"state": "hook"`  
**Intensity**: 0.5-0.6  
**Timeline Anchor**: Entry year (e.g., "2001")

---

### Beat 2: The Initial Outcome (8-18s)

**Goal**: Show the immediate result of the hypothetical

**Tone**: Optimistic, building momentum

**Pattern**: Calculate what the position would look like

**Structure**:
1. State the math: "At $5 per share, he'd own [X] shares"
2. Show early growth: "By [YEAR+2], it hit $[PRICE]"
3. Calculate gain: "His $[AMOUNT] became $[AMOUNT]"

**Example**:
```
"At $5 per share, he'd own 2,000 shares.
By 2003, Amazon hit $55.
His $10,000 became $110,000."
```

**State**: `"state": "optimism"` or `"state": "growth"`  
**Intensity**: 0.6-0.7  
**Timeline Anchor**: Mid-point year

**Retention Trigger**: "stakes" (first big number reveal)

---

### Beat 3: The Long-Term Compounding (18-28s)

**Goal**: Show exponential growth over time

**Tone**: Momentum building, numbers getting absurd

**Pattern**: Multiple timeline jumps showing compounding

**Structure**:
1. Jump to next milestone: "By [YEAR+5], it reached $[PRICE]"
2. Show bigger gains: "Now worth $[LARGER_AMOUNT]"
3. Optional: Mention near-miss moments ("Even after the 2008 crash...")

**Example**:
```
"By 2007, Amazon hit $100.
His investment: $200,000.
Even after the 2008 crash, he'd have $120,000.
By 2015: $600,000."
```

**State**: `"state": "growth"`  
**Intensity**: 0.7-0.8  
**Timeline Anchor**: 2-3 additional years

**Retention Trigger**: "surprise" (the compounding is shocking)

---

### Beat 4: The Peak Scenario (28-38s)

**Goal**: Reveal the maximum potential outcome

**Tone**: Peak momentum, biggest number

**Pattern**: Show recent/current price

**Structure**:
1. Final timeline jump: "By [RECENT_YEAR], ..."
2. Reveal peak/current price
3. Calculate total value
4. Optional: Comparison to alternatives

**Example**:
```
"By 2021, Amazon stock reached $3,500.
His 2,000 shares would be worth $7 million.
From a $10,000 bet."
```

**State**: `"state": "climax_setup"` or `"state": "consequence"`  
**Intensity**: 0.9 (peak)  
**Timeline Anchor**: Final year

**Retention Trigger**: "stakes" (maximum value)

---

### Beat 5: The Reality Check (38-45s)

**Goal**: Callback to hook, reveal what actually happened

**Tone**: Deadpan irony, dark humor

**Punchline Types**:

**Option A - He Never Did It**:
"Skulsy didn't buy. He kept the $10,000 in savings. At 0.5% interest."

**Option B - He Sold Early**:
"Skulsy did buy. Sold in 2005 at $45. Made $90,000. Missed $6.9 million."

**Option C - He Almost Did**:
"Skulsy had the money. He bought a car instead. It's worth $2,000 now."

**Option D - Perfect Hindsight**:
"All he needed was perfect timing. And to ignore everyone's advice. And to hold through 3 crashes."

**State**: `"state": "punchline"`  
**Intensity**: 0.85-0.95  

**Retention Trigger**: "callback" (references the hook)

**Visual Cue**: Split screen or comparison graphic (what could've been vs what was)

---

## Pattern-Specific Retention Mechanics

### The Compounding Surprise

Unlike other patterns, "what if" relies on **exponential growth surprise**.

**Technique**: Each timeline jump should feel bigger than expected.

**Example**:
```
"His $100 became $1,000"  (10x - expected)
"Then $10,000"             (10x again - still expected)
"Then $250,000"            (25x - WHOA)
"Then $2.4 million"        (10x - getting absurd)
```

**Rule**: At least ONE jump should exceed 10x to create surprise.

---

### The Near-Miss Hook

Viewers must feel "I could've done this" + "I missed it by THIS much"

**Techniques**:
- Emphasize the entry barrier was LOW ($100, $1,000)
- Show the decision point was CLEAR (exact date)
- Prove the knowledge was AVAILABLE (hindsight wasn't needed)

**Example**:
"Anyone with $100 could've bought. The price was public. The date was March 17, 2001."

---

### The Alternate Reality

Create cognitive dissonance by maintaining the hypothetical throughout, then crashing to reality at the end.

**Structure**:
```
"He'd own..."  (maintaining hypothetical)
"It would've..." (still hypothetical)
"By now, he'd..." (hypothetical continues)
"But he didn't." (crash to reality)
```

---

## Voice & Narrative Guidelines

### Show the Math

This pattern requires SHOWING calculations, not just results.

❌ BAD: "He would've made a lot of money"  
✅ GOOD: "At $5 per share, he'd own 2,000 shares. At $3,500 per share, that's $7 million."

### Maintain Deadpan

Don't editorialize the absurdity. Let the numbers speak.

❌ BAD: "This is absolutely insane!"  
✅ GOOD: "His $10,000 became $7 million."

### No Moralizing

Avoid "lessons" or "if only" language.

❌ BAD: "If only he'd been patient..."  
✅ GOOD: "He sold in 2005."

---

## Visual Direction (Pattern-Specific)

### Beat 1 (Hook)
- Skulsy with cash/wallet
- Asset logo/chart in background
- Year displayed prominently

### Beat 2-4 (Growth Timeline)
- Animated price chart climbing
- Dollar amounts growing on screen
- Calendar pages flipping (showing years)
- Skulsy's expression unchanging (contrast to rising numbers)

### Beat 5 (Punchline)
- Split screen: What could've been vs what happened
- OR: Empty wallet/zero balance
- OR: Skulsy watching the chart from the sidelines

---

## Research Integration Requirements

This pattern REQUIRES from `research_data`:

**MANDATORY**:
- `entry_price`: Exact price at decision point
- `entry_year`: Exact year
- `exit_price` or `current_price`: Final value
- `exit_year` or current year
- `roi`: ROI calculation

**HIGHLY RECOMMENDED**:
- 2-3 intermediate prices (for timeline progression)
- Key events during the period (crashes, rallies)
- Comparison asset (S&P 500, gold, etc.)

**Example Research Data Usage**:
```json
{
  "core_facts": [
    "Amazon stock was $5.97 in March 2001",
    "By December 2021, it reached $3,334",
    "A $10,000 investment would be worth $5.6 million"
  ]
}
```

Use these EXACT numbers in the script.

---

## Pattern-Specific Quality Metrics

### Compounding Clarity (0-100)

**Score based on**:
- Can viewer follow the math? (+50)
- Are all price points sourced from research? (+30)
- Does each jump feel earned? (+20)

**Passing**: 80+

---

### Reality Contrast (0-100)

**Score based on**:
- Does punchline create clear before/after? (+40)
- Is the gap between hypothetical and reality obvious? (+30)
- Does it callback to the hook? (+30)

**Passing**: 80+

---

## Common Mistakes to Avoid

### Mistake 1: Vague Entry Point

❌ BAD: "What if Skulsy bought Amazon early?"  
✅ GOOD: "What if Skulsy bought Amazon at $5.97 in March 2001?"

### Mistake 2: Skipping the Math

❌ BAD: "His money would've grown a lot"  
✅ GOOD: "At $5 per share, he'd own 2,000 shares. At $3,334, that's $6.6 million."

### Mistake 3: Weak Punchline

❌ BAD: "But he didn't invest"  
✅ GOOD: "He spent the $10,000 on a car. It's worth $1,200 now."

### Mistake 4: Too Many Timeline Jumps

❌ BAD: Showing 8 different years  
✅ GOOD: 3-4 strategic milestones (entry, mid, crash, peak)

### Mistake 5: Editorializing

❌ BAD: "This shows why patience matters in investing"  
✅ GOOD: [Let the numbers speak, no commentary]

---

## Example Script (Full Pattern)

**Topic**: "What if Skulsy bought Bitcoin 2011"

### Full Script Structure:

```json
{
  "title": "Skulsy's $100 Bitcoin Decision",
  "hook_variant": "number_shock",
  "sentences": [
    {
      "text": "What if Skulsy spent $100 on Bitcoin in 2011?",
      "state": "hook",
      "intensity": 0.6,
      "timeline_anchor": "2011",
      "retention_trigger": "number_shock",
      "visual_cue": "Skulsy holding $100 bill, Bitcoin logo background"
    },
    {
      "text": "At $1 per coin, he'd own 100 Bitcoins.",
      "state": "optimism",
      "intensity": 0.5,
      "timeline_anchor": null,
      "retention_trigger": "stakes",
      "visual_cue": "Calculator showing '100 BTC'"
    },
    {
      "text": "By 2013, Bitcoin hit $1,000.",
      "state": "growth",
      "intensity": 0.6,
      "timeline_anchor": "2013",
      "retention_trigger": "surprise",
      "visual_cue": "Chart climbing to $1,000"
    },
    {
      "text": "His $100 became $100,000.",
      "state": "growth",
      "intensity": 0.7,
      "timeline_anchor": null,
      "retention_trigger": "stakes",
      "visual_cue": "Counter: $100 → $100,000"
    },
    {
      "text": "He sold everything.",
      "state": "doubt",
      "intensity": 0.65,
      "timeline_anchor": null,
      "retention_trigger": "pattern_break",
      "visual_cue": "Skulsy clicking 'SELL ALL'"
    },
    {
      "text": "Called it a bubble that had to pop.",
      "state": "doubt",
      "intensity": 0.6,
      "timeline_anchor": null,
      "retention_trigger": "irony_setup",
      "visual_cue": "Skulsy arms crossed, confident"
    },
    {
      "text": "By 2017, Bitcoin reached $20,000.",
      "state": "regret",
      "intensity": 0.8,
      "timeline_anchor": "2017",
      "retention_trigger": "stakes",
      "visual_cue": "Chart rocketing past $20k"
    },
    {
      "text": "His 100 coins would've been worth $2 million.",
      "state": "consequence",
      "intensity": 0.9,
      "timeline_anchor": null,
      "retention_trigger": "stakes",
      "visual_cue": "Calculator: $2,000,000"
    },
    {
      "text": "By 2021, Bitcoin hit $69,000.",
      "state": "consequence",
      "intensity": 0.95,
      "timeline_anchor": "2021",
      "retention_trigger": "surprise",
      "visual_cue": "Chart peak at $69k"
    },
    {
      "text": "That's $6.9 million.",
      "state": "consequence",
      "intensity": 1.0,
      "timeline_anchor": null,
      "retention_trigger": "stakes",
      "visual_cue": "Final number display"
    },
    {
      "text": "Instead, he walked away with $100,000.",
      "state": "punchline",
      "intensity": 0.85,
      "timeline_anchor": null,
      "retention_trigger": "contrast",
      "visual_cue": "Split: $100k vs $6.9M"
    },
    {
      "text": "And watched from the sidelines.",
      "state": "punchline",
      "intensity": 0.8,
      "timeline_anchor": null,
      "retention_trigger": "callback",
      "visual_cue": "Skulsy alone, chart in distance"
    }
  ],
  "beat_map": {
    "hook": [0.0, 3.0],
    "setup": [3.0, 10.0],
    "timeline": [10.0, 28.0],
    "consequence": [28.0, 38.0],
    "punchline": [38.0, 42.0]
  }
}
```

---

**Pattern Comparison Checklist**:

Before submitting:
- [ ] Hook contains specific dollar amount + year
- [ ] Entry price is from research (exact)
- [ ] Timeline shows 3-4 price milestones
- [ ] Each jump is calculated (viewers can follow math)
- [ ] Peak value is emphasized
- [ ] Punchline reveals what actually happened
- [ ] Punchline callbacks to initial amount
- [ ] No moralizing or lessons
- [ ] All numbers match research exactly

---

**Pattern Type**: What If  
**Difficulty**: Medium  
**Best For**: Large ROI stories, missed opportunities, FOMO content  
**Version**: 1.0  
**Last Updated**: 2025-02-08
