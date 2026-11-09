
import os
try:
    from moviepy.editor import AudioFileClip
    print("Imported from moviepy.editor")
except ImportError:
    try:
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        print("Imported from moviepy.audio.io.AudioFileClip")
    except ImportError:
        print("Failed to import AudioFileClip")
        AudioFileClip = None

# Path to one of the generated files
audio_path = r"c:\Users\Himanshu Yadav\Downloads\Finance-Agent(long form)\YouTubeAutomation\assets\run_20260111_081251\audio_hook.mp3"

print(f"Checking file: {audio_path}")
print(f"Exists: {os.path.exists(audio_path)}")
print(f"Size: {os.path.getsize(audio_path)} bytes")

try:
    clip = AudioFileClip(audio_path)
    print(f"Duration: {clip.duration}")
    clip.close()
except Exception as e:
    print(f"Error: {e}")
