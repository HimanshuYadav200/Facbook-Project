import os
from dotenv import load_dotenv

# Load .env from project root (one level up)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')
print(f"[DEBUG] Loading .env from: {env_path}")
load_dotenv(env_path, override=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # Can be None for manual mode
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_API_KEY_BACKUP = os.getenv("ELEVENLABS_API_KEY_BACKUP")  # Failover key

# Configuration for Video
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
DURATION_TARGET = (30, 45)  # Seconds

# Agent Settings
IMAGE_MODEL_NAME = "gemini-3-pro-image-preview" # Validated available model
TEXT_MODEL_NAME = "gemini-3-pro-preview" # Validated available model

# Audio Settings
AUDIO_PROVIDER = "google"  # "google" or "elevenlabs"
GOOGLE_AUDIO_VOICE = "en-US-Journey-D" # "en-US-Journey-D" (Male), "en-US-Journey-F" (Female) or similar
GOOGLE_AUDIO_VOICE_PARABLE = "en-US-Neural2-D"  # Deep baritone for Mindlander-style parables

