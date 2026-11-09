from moviepy import vfx, ImageClip, ColorClip

print("vfx dir:", dir(vfx))

try:
    print("Type of Resize:", type(vfx.Resize))
    # Try to instantiate
    res = vfx.Resize(width=100)
    print("Instantiated Resize:", res)
    
    clip = ColorClip(size=(1000, 1000), color=(255,0,0), duration=1)
    
    # Try applying
    # new_clip = clip.with_effects([res])  <-- common v2 syntax
    if hasattr(clip, 'with_effects'):
        print("Clip has with_effects")
        new_clip = clip.with_effects([vfx.Resize(width=100)])
        print("Resize applied via with_effects. New size:", new_clip.size)
    else:
        print("Clip does NOT have with_effects")

except Exception as e:
    print("Resize experimentation failed:", e)

try:
    # Try Crop
    crop = vfx.Crop(x1=0, y1=0, width=100, height=100)
    print("Instantiated Crop:", crop)
except Exception as e:
    print("Crop failed:", e)
