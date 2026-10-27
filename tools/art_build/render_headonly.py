import bpy
import os
import numpy as np
from mathutils import Euler
import math

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "previews"))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.collada_import(filepath=os.path.join(MOD, "art", "meshes", "props", "new", "elf_head.dae"))
head = next(o for o in bpy.data.objects if o.type == "MESH")
# texture
mat = bpy.data.materials.new("m"); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(
    os.path.join(MOD, "art", "textures", "skins", "props", "head", "elf_face_a.png"))
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
head.data.materials.clear(); head.data.materials.append(mat)
# face is +Y; put camera in front (-Y) looking toward +Y
head.location = (0, 0, 0)
cam_d = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cam_d)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (0, 3.0, 0.25)
cam.rotation_euler = Euler((math.radians(-90), 0, 0), "XYZ")
cam_d.lens = 60
sun = bpy.data.lights.new("s", "SUN"); sun.energy = 4
so = bpy.data.objects.new("s", sun); bpy.context.collection.objects.link(so)
so.rotation_euler = Euler((math.radians(60), 0, 0), "XYZ")
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "FLAT"; sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x = 600; sc.render.resolution_y = 600
sc.render.filepath = os.path.join(OUT, "_headonly.png")
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(os.path.join(OUT, "_headonly.png"))
w, h = img.size
a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a); a = a.reshape(h, w, 4)
G = 24
print("head-only map (top=y0): P=pale H=brown .=other")
for ry in range(G):
    line = ""
    for rx in range(G):
        y0 = int(ry * h / G); y1 = max(int((ry + 1) * h / G), y0 + 1)
        x0 = int(rx * w / G); x1 = max(int((rx + 1) * w / G), x0 + 1)
        blk = a[y0:y1, x0:x1, :3].reshape(-1, 3)
        R, G_, B = blk[:, 0].mean(), blk[:, 1].mean(), blk[:, 2].mean()
        if R > 0.6 and G_ > 0.5 and B > 0.42 and abs(R - B) < 0.2: ch = "P"
        elif R > G_ * 1.12 and G_ > B * 1.03 and R < 0.6: ch = "H"
        else: ch = "."
        line += ch
    print(line)
