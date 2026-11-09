import os
import sys
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")

print(f"Key loaded: {bool(api_key)}")

try:
    import elevenlabs
    print(f"ElevenLabs Version: {elevenlabs.__version__ if hasattr(elevenlabs, '__version__') else 'Unknown'}")
    print(f"ElevenLabs dir: {dir(elevenlabs)}")
except ImportError:
    print("ElevenLabs not installed")

try:
    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=api_key)
    print(f"Client dir: {dir(client)}")
    
    # Try text_to_speech
    if hasattr(client, 'text_to_speech'):
        print("Attempting text_to_speech.convert...")
        try:
            gen = client.text_to_speech.convert(
                text="Hello world",
                voice_id="pNInz6obpgDQGcFmaJgB",
                model_id="eleven_monolingual_v1"
            )
            print("Generator created.")
            audio_data = b"".join(gen)
            print(f"Audio Generated: {len(audio_data)} bytes")
        except Exception as e:
            print(f"text_to_speech failed: {e}")

except Exception as e:
    print(f"Client init failed: {e}")

# Try legacy
try:
    from elevenlabs import generate
    print("Attempting legacy generate...")
    generate(text="Legacy test", api_key=api_key)
    print("Legacy generate worked.")
except Exception as e:
    print(f"Legacy generate failed: {e}")
