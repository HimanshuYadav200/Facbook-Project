"""Blender test (2026-11-10): three short shots to compare with the Remotion draft. Not part of the engine yet.

Usage (from the project root):
  blender -b -P runs/strange-money/2026-11-10_eiffel-tower-sale/blender_test/blender_test.py -- <shot>
  <shot> = parallax | walker | beams
Writes PNG frames to blender_test/frames_<shot>/ (then ffmpeg makes the mp4).

  parallax: our AI background + green-keyed actors as flat cards at different depths; a real 3D camera arcs
            through them, so near things move more than far things (true depth, unlike a flat zoom).
  walker:   a real 3D cartoon character built from simple shapes (sphere head, capsule body, stick legs,
            top hat), walking and waving, in front of the AI background; the camera circles him.
  beams:    physics: rusty iron beams fall and crash into a pile (rigid bodies), camera pushes in.
"""
import math
import random
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
IMG = HERE.parent / "img"
FPS, W, H = 30, 1080, 1920


# ---------- scene basics ----------
def reset(frames):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x, s.render.resolution_y = W, H
    s.render.fps = FPS
    s.frame_start, s.frame_end = 1, frames
    s.view_settings.view_transform = "Standard"  # keep the AI images' colours as they are (AgX would wash them out)
    s.eevee.taa_render_samples = 32
    s.render.image_settings.file_format = "PNG"
    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (1.0, 0.85, 0.7, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    s.world = world
    return s


def camera(fov_deg=40):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle = math.radians(fov_deg)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def look_at(obj, target):
    d = (target[0] - obj.location.x, target[1] - obj.location.y, target[2] - obj.location.z)
    from mathutils import Vector
    obj.rotation_euler = Vector(d).to_track_quat("-Z", "Y").to_euler()


def key(obj, frame, loc=None, rot=None):
    if loc is not None:
        obj.location = loc
        obj.keyframe_insert("location", frame=frame)
    if rot is not None:
        obj.rotation_euler = rot
        obj.keyframe_insert("rotation_euler", frame=frame)


def mat_color(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def image_card(path, height, location, name):
    """A flat card showing an image at its own colours (emission), transparent where the PNG is."""
    img = bpy.data.images.load(str(path))
    w, h = img.size
    bpy.ops.mesh.primitive_plane_add(size=1, location=location)
    card = bpy.context.object
    card.name = name
    card.scale = (height * w / h, height, 1)
    card.rotation_euler = (math.radians(90), 0, 0)  # stand up, facing -Y (towards the camera)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    emit = nt.nodes.new("ShaderNodeEmission")
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs["Color"], emit.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(emit.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    card.data.materials.append(m)
    return card


def sun(strength=3.0, angle=(50, 0, 30)):
    l = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    l.data.energy = strength
    l.data.color = (1.0, 0.9, 0.78)
    l.rotation_euler = tuple(math.radians(a) for a in angle)
    bpy.context.scene.collection.objects.link(l)
    return l


# ---------- shot 1: parallax ----------
def shot_parallax():
    s = reset(75)
    cam = camera(40)
    bg_dist = 30
    visible_h = 2 * bg_dist * math.tan(math.radians(20))
    image_card(IMG / "bg_paris_street.webp", visible_h * 1.8, (0, bg_dist, visible_h * 0.1), "bg")
    image_card(IMG / "g_lustig_point.png", 4.2, (-1.4, 9, -1.0), "lustig")
    image_card(IMG / "g_poisson_happy.png", 3.6, (1.8, 13, -1.1), "poisson")
    # Camera arcs from the left and pushes in: near Lustig slides across faster than far Poisson and the street.
    for f, x, y, z in [(1, -3.2, -2.0, 0.6), (75, 1.2, 1.5, 0.2)]:
        key(cam, f, loc=(x, y, z))
    tgt = (0, 11, 0.3)
    for f in (1, 75):
        s.frame_set(f)
        look_at(cam, tgt)
        cam.keyframe_insert("rotation_euler", frame=f)
    # Actors bob a little, like the Remotion idle.
    for name, amp in (("lustig", 0.12), ("poisson", 0.2)):
        o = bpy.data.objects[name]
        z0 = o.location.z
        for f in range(1, 76, 6):
            key(o, f, loc=(o.location.x, o.location.y, z0 + amp * abs(math.sin(f / 6))))


# ---------- shot 2: walker ----------
def part(kind, name, mat, **kw):
    getattr(bpy.ops.mesh, f"primitive_{kind}_add")(**kw)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def attach(child, parent):
    """Parent without moving: Blender would otherwise read the child's position relative to the parent."""
    bpy.context.view_layer.update()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


def build_lustig():
    """Our Lustig in 3D: cream sphere head, dot eyes, black moustache, top hat, navy capsule body, stick limbs."""
    cream, black = mat_color("cream", (0.93, 0.84, 0.70), 0.5), mat_color("black", (0.02, 0.02, 0.02), 0.3)
    navy, red = mat_color("navy", (0.05, 0.08, 0.22), 0.7), mat_color("red", (0.6, 0.04, 0.04))
    root = bpy.data.objects.new("lustig", None)
    bpy.context.scene.collection.objects.link(root)
    body = part("uv_sphere", "body", navy, radius=0.45, location=(0, 0, 1.0))
    body.scale = (1, 0.8, 1.35)
    head = part("uv_sphere", "head", cream, radius=0.55, location=(0, 0, 2.15))
    for x in (-0.18, 0.18):
        attach(part("uv_sphere", "eye", black, radius=0.06, location=(x, -0.5, 2.25)), head)
        m = part("uv_sphere", "stache", black, radius=0.12, location=(x * 0.9, -0.5, 1.98))
        m.scale = (1.4, 0.4, 0.35)
        attach(m, head)
    attach(part("cylinder", "brim", black, radius=0.55, depth=0.05, location=(0, 0, 2.62)), head)
    attach(part("cylinder", "hat", black, radius=0.36, depth=0.7, location=(0, 0, 2.98)), head)
    tie = part("cube", "tie", red, size=0.12, location=(0, -0.42, 1.4))
    tie.scale = (0.7, 0.3, 2.2)
    attach(tie, body)
    limbs = {}
    for side, x in (("L", -0.2), ("R", 0.2)):
        # Legs and arms pivot at the top (origin moved there), so a rotation swings them.
        leg = part("cylinder", f"leg{side}", black, radius=0.05, depth=0.9, location=(x, 0, 0.45))
        arm = part("cylinder", f"arm{side}", navy, radius=0.07, depth=0.75, location=(x * 2.7, 0, 1.15))
        for o, top in ((leg, 0.9), (arm, 1.52)):
            bpy.context.scene.cursor.location = (o.location.x, 0, top)
            bpy.ops.object.select_all(action="DESELECT")
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        # Shoes and hands are added after the pivot moved, so they stay where they are drawn.
        shoe = part("uv_sphere", f"shoe{side}", black, radius=0.12, location=(x, -0.08, 0.02))
        shoe.scale = (1, 1.6, 0.6)
        attach(shoe, leg)
        attach(part("uv_sphere", f"hand{side}", cream, radius=0.1, location=(x * 2.7, 0, 0.78)), arm)
        limbs[f"leg{side}"], limbs[f"arm{side}"] = leg, arm
    for o in (body, head, *limbs.values()):
        attach(o, root)
    return root, body, head, limbs


def shot_walker():
    s = reset(75)
    cam = camera(38)
    sun(3.5)
    bg_dist = 40
    vis = 2 * bg_dist * math.tan(math.radians(19))
    image_card(IMG / "bg_paris_street.webp", vis * 1.9, (0, bg_dist, vis * 0.3), "bg")
    ground = part("plane", "ground", mat_color("cobble", (0.42, 0.30, 0.22), 0.9), size=60, location=(0, 10, 0))
    root, body, head, limbs = build_lustig()
    # Walk towards the camera; legs swing, arms swing opposite, body bobs, head tilts. The right arm waves at the end.
    for f in range(1, 76):
        t = f / FPS
        ph = t * 2 * math.pi * 1.6
        root.location = (0, 6 - 1.2 * t, 0.06 * abs(math.sin(ph)))
        root.keyframe_insert("location", frame=f)
        limbs["legL"].rotation_euler = (0.5 * math.sin(ph), 0, 0)
        limbs["legR"].rotation_euler = (-0.5 * math.sin(ph), 0, 0)
        limbs["armL"].rotation_euler = (-0.45 * math.sin(ph), 0, 0)
        wave = min(1, max(0, (f - 40) / 10))
        limbs["armR"].rotation_euler = ((1 - wave) * 0.45 * math.sin(ph), 0, -wave * (2.4 + 0.35 * math.sin(t * 14)))
        head.rotation_euler = (0, 0.12 * math.sin(ph / 2), 0)
        for o in (limbs["legL"], limbs["legR"], limbs["armL"], limbs["armR"], head):
            o.keyframe_insert("rotation_euler", frame=f)
    # Camera: low angle, circles from his left to his right while he walks.
    for f in range(1, 76, 4):
        a = math.radians(-35 + 70 * (f - 1) / 74)
        cy = 6 - 1.2 * f / FPS
        key(cam, f, loc=(7.5 * math.sin(a), cy - 7.5 * math.cos(a), 1.0))
        look_at(cam, (0, cy, 1.6))
        cam.keyframe_insert("rotation_euler", frame=f)


# ---------- shot 3: beams ----------
def shot_beams():
    s = reset(75)
    cam = camera(45)
    sun(4.0, (40, 10, -40))
    bg_dist = 45
    vis = 2 * bg_dist * math.tan(math.radians(22.5))
    # Only the beams are rendered (transparent film); the ground is an invisible "holdout" they land on.
    # The video is then laid over an AI picture, so Blender adds 3D motion without having to match the art.
    s.render.film_transparent = True
    ground = part("plane", "ground", mat_color("dirt", (0.35, 0.25, 0.18), 0.95), size=80, location=(0, 10, 0))
    ground.is_holdout = True
    bpy.ops.rigidbody.world_add()
    bpy.context.scene.rigidbody_world.point_cache.frame_end = 75
    s.frame_end = 75
    bpy.ops.object.select_all(action="DESELECT")
    ground.select_set(True)
    bpy.context.view_layer.objects.active = ground
    bpy.ops.rigidbody.object_add(type="PASSIVE")
    rust = mat_color("rust", (0.45, 0.17, 0.06), 0.85)
    rnd = random.Random(7)
    for i in range(22):
        b = part("cube", f"beam{i}", rust, size=1, location=(rnd.uniform(-1.8, 1.8), rnd.uniform(6.5, 9.5), 5 + i * 0.75 + rnd.uniform(0, 0.3)))  # 1.6 apart: overlapping bodies explode apart
        b.scale = (rnd.uniform(2.2, 3.6), 0.28, 0.28)
        b.rotation_euler = (0, rnd.uniform(-0.12, 0.12), rnd.uniform(0, math.pi))  # nearly flat: stacked bodies never overlap
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)  # location/rotation default to True too, which moved the centre to 0,0,0
        bpy.ops.rigidbody.object_add(type="ACTIVE")
        b.rigid_body.mass = 5
        b.rigid_body.restitution = 0.2
    # Without a GUI the physics only runs when baked ahead of time (frame by frame from the start).
    bpy.ops.ptcache.bake_all(bake=True)
    for f, y, z in [(1, -2, 4.0), (75, 1.5, 3.0)]:
        key(cam, f, loc=(0, y, z))
        look_at(cam, (0, 8, 2.0))
        cam.keyframe_insert("rotation_euler", frame=f)


SHOTS = {"parallax": shot_parallax, "walker": shot_walker, "beams": shot_beams}

if __name__ == "__main__":
    name = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "parallax"
    SHOTS[name]()
    out = HERE / f"frames_{name}"
    out.mkdir(exist_ok=True)
    bpy.context.scene.render.filepath = str(out / "f_")
    bpy.ops.render.render(animation=True)
