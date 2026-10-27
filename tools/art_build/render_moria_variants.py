"""Moria dwarf variants preview (Blender 3.0 headless).

Renders the 10 look-iteration units from build_moria_variants into two sheets,
plus a close-up of the champion tiers. Review images land in previews/.

  blender --background --python tools/art_build/render_moria_variants.py
"""
import bpy
import os
import runpy
from mathutils import Euler

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "..", "tolkien"))
SOURCE_MOD = os.environ.get("ZEROAD_SOURCE_MOD")
if not SOURCE_MOD:
    raise RuntimeError("Set ZEROAD_SOURCE_MOD to the installed 0 A.D. public mod directory")
VAN = os.path.join(SOURCE_MOD, "art", "meshes")
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "previews"))
LEAN = Euler((0.0, 0.0, 0.0), "XYZ")

SKEL = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien")
PROPS = os.path.join(MOD, "art", "meshes", "props", "new")

VANILLA = {
    "pick": (VAN, "props/tool_pick.dae"),
    "hammer": (VAN, "props/tool_hammer.dae"),
    "mallet": (VAN, "props/prop_mallet.dae"),
    "axe": (VAN, "props/weap_axe_a.dae"),
    "axe2": (VAN, "props/weap_axe_c.dae"),
    "xiphos": (VAN, "props/weap_xiphos_d.dae"),
    "spear": (VAN, "props/weap_shaft_wood_a.dae"),
    "buckler_a": (VAN, "props/shield/pict_a_f.dae"),
    "buckler_c": (VAN, "props/shield/round_t_f.dae"),
}

# key for render_doriath weapon slot lambdas
WEAPON_OF = {
    "moria_civil_miner": "pick",
    "moria_civil_smith": "hammer",
    "moria_civil_guest": "mallet",
    "moria_levy_ovalax": "axe",
    "moria_levy_spear": "spear",
    "moria_reg_axe": "axe",
    "moria_reg_spearsteel": "spear",
    "moria_adv_shieldgold": "xiphos",
    "moria_adv_gildedaxe": "axe2",
    "moria_champ_full": "axe2",
}
SHIELD_OF = {
    "moria_levy_ovalax": "buckler_a",
    "moria_levy_spear": "buckler_c",
    "moria_reg_axe": "buckler_a",
    "moria_adv_shieldgold": "buckler_a",
}

HELM_PROPS = {
    "moria_reg_axe": ["erebor_helm.dae"],
    "moria_reg_spearsteel": ["erebor_helm.dae"],
    "moria_adv_shieldgold": ["erebor_helm.dae", "moria_crown.dae"],
    "moria_adv_gildedaxe": ["erebor_helm.dae"],
    "moria_champ_full": ["erebor_helm.dae", "moria_crown.dae",
                         "moria_horn_l.dae", "moria_horn_r.dae",
                         "moria_crest.dae"],
}


def main():
    base = runpy.run_path(os.path.join(HERE, "render_doriath.py"))
    base["MOD"] = MOD
    base["OUT"] = OUT
    base["clear"]()

    skel_tex = os.path.join(MOD, "art", "textures", "skins", "skeletal",
                            "tolkien")
    head_tex = os.path.join(MOD, "art", "textures", "skins", "props", "head")
    helm_tex = os.path.join(MOD, "art", "textures", "skins", "props",
                            "helmet")

    SPEC = [
        # (name, body, bodytex, beardtex, weapon, shield)
        ("moria_civil_miner", "tunic", "moria_leather_01.png", "erebor_face_a.png", "pick", None),
        ("moria_civil_smith", "tunic", "moria_cloth_01.png", "erebor_face_white.png", "hammer", None),
        ("moria_civil_guest", "tunic", "moria_cloth_red_01.png", "erebor_face_ginger.png", "mallet", None),
        ("moria_levy_ovalax", "pants", "moria_cloth_blue_01.png", "erebor_face_brown.png", "axe", "buckler_a"),
        ("moria_levy_spear", "pants", "moria_leather_01.png", "erebor_face_a.png", "spear", "buckler_c"),
        ("moria_reg_axe", "pants", "moria_iron_01.png", "erebor_face_brown.png", "axe", "buckler_a"),
        ("moria_reg_spearsteel", "pants", "moria_iron_02_steel.png", "erebor_face_ginger.png", "spear", None),
        ("moria_adv_shieldgold", "pants", "moria_iron_02_steel.png", "erebor_face_ginger.png", "xiphos", "buckler_a"),
        ("moria_adv_gildedaxe", "pants", "moria_gold_01.png", "erebor_face_white.png", "axe2", None),
        ("moria_champ_full", "pants", "moria_gold_01.png", "erebor_face_ginger.png", "axe2", None),
    ]

    def import_mesh(dae):
        before = set(bpy.data.objects)
        bpy.ops.wm.collada_import(filepath=dae)
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == "MESH"]
        for o in new:
            if o.type != "MESH":
                bpy.data.objects.remove(o, do_unlink=True)
        if len(meshes) != 1:
            raise SystemExit("expected 1 mesh in %s" % dae)
        return meshes[0]

    def place_unit(name, bodykey, tex, beartex, weapon, shield, x):
        before = set(bpy.data.objects)
        bpy.ops.wm.collada_import(filepath=os.path.join(
            SKEL, ("moria_dwarf_stout_pants.dae" if bodykey == "pants"
                   else "moria_dwarf_stout_tunic.dae")))
        new = [o for o in bpy.data.objects if o not in before]
        mesh = max((o for o in new if o.type == "MESH"),
                   key=lambda o: len(o.data.vertices))
        arms = [o for o in new if o.type == "ARMATURE"]
        arm = max(arms, key=lambda o: len(o.data.bones)) if arms else None
        base["set_tex"](mesh, os.path.join(skel_tex, tex))
        if arm:
            arm.location.x = x
            hb = arm.data.bones.get("head")
            hm = arm.data.bones.get("helmet")
            hb = hb.head_local if hb is not None else None
            hm = hm.head_local if hm is not None else None
            wr = arm.data.bones.get("weapon_R")
            sh = arm.data.bones.get("shield")
        else:
            hb = hm = None
        head = base["add_head"](mesh, os.path.join(PROPS, "erebor_head.dae"), x)
        base["set_tex"](head, os.path.join(head_tex, "erebor_face_a.png"))
        if hb is not None:
            head.location = (arm.location[0] + hb[0],
                             arm.location[1] + hb[1],
                             arm.location[2] + hb[2])
            head.rotation_euler = LEAN
        bb = set(bpy.data.objects)
        bpy.ops.wm.collada_import(filepath=os.path.join(PROPS, "erebor_beard.dae"))
        beard = next(o for o in bpy.data.objects
                     if o not in bb and o.type == "MESH")
        base["set_tex"](beard, os.path.join(head_tex, beartex))
        beard.location = (head.location[0], head.location[1],
                          head.location[2])
        beard.rotation_euler = head.rotation_euler
        if hm is not None and name in HELM_PROPS:
            for rel in HELM_PROPS[name]:
                hb2 = set(bpy.data.objects)
                bpy.ops.wm.collada_import(filepath=os.path.join(PROPS, rel))
                decoh = next(o for o in bpy.data.objects
                             if o not in hb2 and o.type == "MESH")
                if rel.startswith("erebor_helm"):
                    base["set_tex"](decoh, os.path.join(
                        helm_tex, "erebor_helm_gold.png" if "adv" in name
                        or "champ" in name else "erebor_helm.png"))
                elif rel == "moria_crown.dae":
                    base["set_tex"](decoh, os.path.join(helm_tex, "moria_crown.png"))
                elif rel.startswith("moria_horn"):
                    base["set_tex"](decoh, os.path.join(helm_tex, "moria_horn.png"))
                elif rel == "moria_crest.dae":
                    base["set_tex"](decoh, os.path.join(helm_tex, "moria_crest.png"))
                decoh.location = (arm.location[0] + hm[0],
                                  arm.location[1] + hm[1],
                                  arm.location[2] + hm[2])
                decoh.rotation_euler = head.rotation_euler
        wp = VANILLA[weapon]
        wmesh = import_mesh(os.path.join(wp[0], wp[1]))
        if wr is not None:
            wmesh.location = (arm.location[0] + wr.head_local[0],
                              arm.location[1] + wr.head_local[1],
                              arm.location[2] + wr.head_local[2])
            wmesh.rotation_euler = LEAN
        if shield and sh is not None:
            sp = VANILLA[shield]
            smesh = import_mesh(os.path.join(sp[0], sp[1]))
            smesh.location = (arm.location[0] + sh.head_local[0],
                              arm.location[1] + sh.head_local[1],
                              arm.location[2] + sh.head_local[2])
            smesh.rotation_euler = head.rotation_euler

    for i, (name, body, tex, beard, weapon, shield) in enumerate(SPEC):
        place_unit(name, body, tex, beard, weapon, shield, i * 3.2)
    log("units placed", len(SPEC))

    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    base["link"](cam)
    bpy.context.scene.camera = cam
    base["place"](cam, (14.4, -30, 5.2), rot=(87, 0, 0))
    cam_data.lens = 42
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy = 3.0
    sun = bpy.data.objects.new("sun", sun_d)
    base["link"](sun)
    base["place"](sun, (14.4, 0, 10), rot=(50, 0, 30))
    bpy.ops.mesh.primitive_plane_add(size=140, location=(14.4, 0, 0))
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
    sc.render.resolution_x = 2400
    sc.render.resolution_y = 760
    sc.render.filepath = os.path.join(OUT, "moria_variants_front.png")
    bpy.ops.render.render(write_still=True)
    base["place"](cam, (32, -36, 9.5), rot=(83, 0, 40))
    cam_data.lens = 38
    sc.render.filepath = os.path.join(OUT, "moria_variants_34.png")
    bpy.ops.render.render(write_still=True)

    # close-up detail: regular vs advanced vs champion
    cx = 18.0
    place_unit("moria_reg_axe", "pants", "moria_iron_01.png",
               "erebor_face_brown.png", "axe", "buckler_a", cx)
    place_unit("moria_adv_shieldgold", "pants", "moria_iron_02_steel.png",
               "erebor_face_ginger.png", "xiphos", "buckler_a", cx + 3.2)
    place_unit("moria_champ_full", "pants", "moria_gold_01.png",
               "erebor_face_ginger.png", "axe2", None, cx + 6.4)
    base["place"](cam, (cx + 3.2, -9.5, 3.4), rot=(87, 0, 0))
    cam_data.lens = 50
    sc.render.resolution_x = 1800
    sc.render.resolution_y = 800
    sc.render.filepath = os.path.join(OUT, "moria_variants_detail.png")
    bpy.ops.render.render(write_still=True)
    with open(os.path.join(OUT, "LINK.txt"), "w") as lf:
        pass
    print("MORIA VARIANT PREVIEWS DONE")


def log(*a):
    print("[moria-var-prev]", *a)


if __name__ == "__main__":
    main()
