"""Render the rigged Ent as a 256px unit portrait (transparent PNG).

Usage (headless):
  blender --background --python tools/art_build/render_ent_portrait.py
Output (overwrites the programmer-art placeholders):
  tolkien/art/textures/ui/session/icons/units/doriath/siege_ent.png
  tolkien/art/textures/ui/session/portraits/units/doriath/siege_ent.png
"""
import bpy
import os
import math

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))

bpy.ops.wm.read_factory_settings(use_empty=True)

# import rigged ent (mesh + Biped armature)
before = set(bpy.data.objects)
bpy.ops.wm.collada_import(
    filepath=os.path.join(MOD, "art", "meshes", "skeletal", "tolkien", "ent.dae"))
new_objs = [o for o in bpy.data.objects if o not in before]
mesh = next(o for o in new_objs if o.type == "MESH")
print("[ent-portrait] mesh:", mesh.name, "verts:", len(mesh.data.vertices))

# texture: fresh material with the bark albedo (same pattern as render_*.py)
texpath = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "ent_body.png")
mat = bpy.data.materials.new("ent_portrait_m")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes.get("Principled BSDF")
texnode = nt.nodes.new("ShaderNodeTexImage")
texnode.image = bpy.data.images.load(texpath)
nt.links.new(texnode.outputs["Color"], bsdf.inputs["Base Color"])
mesh.data.materials.clear()
mesh.data.materials.append(mat)
for p in mesh.data.polygons:
    p.material_index = 0

# frame: mesh ~7.7 tall, feet at z=0, centered XY
bpy.context.view_layer.update()
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
zmax, zmin = max(zs), min(zs)
print("[ent-portrait] bounds z: %.2f .. %.2f" % (zmin, zmax))
target = (0.0, 0.0, (zmax + zmin) * 0.52)

# camera: 3/4 view
sc = bpy.context.scene
cam_d = bpy.data.cameras.new("portrait_cam")
cam_d.lens = 50
cam = bpy.data.objects.new("portrait_cam", cam_d)
bpy.context.collection.objects.link(cam)
sc.camera = cam
cam.location = (7.5, -8.5, target[2] + 2.1)
trk = cam.constraints.new("TRACK_TO")
trkc = bpy.data.objects.new("portrait_target", None)
bpy.context.collection.objects.link(trkc)
trkc.location = target
trk.target = trkc
trk.track_axis = "TRACK_NEGATIVE_Z"
trk.up_axis = "UP_Y"

# lights: key sun + frontal fill + ambient world (world lights but stays invisible)
sun = bpy.data.lights.new("key", "SUN")
sun.energy = 5.0
suno = bpy.data.objects.new("key", sun)
bpy.context.collection.objects.link(suno)
suno.rotation_euler = (math.radians(50), 0, math.radians(-35))
fill = bpy.data.lights.new("fill", "SUN")
fill.energy = 2.0
fillo = bpy.data.objects.new("fill", fill)
bpy.context.collection.objects.link(fillo)
fillo.rotation_euler = (math.radians(30), 0, math.radians(215))
world = bpy.data.worlds.new("portrait_world")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.5
sc.world = world

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 256
sc.render.resolution_y = 256
sc.render.film_transparent = True
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
sc.eevee.taa_render_samples = 64

for sub in ("icons/units/doriath/siege_ent.png",
            "portraits/units/doriath/siege_ent.png"):
    out = os.path.join(MOD, "art", "textures", "ui", "session", *sub.split("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("[ent-portrait] wrote", out)
