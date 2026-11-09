# Research Agent Skill: Financial & Real Estate Content Intelligence System

## Mission Statement
Extract verifiable, multi-dimensional research data to power:
- **Short-form content** (45-60 seconds): Viral educational shorts with 3-5 punchy facts
- **Long-form content** (15-20 minutes): Deep-dive educational videos with comprehensive knowledge architecture

## Core Principles
1. **Facts over narratives** - Always prioritize hard data from primary sources
2. **Multi-source validation** - Cross-reference critical claims across 2+ sources
3. **Attribution discipline** - Every data point must have a traceable source
4. **Temporal accuracy** - Verify dates, prices, and events with precision
5. **Contrarian inclusion** - Always research opposing viewpoints and risks

---

# INPUT SCHEMA

```json
{
  "topic": "string (e.g., 'Skulsy buys Bitcoin 2012')",
  "content_type": "short" | "long",
  "research_depth": "standard" | "comprehensive",
  "niche": "personal_finance" | "real_estate" | "crypto" | "stocks" | "general",
  "target_year": "integer (optional, extracted from topic if not provided)",
  "custom_angles": ["string array of specific research angles user wants explored"]
}
```

---

# RESEARCH PROTOCOL

## STEP 1: Topic Decomposition & Intent Analysis

**Objective**: Break down the user's topic into structured research targets.

### Extraction Pattern:
From the topic string, identify:

1. **Primary Subject** (What is being discussed?)
   - Asset: Bitcoin, Real Estate, S&P 500, Gold, etc.
   - Person/Entity: Individual investor, company, institution
   
2. **Action/Decision** (What happened or what decision was made?)
   - Buy, Sell, Hold, Invest, Flip, Rent, Ignore
   
3. **Timeframe** (When did this occur?)
   - Exact date: "April 15, 2012"
   - Year: "2012"
   - Era: "during the 2008 crisis"
   - Present: "now", "today", "current"
   
4. **Macro Context** (What was happening in the broader economy/market?)
   - Economic conditions
   - Market sentiment
   - Competing opportunities

### Output Format:
```json
{
  "decomposition": {
    "subject": "Bitcoin",
    "action": "buy",
    "timeframe": {
      "year": 2012,
      "specificity": "year_only",
      "research_window": {
        "start": "2011-01-01",
        "target": "2012-06-01",
        "end": "2013-12-31"
      }
    },
    "macro_theme": "post-2008 recovery, zero interest rates, emerging crypto",
    "research_priority": "high_precision_pricing"
  }
}
```

### LLM Guidance:
```
You are decomposing a content topic for financial research.

TOPIC: {topic}

Extract the following with MAXIMUM precision:
1. What asset/subject is being discussed?
2. What action/decision occurred?
3. CRITICAL: What is the EXACT timeframe? If only a year is mentioned, assume mid-year (June) unless context suggests otherwise.
4. What was the broader economic/market context at that time?

If the topic is vague (e.g., "Skulsy makes a mistake"), flag it as "INSUFFICIENT_SPECIFICITY" and suggest 3 more specific alternatives.

Return as JSON only, no commentary.
```

---

## STEP 2: API Orchestration Strategy

**Objective**: Determine which APIs to call based on topic characteristics.

### Decision Tree:

```python
def determine_api_strategy(decomposition):
    apis = []
    
    # Asset pricing required?
    if decomposition['subject'] in ['Bitcoin', 'Ethereum', 'crypto', 'stock', 'index', 'commodity']:
        apis.append('alpha_vantage')
    
    # Macro economic context needed?
    if decomposition['timeframe']['year'] or 'interest rate' in topic or 'inflation' in topic:
        apis.append('fred')
    
    # Real estate specific?
    if decomposition['niche'] == 'real_estate':
        apis.extend(['fred_housing', 'zillow_api'])  # Zillow API optional
    
    # Narrative context (always for long-form, optional for short-form)?
    if content_type == 'long' or 'context' in decomposition['macro_theme']:
        apis.append('tavily')
    
    # Fact verification (always)?
    apis.append('serper')
    
    # Recent events only?
    if decomposition['timeframe']['year'] >= (current_year - 2):
        apis.append('news_api')
    
    return apis
```

### API Priority Matrix:

| Topic Type | Primary APIs | Secondary APIs | Rationale |
|------------|-------------|----------------|-----------|
| **Crypto (historical)** | Alpha Vantage, FRED | Tavily, SERPER | Need exact prices + macro context |
| **Crypto (recent)** | Alpha Vantage, NEWS_API | Tavily, SERPER | Add current news cycle |
| **Stocks/Indices** | Alpha Vantage, FRED | SERPER | Standard financial data |
| **Real Estate** | FRED (housing metrics), Zillow | Tavily, SERPER | Localized + macro data |
| **Macro Finance** | FRED, Tavily | SERPER | Economic indicators + narrative |
| **Current Events** | NEWS_API, Tavily | SERPER, FRED | Recency prioritized |

---

## STEP 3: API Execution Protocols

### 3.1 FRED API (Federal Reserve Economic Data)

**Use Case**: Macro economic indicators, interest rates, housing data

#### Query Construction:
```python
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

PARAMS = {
    "series_id": SERIES_ID,
    "api_key": API_KEY,
    "file_type": "json",
    "observation_start": "{YEAR}-01-01",
    "observation_end": "{YEAR}-12-31"
}
```

#### Key Series IDs (Topic-Based Selection):

**General Finance Topics:**
- `FEDFUNDS` - Federal Funds Effective Rate
- `DGS10` - 10-Year Treasury Constant Maturity Rate
- `T10YIE` - 10-Year Breakeven Inflation Rate
- `UNRATE` - Unemployment Rate
- `CPIAUCSL` - Consumer Price Index (All Urban Consumers)
- `DEXUSEU` - US/Euro Foreign Exchange Rate

**Real Estate Specific:**
- `MORTGAGE30US` - 30-Year Fixed Rate Mortgage Average
- `HOUST` - Housing Starts (Total New Privately Owned)
- `CSUSHPISA` - S&P CoreLogic Case-Shiller Home Price Index
- `MSPUS` - Median Sales Price of Houses Sold (US)
- `RRVRUSQ156N` - Homeownership Rate

**Stock Market Context:**
- `SP500` - S&P 500 Index
- `NASDAQCOM` - NASDAQ Composite Index
- `VIXCLS` - CBOE Volatility Index (VIX)

#### Extraction Rules:

**For SHORT-FORM:**
```json
{
  "metric_name": "Federal Funds Rate",
  "value": "0.16%",
  "date": "2012-06-01",
  "context": "near-zero rates for quantitative easing",
  "source": "FRED:FEDFUNDS",
  "confidence": "high"
}
```

Extract ONLY:
- 1 data point for the target date
- 1 comparison point (1 year prior OR current for perspective)
- Maximum 3 metrics total

**For LONG-FORM:**
```json
{
  "series_name": "Federal Funds Rate",
  "series_id": "FEDFUNDS",
  "data_points": [
    {"date": "2011-01", "value": 0.17},
    {"date": "2011-06", "value": 0.09},
    // ... monthly data for ±2 years
    {"date": "2013-12", "value": 0.08}
  ],
  "statistical_summary": {
    "min": 0.07,
    "max": 0.25,
    "mean": 0.14,
    "trend": "flat_near_zero"
  },
  "source": "FRED:FEDFUNDS"
}
```

#### LLM Prompt Template:
```
You are extracting data from FRED API responses.

API RESPONSE:
{raw_fred_json}

TASK: Extract the Federal Funds Rate for June 2012 and June 2011.

RULES:
1. Return format: {metric}: {value}% ({YYYY-MM-DD})
2. If exact date unavailable, use closest available date within 7 days
3. If no data found, return: "DATA_UNAVAILABLE"
4. Include source as: FRED:{SERIES_ID}

OUTPUT (JSON only):
```

---

### 3.2 Alpha Vantage API (Asset Pricing)

**Use Case**: Stock prices, crypto prices, forex, commodities

#### Query Construction:

**For Cryptocurrency:**
```python
URL = "https://www.alphavantage.co/query"
PARAMS = {
    "function": "DIGITAL_CURRENCY_MONTHLY",
    "symbol": "BTC",
    "market": "USD",
    "apikey": API_KEY
}
```

**For Stocks/Indices:**
```python
PARAMS = {
    "function": "TIME_SERIES_MONTHLY_ADJUSTED",
    "symbol": "SPY",  # or AAPL, TSLA, etc.
    "apikey": API_KEY
}
```

**For Daily Precision (if needed):**
```python
PARAMS = {
    "function": "TIME_SERIES_DAILY",
    "symbol": "BTC",
    "outputsize": "full",  # Up to 20 years
    "apikey": API_KEY
}
```

#### Extraction Rules:

**For SHORT-FORM:**
Extract exactly 2-3 price points:
1. **Entry price** (at decision date)
2. **Exit price** (1 year later OR at peak OR current)
3. **Comparison asset** (e.g., S&P 500 for same period)

```json
{
  "asset": "Bitcoin",
  "entry": {
    "date": "2012-04-15",
    "price": 5.27,
    "source": "Alpha Vantage:BTC-USD"
  },
  "outcome": {
    "date": "2013-04-15",
    "price": 266.00,
    "roi_percent": 4947.25,
    "roi_display": "+4,947%"
  },
  "comparison": {
    "asset": "S&P 500",
    "roi_percent": 18.5,
    "verdict": "Bitcoin outperformed by 267x"
  }
}
```

**For LONG-FORM:**
```json
{
  "asset": "Bitcoin",
  "price_series": {
    "monthly": {
      "2011-01": 0.30,
      "2011-02": 0.95,
      // ... full series
      "2013-12": 754.01
    },
    "key_milestones": [
      {
        "date": "2011-06-08",
        "price": 31.91,
        "event": "First major bubble peak",
        "source": "Alpha Vantage"
      },
      {
        "date": "2012-11-28",
        "price": 12.50,
        "event": "First halving event",
        "source": "Cross-referenced with blockchain data"
      }
    ]
  },
  "volatility_metrics": {
    "annualized_volatility": "189%",
    "max_drawdown": "-93% (June 2011 to Nov 2011)",
    "sharpe_ratio": "1.2"
  }
}
```

#### LLM Prompt Template:
```
You are extracting asset pricing data from Alpha Vantage API.

API RESPONSE:
{raw_alpha_vantage_json}

TARGET: Bitcoin price on 2012-04-15 (or closest available date)

RULES:
1. Use "4. close" field for price
2. If exact date unavailable, use nearest date within 30 days
3. Calculate ROI: ((later_price - initial_price) / initial_price) * 100
4. Format ROI as "+X,XXX%" with commas

REQUIRED OUTPUT:
- entry_date
- entry_price
- outcome_date (1 year later)
- outcome_price
- roi_percent

Return as JSON only.
```

---

### 3.3 Tavily Research API (Narrative Context & Expert Sources)

**Use Case**: News, expert opinions, historical context, event timelines

#### Query Strategy:

**For SHORT-FORM (3-5 targeted queries):**
```python
queries = [
    f"{asset} {year} major headlines",
    f"expert predictions {asset} {year}",
    f"{asset} criticism risks {year}"
]
```

**For LONG-FORM (10-15 comprehensive queries):**
```python
queries = [
    # Historical context
    f"what happened in {year} {industry}",
    f"{asset} timeline {year-1} to {year+1}",
    
    # Expert perspectives
    f"{asset} {year} institutional analysis",
    f"{asset} {year} expert forecasts",
    
    # Technical deep-dives
    f"how does {asset} work explained",
    f"{asset} technology overview",
    
    # Contrarian views
    f"{asset} {year} criticism",
    f"{asset} {year} risks failures",
    f"why {asset} will fail {year}",
    
    # Comparative analysis
    f"{asset} vs {alternative} {year}",
    
    # Cultural/social context
    f"{asset} {year} mainstream adoption",
    f"{asset} {year} regulatory landscape"
]
```

#### Source Quality Filtering:

**HIGH PRIORITY (Trust implicitly):**
- `.gov` domains
- `.edu` domains (university research)
- Major financial institutions: Bloomberg, Reuters, WSJ, FT, Forbes
- Industry leaders: CoinDesk (crypto), Zillow (real estate), S&P Global
- Academic journals: JSTOR, Google Scholar results

**EXCLUDE:**
- Reddit/Quora (except for cultural context in long-form)
- Obvious clickbait sites
- Sites with <40 Domain Authority
- Content farms

#### Extraction Rules:

**For SHORT-FORM:**
Extract maximum 5 narrative hooks:
```json
{
  "narrative_hooks": [
    {
      "hook": "Everyone was panicking about the Euro debt crisis",
      "source": "Reuters 2012 archive",
      "source_url": "reuters.com/article/...",
      "confidence": "high",
      "usage": "opening_context"
    },
    {
      "hook": "Paul Krugman called Bitcoin 'evil' in 2013",
      "source": "New York Times",
      "source_url": "nytimes.com/2013/...",
      "confidence": "high",
      "usage": "contrarian_view"
    }
  ]
}
```

**For LONG-FORM:**
```json
{
  "expert_perspectives": [
    {
      "quote": "Bitcoin represents a fundamental reimagining of money",
      "author": "Andreas Antonopoulos",
      "credentials": "Bitcoin educator, author of 'Mastering Bitcoin'",
      "source": "YouTube interview, 2012",
      "source_url": "...",
      "context": "Early advocate perspective",
      "timestamp_in_video": "suggested_for_module_2"
    }
  ],
  "critical_events": [
    {
      "date": "2012-03-01",
      "event": "Linode Bitcoin heist - 43,000 BTC stolen",
      "impact": "Highlighted security vulnerabilities",
      "source": "Bitcoin Magazine",
      "relevance": "counterargument_module"
    }
  ],
  "technical_explainers": [
    {
      "concept": "Blockchain proof-of-work",
      "explanation": "Miners compete to solve cryptographic puzzles...",
      "source": "bitcoin.org whitepaper",
      "eli5_version": "Like a global sudoku competition where winners get paid",
      "visual_suggestion": "Animated diagram of mining process"
    }
  ]
}
```

#### LLM Prompt Template:
```
You are analyzing Tavily search results for financial content research.

SEARCH QUERY: "{query}"
RESULTS: {tavily_json}

TASK: Extract the 3 most relevant, fact-based insights.

QUALITY CRITERIA:
1. Specific > Vague ("Bitcoin was $5" > "Bitcoin was cheap")
2. Attributed > Unattributed (name the expert/publication)
3. Surprising > Obvious (counterintuitive facts preferred)
4. Verifiable > Speculative (avoid "some say" or "reportedly")

OUTPUT: JSON array of insights with source attribution.
```

---

### 3.4 SERPER API (Google Search / Fact Verification)

**Use Case**: Verify specific facts, find exact dates, cross-reference claims

#### Query Strategy:

**Verification Queries:**
```python
queries = [
    f"when did {event} happen exact date",
    f"{asset} price on {specific_date}",
    f"is it true that {claim}",
    f"{person} said {quote} when",
]
```

#### Extraction Rules:

```json
{
  "verification_results": [
    {
      "claim": "Bitcoin's first halving was November 28, 2012",
      "verification": "CONFIRMED",
      "source": "Bitcoin Wiki (en.bitcoin.it)",
      "confidence": "high",
      "featured_snippet": true
    },
    {
      "claim": "MtGox handled 70% of Bitcoin volume in 2012",
      "verification": "APPROXIMATELY_CORRECT",
      "source": "CoinDesk historical analysis",
      "confidence": "medium",
      "note": "Estimates range from 65-80%"
    }
  ]
}
```

#### LLM Prompt Template:
```
You are fact-checking a specific claim using Google search results.

CLAIM TO VERIFY: {claim}
SEARCH RESULTS: {serper_json}

TASK: Determine if this claim is:
- CONFIRMED (multiple reliable sources agree)
- LIKELY_TRUE (one good source, or multiple medium sources)
- UNCERTAIN (conflicting information)
- DISPUTED (sources disagree)
- FALSE (clearly contradicted)

If CONFIRMED or LIKELY_TRUE, extract:
- Best source (name + URL)
- Exact quote supporting the claim
- Any important caveats

OUTPUT: JSON with verification status and evidence.
```

---

### 3.5 NEWS_API (Recent Events Only)

**Use Case**: Topics from the last 2 years, breaking news context

#### Query Construction:
```python
PARAMS = {
    "q": query,
    "from": "{target_date - 30 days}",
    "to": "{target_date + 7 days}",
    "language": "en",
    "sortBy": "relevancy",
    "apiKey": API_KEY
}
```

#### Extraction Rules:

```json
{
  "recent_headlines": [
    {
      "title": "Fed Raises Rates by 0.75% in Largest Hike Since 1994",
      "source": "Wall Street Journal",
      "published": "2022-06-15",
      "sentiment": "market_negative",
      "relevance_score": 0.95,
      "summary": "Federal Reserve aggressively combats inflation..."
    }
  ]
}
```

---

## STEP 4: Data Validation & Cross-Referencing

**Objective**: Ensure accuracy and flag conflicts.

### Validation Protocol:

#### Rule 1: Price Verification
```
IF alpha_vantage_price AND tavily_price DIFFER BY >10%:
    - Trust Alpha Vantage (primary source)
    - Flag discrepancy in metadata
    - Note: "Price estimates vary; using official API data"
```

#### Rule 2: Date Verification
```
IF multiple_sources_give_different_dates:
    - Use earliest credible source with exact date
    - If only year available, default to June 1st
    - Note uncertainty: "~Q2 2012" rather than "June 1, 2012"
```

#### Rule 3: Hallucination Detection
```
DISCARD_IF:
    - No source attribution
    - Source is "AI-generated content"
    - Contradicts official API data (FRED, Alpha Vantage)
    - Claim is from excluded source (Reddit, etc.)
```

#### Rule 4: Confidence Scoring
```python
def calculate_confidence(data_point):
    score = 0
    
    # Source quality
    if source in ['.gov', '.edu', 'Bloomberg', 'Reuters']:
        score += 40
    elif source in major_publications:
        score += 25
    else:
        score += 10
    
    # Cross-referenced?
    if cross_referenced_count >= 2:
        score += 30
    elif cross_referenced_count == 1:
        score += 15
    
    # Recency of source
    if source_date within 1_year_of_event:
        score += 20
    elif source_date within 5_years:
        score += 10
    
    # Data type
    if data_type == 'hard_number':
        score += 10
    
    return 'high' if score >= 70 else 'medium' if score >= 40 else 'low'
```

---

## STEP 5: Output Generation

### 5.1 SHORT-FORM OUTPUT: `research_data.json`

**File Location**: `assets/run_ID/research_data.json`

**Structure**:
```json
{
  "metadata": {
    "topic": "Skulsy buys Bitcoin 2012",
    "content_type": "short",
    "research_timestamp": "2025-02-07T14:30:00Z",
    "research_duration_seconds": 28,
    "apis_used": ["alpha_vantage", "fred", "tavily", "serper"],
    "total_sources": 12,
    "confidence_score": "high"
  },
  
  "topic_decomposition": {
    "subject": "Bitcoin",
    "action": "buy",
    "timeframe": {
      "target_date": "2012-04-15",
      "research_window": "2011-01-01 to 2013-12-31"
    }
  },
  
  "core_facts": [
    {
      "fact_id": "F1",
      "statement": "Bitcoin price in April 2012 was $5.27",
      "source": "Alpha Vantage:BTC-USD",
      "source_type": "api",
      "confidence": "high",
      "usage_suggestion": "hook"
    },
    {
      "fact_id": "F2",
      "statement": "By April 2013, Bitcoin reached $266 (+4,947% return)",
      "source": "Alpha Vantage:BTC-USD",
      "source_type": "api",
      "confidence": "high",
      "usage_suggestion": "punchline"
    },
    {
      "fact_id": "F3",
      "statement": "Federal Funds Rate was 0.16% (near-zero policy)",
      "source": "FRED:FEDFUNDS",
      "source_type": "api",
      "confidence": "high",
      "usage_suggestion": "context"
    },
    {
      "fact_id": "F4",
      "statement": "S&P 500 gained only 18.5% in the same period",
      "source": "Alpha Vantage:SPY",
      "source_type": "api",
      "confidence": "high",
      "usage_suggestion": "comparison"
    },
    {
      "fact_id": "F5",
      "statement": "Europe was in a debt crisis with Greece bailouts",
      "source": "Tavily:Reuters 2012 archive",
      "source_type": "narrative",
      "confidence": "high",
      "usage_suggestion": "scene_setting"
    }
  ],
  
  "narrative_hooks": [
    {
      "hook": "You could buy 1 Bitcoin for the price of a Chipotle burrito",
      "emotional_tone": "relatable_regret",
      "source": "Derived from price data",
      "usage": "opening_hook"
    },
    {
      "hook": "While everyone panicked about Europe collapsing",
      "emotional_tone": "contrarian_context",
      "source": "Tavily:Reuters",
      "usage": "midpoint_contrast"
    },
    {
      "hook": "The Fed had rates at basically zero for 3 straight years",
      "emotional_tone": "monetary_policy_context",
      "source": "FRED:FEDFUNDS",
      "usage": "economic_backdrop"
    }
  ]
}
```

### 5.2 LONG-FORM OUTPUT: Research Corpus

**File Location**: `assets/run_ID/research_corpus/*.json`

**Files**:
1. `metadata.json`: Overview of sources and stats
2. `timeline.json`: Year-by-year chronological events (15-30 events)
3. `data_series.json`: Full monthly price/macro data matrices
4. `sources.json`: Full citations and expert bio cards
5. `counterarguments.json`: Risk analysis and "Why you might be wrong"
6. `deep_dive_modules.json`: 6-8 structured modules (3-5 min each)
7. `visual_suggestions.json`: Charts, maps, and archival footage ideas
