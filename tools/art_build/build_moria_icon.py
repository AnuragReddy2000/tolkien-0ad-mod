"""
Composite building icons (Blender 3.0 headless, numpy only - no scene needed).

Moria shaft: stock storehouse portrait + stone badge (bottom-left) +
metal badge (bottom-right) + white sparkle glints.

USAGE:
  blender --background --python tools\\art_build\\build_moria_icon.py
"""
import bpy
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "..", "tolkien"))
SRC = os.environ.get("MORIA_ICON_SOURCE_DIR")
if not SRC:
    raise RuntimeError("Set MORIA_ICON_SOURCE_DIR to the directory containing the source icon")


def log(*a):
    print("[moria-icon]", *a)


def load_rgba(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    bpy.data.images.remove(img)
    return arr.reshape(h, w, 4)[..., :3]


def resize_nearest(arr, out_h, out_w):
    h, w = arr.shape[:2]
    ys = (np.arange(out_h) * h // out_h).clip(0, h - 1)
    xs = (np.arange(out_w) * w // out_w).clip(0, w - 1)
    return arr[np.ix_(ys, xs)]


def paste(canvas, sprite, top, left, alpha=1.0):
    """Alpha-free overlay: sprite has black background; use luma as mask."""
    sh, sw = sprite.shape[:2]
    H, W = canvas.shape[:2]
    bottom, right = min(top + sh, H), min(left + sw, W)
    top_c, left_c = max(top, 0), max(left, 0)
    if bottom <= top_c or right <= left_c:
        return
    region = canvas[top_c:bottom, left_c:right]
    sp = sprite[(top_c - top):(bottom - top), (left_c - left):(right - left)]
    mask = np.clip(sp.max(axis=-1, keepdims=True) * 3.0, 0, 1) * alpha
    canvas[top_c:bottom, left_c:right] = region * (1 - mask) + sp * mask


def disc(canvas, cy, cx, r, color):
    H, W = canvas.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    m = ((yy - cy) ** 2 + (xx - cx) ** 2) <= r * r
    canvas[m] = np.array(color, dtype=np.float32)


def sparkle(canvas, cy, cx, r, strength=0.9):
    H, W = canvas.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dy, dx = np.abs(yy - cy), np.abs(xx - cx)
    arm = np.maximum(0, 1 - dx / (r * 2.5)) * (dy < max(r * 0.35, 1.0))
    arm += np.maximum(0, 1 - dy / (r * 2.5)) * (dx < max(r * 0.35, 1.0))
    core = np.maximum(0, 1 - np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2) / r)
    glow = np.clip(arm * 0.7 + core, 0, 1) * strength
    canvas += glow[..., None] * np.array([1.0, 1.0, 1.0], dtype=np.float32)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    base = load_rgba(os.path.join(SRC, "storehouse.png"))
    H, W = base.shape[:2]
    log(f"base {W}x{H}")
    stone = load_rgba(os.path.join(SRC, "stone.png"))
    metal = load_rgba(os.path.join(SRC, "metal.png"))
    bs = max(H // 3, 24)  # badge size (large read at menu size)
    stone = resize_nearest(stone, bs, bs)
    metal = resize_nearest(metal, bs, bs)
    # dark backing discs for readability
    disc(base, H - bs // 2 - 4, bs // 2 + 4, int(bs * 0.62), (0.05, 0.05, 0.06))
    disc(base, H - bs // 2 - 4, W - bs // 2 - 4, int(bs * 0.62),
         (0.05, 0.05, 0.06))
    paste(base, stone, H - bs - 4, 4)
    paste(base, metal, H - bs - 4, W - bs - 4)
    # sparkle glints: above badges + top corners
    sparkle(base, H - bs - 10, 4 + bs // 2, 7)
    sparkle(base, H - bs - 10, W - 4 - bs // 2, 7)
    sparkle(base, 10, 10, 6, 0.7)
    sparkle(base, 14, W - 10, 5, 0.6)
    np.clip(base, 0, 1, out=base)
    outdir = os.path.join(MOD, "art", "textures", "ui", "session",
                          "portraits", "structures")
    os.makedirs(outdir, exist_ok=True)
    outp = os.path.join(outdir, "moria_mithril_shaft.png")
    img = bpy.data.images.new("shaft_icon", W, H)
    rgba = np.ones((H, W, 4), dtype=np.float32)
    rgba[..., :3] = base
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = outp
    img.file_format = "PNG"
    img.save()
    log(f"WROTE {outp} {W}x{H}")
    with open(os.path.join(outdir, "moria_icons_CREDITS.txt"), "w",
              encoding="utf-8") as f:
        f.write("Moria shaft icon: composite of 0 A.D. public portraits/icons "
                "(CC-BY-SA, Wildfire Games): storehouse.png portrait + "
                "stone/metal resource badges + procedural sparkle.\n")


if __name__ == "__main__":
    main()
