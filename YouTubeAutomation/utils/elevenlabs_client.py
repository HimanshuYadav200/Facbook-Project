import sys
import os

# Add parent directory to path to allow importing config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class ElevenLabsClientManager:
    """
    Manages multiple ElevenLabs API keys with automatic failover.
    Switches to backup key when primary key's credits are exhausted.
    """
    
    def __init__(self):
        self.api_keys = []
        self.current_key_index = 0
        self.client = None
        
        # Load API keys from config
        if config.ELEVENLABS_API_KEY:
            self.api_keys.append(config.ELEVENLABS_API_KEY)
        if hasattr(config, 'ELEVENLABS_API_KEY_BACKUP') and config.ELEVENLABS_API_KEY_BACKUP:
            self.api_keys.append(config.ELEVENLABS_API_KEY_BACKUP)
        
        if not self.api_keys:
            print("[!] Warning: No ELEVENLABS_API_KEY configured.")
        else:
            # Only print this once to avoid spamming logs
            pass 
            # print(f"[*] ElevenLabs: {len(self.api_keys)} API key(s) available")
    
    def get_client(self):
        """Returns current ElevenLabs client, initializing if needed."""
        if self.client is None and self.api_keys:
            self._init_client()
        return self.client
    
    def _init_client(self):
        """Initialize client with current API key."""
        if self.current_key_index < len(self.api_keys):
            try:
                from elevenlabs.client import ElevenLabs
                current_key = self.api_keys[self.current_key_index]
                self.client = ElevenLabs(api_key=current_key)
                print(f"[*] Using ElevenLabs API key #{self.current_key_index + 1}")
            except ImportError:
                print("[!] ElevenLabs SDK not installed")
                self.client = None
    
    def switch_to_backup(self):
        """
        Switches to the next available API key.
        Returns True if switch successful, False if no more keys available.
        """
        self.current_key_index += 1
        
        if self.current_key_index >= len(self.api_keys):
            print("[!] All ElevenLabs API keys exhausted. No backup available.")
            return False
        
        print(f"\n[!] Switching to backup API key #{self.current_key_index + 1}...")
        self._init_client()
        return True
    
    def is_quota_error(self, error):
        """
        Checks if the error indicates quota/credits exhausted.
        """
        error_str = str(error).lower()
        # Common ElevenLabs quota error indicators
        quota_indicators = [
            "quota", "limit", "exceeded", "credits", "insufficient",
            "rate limit", "429", "too many requests", "exhausted",
            "subscription", "billing", "payment required", "402"
        ]
        return any(indicator in error_str for indicator in quota_indicators)
    
    def has_backup_available(self):
        """Check if there's a backup key available."""
        return self.current_key_index + 1 < len(self.api_keys)
