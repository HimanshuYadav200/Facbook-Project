import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'YouTubeAutomation', '.env')
print(f"Loading from: {env_path}")
print(f"Exists: {os.path.exists(env_path)}")

load_dotenv(env_path, override=True)

key = os.getenv("ELEVENLABS_API_KEY")
print(f"Key loaded: {key}")

with open(env_path, 'r') as f:
    print(f"File content (first line): {f.readline()}")
