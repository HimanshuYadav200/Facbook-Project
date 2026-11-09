import os
import sys

try:
    import moviepy.video.fx.all as vfx
    print(f"vfx dir: {dir(vfx)}")
    print(f"Has crop: {'crop' in dir(vfx)}")
except ImportError as e:
    print(f"Import failed: {e}")

try:
    from moviepy import vfx as vfx_top
    print(f"Top level vfx dir: {dir(vfx_top)}")
except ImportError:
    pass
