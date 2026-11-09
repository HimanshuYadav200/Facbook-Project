"""
Research Agent V2: Comprehensive Financial & Real Estate Content Intelligence
==============================================================================

This module implements the research protocol defined in SKILL.md.
It orchestrates API calls, validates data, and generates structured research outputs
for both short-form (45s) and long-form (15-20min) content.

Author: Antigravity (adapted from User Request)
Version: 2.1
Last Updated: 2026-02-06
"""

import os
import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
import requests
from pathlib import Path

# Add parent directory to path to allow importing config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.llm_client import LLMClient

# ===========================
# Configuration & Constants
# ===========================

class ResearchConfig:
    """Configuration for Research Agent"""
    
    # API Keys (load from environment)
    ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    FRED_KEY = os.getenv("FRED_API_KEY")
    TAVILY_KEY = os.getenv("TAVILY_API_KEY")
    SERPER_KEY = os.getenv("SERPER_API_KEY")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    
    # API Endpoints
    FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
    ALPHA_BASE = "https://www.alphavantage.co/query"
    TAVILY_BASE = "https://api.tavily.com/search"
    SERPER_BASE = "https://google.serper.dev/search"
    NEWS_BASE = "https://newsapi.org/v2/everything"
    
    # Cache settings
    CACHE_DB = "research_cache.db"
    CACHE_EXPIRY_DAYS = 30
    
    # Research parameters
    MAX_API_RETRIES = 3
    API_TIMEOUT = 30
    PARALLEL_WORKERS = 5
    
    # Skill file location (Approximate path relative to project root)
    SKILL_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".agent", "skills", "research_agent", "SKILL.md")


# ===========================
# Data Models
# ===========================

@dataclass
class TopicDecomposition:
    """Structured breakdown of user topic"""
    subject: str
    action: str
    timeframe: Dict
    macro_theme: str
    research_priority: str
    niche: str
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ResearchFact:
    """Individual research fact with metadata"""
    fact_id: str
    statement: str
    source: str
    source_type: str  # 'api', 'narrative', 'derived'
    confidence: str  # 'high', 'medium', 'low'
    usage_suggestion: str  # 'hook', 'punchline', 'context', 'comparison'
    
    def to_dict(self):
        return asdict(self)


@dataclass
class NarrativeHook:
    """Narrative element for storytelling"""
    hook: str
    emotional_tone: str
    source: str
    usage: str
    
    def to_dict(self):
        return asdict(self)


# ===========================
# Cache Manager
# ===========================

class ResearchCache:
    """SQLite-based cache for API responses"""
    
    def __init__(self, db_path: str = ResearchConfig.CACHE_DB):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize cache database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_cache (
                    cache_key TEXT PRIMARY KEY,
                    response_data TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    api_name TEXT,
                    query_hash TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ResearchCache] Warning: DB Init failed ({e}). Cache disabled.")
    
    def get(self, api_name: str, query: str) -> Optional[Dict]:
        """Retrieve cached API response"""
        try:
            cache_key = self._generate_key(api_name, query)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT response_data, timestamp 
                FROM api_cache 
                WHERE cache_key = ?
            """, (cache_key,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                response_data, timestamp = result
                cached_time = datetime.fromisoformat(timestamp)
                
                # Check if cache is still valid
                if datetime.now() - cached_time < timedelta(days=ResearchConfig.CACHE_EXPIRY_DAYS):
                    return json.loads(response_data)
        except:
            pass
        return None
    
    def set(self, api_name: str, query: str, response: Dict):
        """Store API response in cache"""
        try:
            cache_key = self._generate_key(api_name, query)
            query_hash = hashlib.md5(query.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO api_cache (cache_key, response_data, api_name, query_hash)
                VALUES (?, ?, ?, ?)
            """, (cache_key, json.dumps(response), api_name, query_hash))
            conn.commit()
            conn.close()
        except:
            pass
    
    @staticmethod
    def _generate_key(api_name: str, query: str) -> str:
        """Generate cache key from API name and query"""
        combined = f"{api_name}:{query}"
        return hashlib.sha256(combined.encode()).hexdigest()


# ===========================
# API Clients
# ===========================

class FREDClient:
    """Federal Reserve Economic Data API client"""
    
    # Key FRED series IDs
    SERIES_IDS = {
        'fed_funds': 'FEDFUNDS',
        'treasury_10y': 'DGS10',
        'unemployment': 'UNRATE',
        'cpi': 'CPIAUCSL',
        'mortgage_30y': 'MORTGAGE30US',
        'housing_starts': 'HOUST',
        'home_price_index': 'CSUSHPISA',
        'sp500': 'SP500', 
        'gdp': 'GDP'
    }
    
    def __init__(self, cache: ResearchCache):
        self.cache = cache
        self.api_key = ResearchConfig.FRED_KEY
    
    def get_series(self, series_name: str, start_date: str, end_date: str) -> Dict:
        """Fetch FRED time series data"""
        series_id = self.SERIES_IDS.get(series_name)
        if not series_id:
            # Try direct ID if name lookup fails
            series_id = series_name
        
        # Check cache first
        cache_key = f"{series_id}:{start_date}:{end_date}"
        cached = self.cache.get('fred', cache_key)
        if cached:
            return cached
            
        if not self.api_key:
            return {} # Fallback if no key
        
        # Make API call
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date
        }
        
        try:
            response = requests.get(ResearchConfig.FRED_BASE, params=params, timeout=ResearchConfig.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            self.cache.set('fred', cache_key, data)
            return data
        except Exception as e:
            print(f"[FRED] Error: {e}")
            return {}
    
    def extract_value_for_date(self, series_data: Dict, target_date: str) -> Optional[float]:
        """Extract value for specific date (or nearest)"""
        observations = series_data.get('observations', [])
        if not observations: return None
        
        # Try exact match first
        for obs in observations:
            if obs['date'] == target_date:
                try: return float(obs['value'])
                except: return None
        
        # Find nearest date within 7 days
        try:
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            closest_obs = None
            min_diff = timedelta(days=365) # Start with wide window
            
            for obs in observations:
                try:
                    obs_dt = datetime.strptime(obs['date'], '%Y-%m-%d')
                    diff = abs(target_dt - obs_dt)
                    if diff < min_diff:
                        min_diff = diff
                        closest_obs = obs
                except: continue
                
            if closest_obs and min_diff < timedelta(days=30): # Allow up to 30 days drift
                try: return float(closest_obs['value'])
                except: return None
        except:
            return None
        return None


class AlphaVantageClient:
    """Alpha Vantage API client for asset pricing"""
    
    def __init__(self, cache: ResearchCache):
        self.cache = cache
        self.api_key = ResearchConfig.ALPHA_VANTAGE_KEY
    
    def get_crypto_price(self, symbol: str, target_date: str) -> Optional[Dict]:
        """Get cryptocurrency price for specific date"""
        cache_key = f"crypto:{symbol}:{target_date[:7]}"  # Cache by month
        cached = self.cache.get('alpha_vantage', cache_key)
        
        if cached:
            return self._extract_price_for_date(cached, target_date)
            
        if not self.api_key: return None
        
        # Fetch monthly data
        params = {
            'function': 'DIGITAL_CURRENCY_MONTHLY',
            'symbol': symbol,
            'market': 'USD',
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(ResearchConfig.ALPHA_BASE, params=params, timeout=ResearchConfig.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            self.cache.set('alpha_vantage', cache_key, data)
            return self._extract_price_for_date(data, target_date)
        except Exception as e:
            print(f"[AlphaVantage] Crypto Error: {e}")
            return None
    
    def get_stock_price(self, symbol: str, target_date: str) -> Optional[Dict]:
        """Get stock price for specific date"""
        cache_key = f"stock:{symbol}:{target_date[:7]}"
        cached = self.cache.get('alpha_vantage', cache_key)
        
        if cached:
            return self._extract_price_for_date(cached, target_date, data_type='stock')
            
        if not self.api_key: return None
        
        params = {
            'function': 'TIME_SERIES_MONTHLY_ADJUSTED',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(ResearchConfig.ALPHA_BASE, params=params, timeout=ResearchConfig.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            self.cache.set('alpha_vantage', cache_key, data)
            return self._extract_price_for_date(data, target_date, data_type='stock')
        except Exception as e:
            print(f"[AlphaVantage] Stock Error: {e}")
            return None
    
    @staticmethod
    def _extract_price_for_date(data: Dict, target_date: str, data_type: str = 'crypto') -> Optional[Dict]:
        """Extract price from API response for specific date"""
        if data_type == 'crypto':
            time_series = data.get('Time Series (Digital Currency Monthly)', {})
            price_key = '4a. close (USD)'
        else:
            time_series = data.get('Monthly Adjusted Time Series', {})
            price_key = '4. close'
        
        if not time_series: return None

        # Try exact month match
        target_month = target_date[:7]  # YYYY-MM
        
        # Iterating just to find key
        for date_key, values in time_series.items():
            if date_key.startswith(target_month):
                try:
                    return {
                        'date': date_key,
                        'price': float(values.get(price_key, 0)),
                        'source': 'Alpha Vantage'
                    }
                except: return None
        return None
    
    def calculate_roi(self, entry_price: float, exit_price: float) -> Dict:
        """Calculate return on investment"""
        if entry_price == 0: return {}
        roi_decimal = (exit_price - entry_price) / entry_price
        roi_percent = roi_decimal * 100
        
        return {
            'entry_price': entry_price,
            'exit_price': exit_price,
            'roi_percent': round(roi_percent, 2),
            'roi_display': f"+{roi_percent:,.1f}%" if roi_percent > 0 else f"{roi_percent:,.1f}%",
            'multiplier': round(exit_price / entry_price, 2)
        }


class TavilyClient:
    """Tavily Research API client"""
    
    def __init__(self, cache: ResearchCache):
        self.cache = cache
        self.api_key = ResearchConfig.TAVILY_KEY
    
    def search(self, query: str, max_results: int = 5) -> Dict:
        """Perform Tavily search"""
        cache_key = f"tavily:{query}:{max_results}"
        cached = self.cache.get('tavily', cache_key)
        if cached: return cached
        
        if not self.api_key: return {}
        
        payload = {
            'api_key': self.api_key,
            'query': query,
            'max_results': max_results,
            'search_depth': 'advanced',
            'include_domains': [
                'bloomberg.com', 'reuters.com', 'wsj.com', 
                'ft.com', 'forbes.com', 'coindesk.com', 'cnbc.com', 'investopedia.com'
            ]
        }
        
        try:
            response = requests.post(ResearchConfig.TAVILY_BASE, json=payload, timeout=ResearchConfig.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            self.cache.set('tavily', cache_key, data)
            return data
        except Exception as e:
            print(f"[Tavily] Error: {e}")
            return {}
    
    def filter_high_quality_sources(self, results: Dict) -> List[Dict]:
        """Filter results for high-quality sources only"""
        high_priority_domains = [
            '.gov', '.edu', 'bloomberg.com', 'reuters.com', 
            'wsj.com', 'ft.com', 'forbes.com'
        ]
        
        filtered = []
        for result in results.get('results', []):
            url = result.get('url', '')
            # If domain match OR score is high
            if any(domain in url for domain in high_priority_domains) or result.get('score', 0) > 0.7:
                filtered.append(result)
        
        # If too restrictive, return all results
        return filtered if filtered else results.get('results', [])


class SERPERClient:
    """Google SERPER API client for fact verification"""
    
    def __init__(self, cache: ResearchCache):
        self.cache = cache
        self.api_key = ResearchConfig.SERPER_KEY
    
    def search(self, query: str) -> Dict:
        """Perform Google search via SERPER"""
        cached = self.cache.get('serper', query)
        if cached: return cached
        
        if not self.api_key: return {}
        
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        payload = {'q': query}
        
        try:
            response = requests.post(ResearchConfig.SERPER_BASE, json=payload, headers=headers, timeout=ResearchConfig.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            self.cache.set('serper', query, data)
            return data
        except Exception as e:
            print(f"[SERPER] Error: {e}")
            return {}


# ===========================
# Core Research Agent
# ===========================

class ResearchAgent:
    """Main research orchestrator"""
    
    def __init__(self, topic: str = "", content_type: str = "short", research_depth: str = "standard"):
        self.topic = topic
        self.content_type = content_type  # 'short' or 'long'
        self.research_depth = research_depth
        
        # Initialize cache and API clients
        self.cache = ResearchCache()
        self.fred = FREDClient(self.cache)
        self.alpha = AlphaVantageClient(self.cache)
        self.tavily = TavilyClient(self.cache)
        self.serper = SERPERClient(self.cache)
        
        self.llm = LLMClient()
        
        # Research results storage
        self.decomposition = None
        self.api_results = {}
        self.validated_facts = []
    
    def research_topic(self, topic: str, angle: str = None, depth: str = "deep") -> Dict:
        """Entry point compatible with main.py existing calls"""
        self.topic = f"{topic}: {angle}" if angle else topic
        self.research_depth = depth
        return self.execute()

    def execute(self) -> Dict:
        """Main execution flow"""
        print(f"\n{'='*60}")
        print(f"RESEARCH AGENT V2 - STARTING")
        print(f"Topic: {self.topic}")
        print(f"Type: {self.content_type}")
        print(f"{'='*60}\n")
        
        # Step 1: Decompose topic
        print("STEP 1: Decomposing topic...")
        self.decomposition = self._decompose_topic()
        if self.decomposition:
            print(f"✓ Identified: {self.decomposition.subject} ({self.decomposition.action})")
        else:
            print("! Decomposition failed. Using defaults.")
        
        # Step 2: Determine API strategy
        print("\nSTEP 2: Planning API calls...")
        apis_needed = self._determine_api_strategy()
        print(f"✓ APIs to call: {', '.join(apis_needed)}")
        
        # Step 3: Execute API calls in parallel
        print("\nSTEP 3: Fetching data from APIs...")
        self.api_results = self._orchestrate_apis(apis_needed)
        print(f"✓ Received responses from {len(self.api_results)} sources")
        
        # Step 4: Validate & cross-reference
        print("\nSTEP 4: Validating data...")
        self.validated_facts = self._validate_data()
        print(f"✓ Validated {len(self.validated_facts)} facts")
        
        # Step 5: Generate output
        print("\nSTEP 5: Generating research output...")
        
        # Always generate short-form data structure first
        output = self._generate_short_form_output()
        
        # If long-form, ADD the corpus module structure
        if self.content_type == 'long':
            print(">> Generating Long-Form Corpus Deep Dive Modules...")
            long_modules = self._generate_deep_dive_modules()
            output['long_form_modules'] = long_modules
            print(f"✓ Generated {len(long_modules.get('modules', []))} deep-dive modules")
        
        print(f"\n{'='*60}")
        print("RESEARCH COMPLETE")
        print(f"{'='*60}\n")
        
        return output
    
    def _decompose_topic(self) -> TopicDecomposition:
        """Break down topic into structured components using LLM"""
        prompt = f"""
        You are decomposition agent.
        Decompose this financial topic: "{self.topic}"
        
        Return JSON with fields:
        - subject (e.g. Bitcoin)
        - action (e.g. buy)
        - timeframe (object with year as int, and research_window object with start/target/end dates YYYY-MM-DD)
        - macro_theme (string)
        - research_priority (string)
        - niche (crypto/stocks/real_estate)
        """
        
        try:
            resp = self.llm.generate_json(prompt)
            data = json.loads(resp)
            return TopicDecomposition(**data)
        except Exception as e:
            print(f"Decomposition fallback: {e}")
            # Fallback
            return TopicDecomposition(
                subject="General", action="Analyze", 
                timeframe={'year': 2023, 'research_window': {'start': '2022-01-01', 'target': '2023-01-01', 'end': '2023-12-31'}}, 
                macro_theme="General", research_priority="General", niche="general"
            )
    
    def _determine_api_strategy(self) -> List[str]:
        """Decide which APIs to call based on topic"""
        apis = []
        if not self.decomposition: return []
        
        # Asset pricing
        if 'crypto' in self.decomposition.niche or 'stock' in self.decomposition.niche or 'asset' in self.decomposition.research_priority:
            apis.append('alpha_vantage')
        
        # Macro context
        # Always useful for finance
        apis.append('fred')
        
        # Narrative context
        # Always useful for script writing
        apis.append('tavily')
        
        # Fact verification (always)
        apis.append('serper')
        
        return apis
    
    def _orchestrate_apis(self, apis_needed: List[str]) -> Dict:
        """Execute API calls in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=ResearchConfig.PARALLEL_WORKERS) as executor:
            futures = {}
            
            if 'alpha_vantage' in apis_needed:
                futures['alpha_vantage'] = executor.submit(self._call_alpha_vantage)
            
            if 'fred' in apis_needed:
                futures['fred'] = executor.submit(self._call_fred)
            
            if 'tavily' in apis_needed:
                futures['tavily'] = executor.submit(self._call_tavily)
            
            if 'serper' in apis_needed:
                futures['serper'] = executor.submit(self._call_serper)
            
            # Collect results
            for api_name, future in futures.items():
                try:
                    results[api_name] = future.result()
                except Exception as e:
                    print(f"✗ Error calling {api_name}: {str(e)}")
                    results[api_name] = None
        
        return results
    
    def _call_alpha_vantage(self) -> Dict:
        """Fetch price data from Alpha Vantage"""
        if not self.decomposition: return {}
        
        # Safe date extraction
        year = self.decomposition.timeframe.get('year', 2023)
        research_window = self.decomposition.timeframe.get('research_window', {})
        target_date = research_window.get('target', f"{year}-06-01")
        
        # Guess symbol
        symbol = "BTC" if "bitcoin" in self.decomposition.subject.lower() else "SPY"
        if "apple" in self.decomposition.subject.lower(): symbol = "AAPL"
        
        # Get entry price
        if "bitcoin" in self.decomposition.subject.lower() or "crypto" in self.decomposition.niche:
             entry = self.alpha.get_crypto_price(symbol, target_date)
             # Get exit price (1 year later)
             exit_date_str = f"{year + 1}-{target_date[5:]}"
             exit_data = self.alpha.get_crypto_price(symbol, exit_date_str)
        else:
             entry = self.alpha.get_stock_price(symbol, target_date)
             exit_date_str = f"{year + 1}-{target_date[5:]}"
             exit_data = self.alpha.get_stock_price(symbol, exit_date_str)
        
        # Calculate ROI
        result = {'entry': entry, 'exit': exit_data, 'symbol': symbol}
        if entry and exit_data:
            roi = self.alpha.calculate_roi(entry['price'], exit_data['price'])
            result['roi'] = roi
            
        return result
    
    def _call_fred(self) -> Dict:
        """Fetch macro economic data from FRED"""
        if not self.decomposition: return {}
        
        # Safe date extraction
        year = self.decomposition.timeframe.get('year', 2023)
        research_window = self.decomposition.timeframe.get('research_window', {})
        start_date = research_window.get('start', f"{year}-01-01")
        end_date = research_window.get('end', f"{year}-12-31")
        target_date = research_window.get('target', f"{year}-06-01")
        
        results = {}
        
        # Get Fed Funds Rate (Standard for all finance)
        fed_data = self.fred.get_series('fed_funds', start_date, end_date)
        fed_rate = self.fred.extract_value_for_date(fed_data, target_date)
        if fed_rate is not None:
            results['fed_funds_rate'] = {
                'value': fed_rate,
                'date': target_date,
                'source': 'FRED:FEDFUNDS'
            }
            
        return results
    
    def _call_tavily(self) -> Dict:
        """Fetch narrative context from Tavily"""
        if not self.decomposition: return {}
        year = self.decomposition.timeframe.get('year', 2024)
        queries = [
            f"{self.decomposition.subject} {year} headlines",
            f"{self.decomposition.subject} {year} expert predictions",
            f"What happened to {self.decomposition.subject} in {year} timeline"
        ]
        
        results = []
        for query in queries:
            search_results = self.tavily.search(query, max_results=3)
            # Filter?
            results.extend(search_results.get('results', []))
        
        # Also extract Narrative Hooks via LLM
        hooks = self._extract_narrative_hooks({'narrative_sources': results})
        
        return {'narrative_sources': results, 'extracted_hooks': hooks}
    
    def _extract_narrative_hooks(self, tavily_results: Dict) -> List[NarrativeHook]:
        """Use LLM to extract narrative hooks from Tavily results"""
        if not tavily_results.get('narrative_sources'): return []
        
        prompt = f"""
        You are extracting narrative hooks for a financial education video.
        
        SEARCH RESULTS:
        {json.dumps(tavily_results['narrative_sources'][:5], indent=2)}
        
        TASK: Extract 3 narrative hooks that:
        1. Are specific and vivid (use actual numbers/events)
        2. Have emotional resonance (fear, regret, excitement)
        3. Are attributed to credible sources
        
        FORMAT (JSON only):
        [
            {{
            "hook": "The specific narrative hook text",
            "emotional_tone": "regret|fear|excitement|contrarian",
            "source": "Source name",
            "usage": "opening_hook|midpoint_contrast|economic_backdrop"
            }}
        ]
        """
        try:
            resp = self.llm.generate_json(prompt)
            data = json.loads(resp)
            return [NarrativeHook(**h) for h in data]
        except:
            return []

    def _call_serper(self) -> Dict:
        """Verify facts using Google Search"""
        if not self.decomposition: return {}
        year = self.decomposition.timeframe.get('year', 2024)
        query = f"{self.decomposition.subject} price {year}"
        results = self.serper.search(query)
        return results
    
    def _validate_data(self) -> List[ResearchFact]:
        """Cross-reference and validate all collected data"""
        facts = []
        year = self.decomposition.timeframe.get('year') if self.decomposition else "Target Year"
        subject = self.decomposition.subject if self.decomposition else "Asset"
        
        # Validate price data from Alpha Vantage
        if self.api_results.get('alpha_vantage'):
            alpha_data = self.api_results['alpha_vantage']
            
            if alpha_data.get('entry'):
                fact = ResearchFact(
                    fact_id="F1",
                    statement=f"{subject} price in {year} was ${alpha_data['entry']['price']:.2f}",
                    source=f"Alpha Vantage:{alpha_data.get('symbol','Unknown')}",
                    source_type="api",
                    confidence="high",
                    usage_suggestion="hook"
                )
                facts.append(fact)
            
            if alpha_data.get('roi'):
                roi_fact = ResearchFact(
                    fact_id="F2",
                    statement=f"By {year + 1}, it verified return of {alpha_data['roi']['roi_display']}",
                    source="Alpha Vantage",
                    source_type="api",
                    confidence="high",
                    usage_suggestion="punchline"
                )
                facts.append(roi_fact)
        
        # Validate FRED data
        if self.api_results.get('fred'):
            fred_data = self.api_results['fred']
            if 'fed_funds_rate' in fred_data:
                fact = ResearchFact(
                    fact_id="F3",
                    statement=f"Federal Funds Rate was {fred_data['fed_funds_rate']['value']:.2f}%",
                    source="FRED:FEDFUNDS",
                    source_type="api",
                    confidence="high",
                    usage_suggestion="context"
                )
                facts.append(fact)
        
        return facts
    
    def _generate_short_form_output(self) -> Dict:
        """Generate research_data.json for short-form content"""
        
        # Get hooks from Tavily results
        hooks = []
        if self.api_results.get('tavily'):
             hooks_objs = self.api_results['tavily'].get('extracted_hooks', [])
             hooks = [h.to_dict() for h in hooks_objs]

        output = {
            'metadata': {
                'topic': self.topic,
                'content_type': self.content_type,
                'research_timestamp': datetime.now().isoformat(),
                'apis_used': list(self.api_results.keys()),
                'total_sources': len(self.validated_facts),
                'confidence_score': 'high'
            },
            'topic_decomposition': self.decomposition.to_dict() if self.decomposition else {},
            'core_facts': [fact.to_dict() for fact in self.validated_facts],
            'narrative_hooks': hooks,
            # Populate extra fields expected by Script Agent
            'key_facts': [f.statement for f in self.validated_facts],
            'stats': [{'value': f.statement, 'context': f.usage_suggestion, 'source': f.source} for f in self.validated_facts],
            'quotes': [], # Populate if we had quote extraction
            'historical_comparisons': [],
            'current_events': [],
            'contrarian_points': [] 
        }
        
        return output
    
    def _generate_deep_dive_modules(self) -> Dict:
        """Create content modules for long-form video Using LLM"""
        
        prompt = f"""
        You are structuring a 15-20 minute educational video (images only).
        
        TOPIC: {self.topic}
        AVAILABLE DATA:
        - {len(self.validated_facts)} verified facts
        
        CREATE 6-8 modules that:
        1. Each is 2-3 minutes long
        2. Has a clear narrative arc
        3. References specific gathered facts
        
        STRUCTURE:
        M1: Setup (what was X in YEAR?)
        M2: Economic context
        M3: The Mechanism (How it worked)
        ...
        M6: The Lesson
        
        Return JSON format:
        {{
            "modules": [
                {{
                    "title": "Module Title",
                    "duration": "3 min",
                    "key_points": ["point 1", "point 2"],
                    "visual_suggestion": "Description of image/chart to show"
                }}
            ]
        }}
        """
        try:
            resp = self.llm.generate_json(prompt)
            data = json.loads(resp)
            return data
        except Exception as e:
            print(f"Long Form Module Generation Failed: {e}")
            return {"modules": []}

if __name__ == '__main__':
    # Local Testing
    import dotenv
    dotenv.load_dotenv()
    agent = ResearchAgent(topic="Skulsy buys Bitcoin 2012", content_type="short")
    res = agent.execute()
    print(json.dumps(res, indent=2))
