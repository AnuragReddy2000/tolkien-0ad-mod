"""POC preview: stock human vs stout dwarf + helm (Blender 3.0 headless)."""
import bpy
import math
import os
import runpy
from mathutils import Euler

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "..", "tolkien"))
REF = os.environ.get("ZEROAD_REFERENCE_ART")
if not REF:
    raise RuntimeError("Set ZEROAD_REFERENCE_ART to the extracted 0 A.D. public art directory")
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "previews"))


def main():
    base = runpy.run_path(os.path.join(HERE, "render_doriath.py"))
    base["MOD"] = MOD
    base["OUT"] = OUT
    base["clear"]()

    iron_tex = os.path.join(MOD, "art", "textures", "skins", "skeletal",
                            "tolkien", "erebor_iron_01.png")
    head_dae = os.path.join(MOD, "art", "meshes", "props", "new",
                            "erebor_head.dae")
    beard_dae = os.path.join(MOD, "art", "meshes", "props", "new",
                             "erebor_beard.dae")
    helm_dae = os.path.join(MOD, "art", "meshes", "props", "new",
                            "erebor_helm.dae")
    helm_tex = os.path.join(MOD, "art", "textures", "skins", "props",
                            "helmet", "erebor_helm.png")
    if not os.path.isfile(helm_tex):
        helm_tex = iron_tex
    face = os.path.join(MOD, "art", "textures", "skins", "props", "head",
                        "erebor_face_a.png")
    stout = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien",
                         "erebor_dwarf_stout.dae")

    # x=0: stock human (reference)
    body, arm, _ = base["import_body"](
        "meshes_skeletal_new_m_armor_tunic_short.dae")
    base["set_tex"](body, iron_tex)
    if arm:
        arm.location.x = 0
    head = base["add_head"](body, head_dae, 0)
    base["set_tex"](head, face)

    # x=3.2: POC dwarf (stout body + beard + helm)
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=stout)
    new = [o for o in bpy.data.objects if o not in before]
    dmesh = max((o for o in new if o.type == "MESH"),
                key=lambda o: len(o.data.vertices))
    darms = [o for o in new if o.type == "ARMATURE"]
    darm = max(darms, key=lambda o: len(o.data.bones)) if darms else None
    base["set_tex"](dmesh, iron_tex)
    if darm:
        darm.location.x = 3.2
    # head+beard seated on the stout neck opening
    # head+beard seated BY BONE (engine truth: props anchor at bone
    # positions, not geometry - geometry seating sits 0.07 forward here
    # and misjudges the helm). Same 8-degree lean on all three.
    from mathutils import Euler
    import math as _m
    dhead = base["add_head"](dmesh, head_dae, 3.2)
    base["set_tex"](dhead, face)
    if darm is not None and "head" in darm.data.bones:
        hh = darm.data.bones["head"].head_local
        dhead.location = (darm.location[0] + hh[0],
                          darm.location[1] + hh[1],
                          darm.location[2] + hh[2])
    dhead.rotation_euler = Euler((_m.radians(8), 0, 0), "XYZ")
    # beard prop (actor lists head + beard + helm: guard rides over beard)
    bbefore = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=beard_dae)
    beard = next(o for o in bpy.data.objects
                 if o not in bbefore and o.type == "MESH")
    base["set_tex"](beard, face)
    # copy head transform (beard rides with head on the head bone in-game)
    beard.location = (dhead.location[0], dhead.location[1],
                      dhead.location[2])
    beard.rotation_euler = dhead.rotation_euler
    # helm: seated exactly where the engine puts it - prop origin goes to
    # the HELMET bone (helmet bone head in armature local + arm offset).
    # Same 8-degree forward lean as the head so they agree visually.
    hbefore = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=helm_dae)
    helm = next(o for o in bpy.data.objects
                if o not in hbefore and o.type == "MESH")
    base["set_tex"](helm, helm_tex)
    if darm is not None and "helmet" in darm.data.bones:
        hb = darm.data.bones["helmet"].head_local
        helm.location = (darm.location[0] + hb[0],
                         darm.location[1] + hb[1],
                         darm.location[2] + hb[2])
        print("[poc-xsec] helm placed via helmet bone + arm offset")
    else:  # fallback: stout build values
        helm.location = (dhead.location[0], dhead.location[1] + 0.02,
                         dhead.location[2] - 0.06)
        print("[poc-xsec] helm placed via head fallback")
    helm.rotation_euler = dhead.rotation_euler
    print("[poc-xsec] dhead loc=%s rot=%s" % (
        tuple(round(v, 3) for v in dhead.location),
        tuple(round(v, 3) for v in dhead.rotation_euler)))
    # deep debug: why does the helm measure 0.38 low?
    bpy.context.view_layer.update()
    print("[poc-xsec] helm loc=%s rot=%s parent=%s" % (
        tuple(round(v, 3) for v in helm.location),
        tuple(round(v, 3) for v in helm.rotation_euler),
        helm.parent.name if helm.parent else None))
    print("[poc-xsec] darm loc=%s hb=%s" % (
        tuple(round(v, 3) for v in darm.location),
        tuple(round(v, 3) for v in darm.data.bones["helmet"].head_local)))
    print("[poc-xsec] helm matrix_world=%s" % (
        tuple(round(v, 3) for v in helm.matrix_world.translation),))
    hx = [v.co.x for v in helm.data.vertices]
    hy = [v.co.y for v in helm.data.vertices]
    hz = [v.co.z for v in helm.data.vertices]
    print("[poc-xsec] helm LOCAL X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f] n=%d" % (
        min(hx), max(hx), min(hy), max(hy), min(hz), max(hz),
        len(helm.data.vertices)))
    # numeric placement check (AFTER placement): helm vs head vs body
    bpy.context.view_layer.update()
    for label, o in (("helm", helm), ("dhead", dhead), ("dmesh", dmesh)):
        ws = [o.matrix_world @ v.co for v in o.data.vertices]
        print("[poc-xsec] %s X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (
            label, min(p[0] for p in ws), max(p[0] for p in ws),
            min(p[1] for p in ws), max(p[1] for p in ws),
            min(p[2] for p in ws), max(p[2] for p in ws)))

    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    base["link"](cam)
    bpy.context.scene.camera = cam
    base["place"](cam, (1.6, -14, 3.6), rot=(87, 0, 0))
    cam_data.lens = 50
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy = 3.0
    sun = bpy.data.objects.new("sun", sun_d)
    base["link"](sun)
    base["place"](sun, (0, 0, 10), rot=(50, 0, 30))
    bpy.ops.mesh.primitive_plane_add(size=60, location=(1.6, 0, 0))
    gnd = bpy.context.active_object
    gm = bpy.data.materials.new("gnd")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs[
        "Base Color"].default_value = (0.05, 0.05, 0.05, 1)
    gnd.data.materials.append(gm)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = 1280
    sc.render.resolution_y = 720
    sc.render.filepath = os.path.join(OUT, "erebor_poc_front.png")
    bpy.ops.render.render(write_still=True)
    base["place"](cam, (9, -11, 5.0), rot=(83, 0, 40))
    sc.render.filepath = os.path.join(OUT, "erebor_poc_34.png")
    bpy.ops.render.render(write_still=True)
    # helm close-up on the dwarf (head at x=3.2, z~3.0)
    base["place"](cam, (3.2, -3.4, 3.3), rot=(90, 0, 0))
    cam_data.lens = 85
    sc.render.filepath = os.path.join(OUT, "erebor_poc_helm_closeup.png")
    bpy.ops.render.render(write_still=True)
    print("POC RENDERS DONE")


if __name__ == "__main__":
    main()
