import bpy
import math
import os
from mathutils import Vector, Euler

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
REF = os.environ.get("ZEROAD_REFERENCE_ART")
if not REF:
    raise RuntimeError("Set ZEROAD_REFERENCE_ART to the extracted 0 A.D. public art directory")
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "previews"))

def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def link(o):
    bpy.context.collection.objects.link(o)
    return o

def set_tex(obj, texpath):
    mat = bpy.data.materials.new(obj.name + "_m")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(texpath)
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    obj.data.materials.clear()
    obj.data.materials.append(mat)

def import_body(fname):
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=os.path.join(REF, fname))
    new = [o for o in bpy.data.objects if o not in before]
    mesh = next(o for o in new if o.type == "MESH")
    # prefer the armature the mesh is parented to (the one that actually has bones)
    arm = None
    if mesh.parent and mesh.parent.type == "ARMATURE":
        arm = mesh.parent
    else:
        arms = [o for o in new if o.type == "ARMATURE" and len(o.data.bones) > 0]
        arm = arms[0] if arms else None
    return mesh, arm, new

def place(obj, loc, rot=(0, 0, 0)):
    obj.location = loc
    obj.rotation_euler = Euler([math.radians(a) for a in rot], "XYZ")

def align_head_to_body(head, body, seat=0.02):
    # keep the head upright; match the body's neck-opening center to the head's neck-base center
    bpy.context.view_layer.update()
    bme = body.data
    bz = [ (body.matrix_world @ v.co).z for v in bme.vertices ]
    zmax = max(bz)
    neck = [body.matrix_world @ v.co for v, z in zip(bme.vertices, bz) if z > zmax - 0.28]
    bx = sum(p.x for p in neck) / len(neck)
    by = sum(p.y for p in neck) / len(neck)
    bz_ = sum(p.z for p in neck) / len(neck)
    hme = head.data
    hneck = [head.matrix_world @ v.co for v in hme.vertices if v.co.z < -0.05]
    hx = sum(p.x for p in hneck) / len(hneck)
    hy = sum(p.y for p in hneck) / len(hneck)
    hz = sum(p.z for p in hneck) / len(hneck)
    head.rotation_euler = Euler((math.radians(8), 0, 0), "XYZ")  # slight forward lean
    head.location = (bx - hx, by - hy + 0.02, bz_ - hz + seat)

def make_scimitar(name, mat_iron):
    # jagged single-edge blade from a scaled cube chain
    verts = []
    faces = []
    # blade profile in XZ plane, thickness in Y
    prof = [
        (0.00, 0.00), (0.02, 0.10), (0.03, 0.22), (0.02, 0.34),
        (0.05, 0.40), (0.01, 0.46), (-0.01, 0.34), (-0.01, 0.22),
        (-0.01, 0.10), (-0.01, 0.00),
    ]
    t = 0.012
    for (x, z) in prof:
        verts.append((x, -t, z))
        verts.append((x, t, z))
    n = len(prof)
    for i in range(n - 1):
        a, b = i * 2, (i + 1) * 2
        faces.append((a + 1, b + 1, b, a))
    faces.append(tuple(range(0, 2 * n, 2)))
    faces.append(tuple(reversed(range(1, 2 * n, 2))))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    link(ob)
    ob.data.materials.append(mat_iron)
    return ob

def make_spear(name, mat_shaft_wood, mat_iron):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=1.9, location=(0, 0, 0.95), vertices=8)
    shaft = bpy.context.active_object
    shaft.name = name + "_shaft"
    shaft.data.materials.append(mat_shaft_wood)
    bpy.ops.mesh.primitive_cone_add(radius1=0.045, radius2=0.0, depth=0.28, location=(0, 0, 2.0), vertices=6)
    blade = bpy.context.active_object
    blade.name = name + "_blade"
    blade.data.materials.append(mat_iron)
    return shaft, blade

def build_unit(body_file, head_file, weapon_builder, offset_x):
    body, arm, _ = import_body(body_file)
    # orc head
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=head_file)
    head = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
    set_tex(head, os.path.join(MOD, "art", "textures", "skins", "props", "head", "orc_face_a.png"))
    place(head, (offset_x, -0.144, 3.879))
    body.location.x = offset_x
    if arm:
        arm.location.x = offset_x
    weapon_builder(offset_x)
    return body

def main():
    clear()
    iron = bpy.data.materials.new("orc_iron")
    iron.use_nodes = True
    iron.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.10, 0.10, 0.12, 1)
    wood = bpy.data.materials.new("orc_wood")
    wood.use_nodes = True
    wood.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.10, 0.06, 1)

    head_dae = os.path.join(MOD, "art", "meshes", "props", "new", "orc_head.dae")

    # --- Warrior (x=0)
    body, arm, _ = import_body("meshes_skeletal_new_m_armor_tunic_short.dae")
    set_tex(body, os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "orc_leather_01.png"))
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=head_dae)
    head = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
    set_tex(head, os.path.join(MOD, "art", "textures", "skins", "props", "head", "orc_face_a.png"))
    align_head_to_body(head, body)
    sw = make_scimitar("orc_scim", iron)
    place(sw, (-0.84, -0.19, 2.16), rot=(0, 20, 0))

    # --- Spearman (x=3)
    body2, arm2, _ = import_body("meshes_skeletal_new_m_armor_pants_tunic_short.dae")
    set_tex(body2, os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "orc_iron_01.png"))
    if arm2:
        arm2.location.x = 3  # move only the armature; the mesh follows (avoids double-offset)
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=head_dae)
    head2 = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
    set_tex(head2, os.path.join(MOD, "art", "textures", "skins", "props", "head", "orc_face_a.png"))
    align_head_to_body(head2, body2)
    sh, bl = make_spear("orc_sp", wood, iron)
    sh.location = (2.2, -0.25, 0.95)
    bl.location = (2.2, -0.25, 2.0)

    # --- Archer (x=6)
    body3, arm3, _ = import_body("meshes_skeletal_new_m_tunic_short.dae")
    set_tex(body3, os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "orc_leather_01.png"))
    if arm3:
        arm3.location.x = 6  # move only the armature; the mesh follows (avoids double-offset)
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=head_dae)
    head3 = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
    set_tex(head3, os.path.join(MOD, "art", "textures", "skins", "props", "head", "orc_face_a.png"))
    align_head_to_body(head3, body3)
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=os.path.join(REF, "meshes_props_weapons_bow_greek.dae"))
    bow = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
    set_tex(bow, os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "orc_leather_01.png"))
    place(bow, (5.3, -0.1, 2.2), rot=(90, 0, 0))

    # world
    bpy.ops.object.select_all(action="DESELECT")
    # camera
    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    link(cam)
    bpy.context.scene.camera = cam
    place(cam, (3, -14, 4.5), rot=(87, 0, 0))
    cam_data.lens = 50

    # sun
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy = 3.0
    sun = bpy.data.objects.new("sun", sun_d)
    link(sun)
    place(sun, (0, 0, 10), rot=(50, 0, 30))

    # fill
    fill_d = bpy.data.lights.new("fill", "AREA")
    fill_d.energy = 500
    fill = bpy.data.objects.new("fill", fill_d)
    link(fill)
    place(fill, (3, -8, 6), rot=(75, 0, 0))

    # ground
    bpy.ops.mesh.primitive_plane_add(size=60, location=(3, 0, 0))
    gnd = bpy.context.active_object
    gm = bpy.data.materials.new("gnd")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.05, 0.055, 1)
    gnd.data.materials.append(gm)

    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = 1280
    sc.render.resolution_y = 720
    sc.render.filepath = os.path.join(OUT, "orc_units_front.png")
    bpy.ops.render.render(write_still=True)

    # 3/4 view
    place(cam, (11, -11, 5.5), rot=(83, 0, 40))
    sc.render.filepath = os.path.join(OUT, "orc_units_34.png")
    bpy.ops.render.render(write_still=True)

    # close-up on the middle (spearman) head: aim straight at the face
    place(cam, (3, -3.6, 4.0), rot=(90, 0, 0))
    cam_data.lens = 85
    sc.render.filepath = os.path.join(OUT, "orc_heads_closeup.png")
    bpy.ops.render.render(write_still=True)

    print("RENDERS DONE")

if __name__ == "__main__":
    main()
