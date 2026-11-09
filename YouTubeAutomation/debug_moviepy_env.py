
import os
import sys

print("Python:", sys.version)
try:
    import moviepy
    print("MoviePy Version:", moviepy.__version__)
except:
    print("MoviePy version check failed")

IS_MOVIEPY_2 = False
try:
    from moviepy.editor import *
    print("Imported from moviepy.editor (v1 style)")
except ImportError:
    IS_MOVIEPY_2 = True
    print("Failed to import moviepy.editor, trying top-level (v2 style)")
    try:
        from moviepy import *
    except ImportError as e:
        print("Failed to import moviepy:", e)

print(f"IS_MOVIEPY_2 detected as: {IS_MOVIEPY_2}")

try:
    img = ImageClip
    print("ImageClip found:", img)
    print("Has set_duration:", hasattr(img, 'set_duration'))
    print("Has with_duration:", hasattr(img, 'with_duration'))
    
    # Create a dummy image to test instance methods
    # We can't easily create one without a file, so we skip instantiation test
    # unless we mock it or use a solid color (ColorClip)
    
except NameError:
    print("ImageClip not found in namespace")

