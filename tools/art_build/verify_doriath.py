import bpy
import os
import numpy as np

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "previews"))

def clusters(profile, thresh=3, gap=25):
    idx = np.where(profile > thresh)[0]
    if len(idx) == 0:
        return []
    groups = []
    start = idx[0]
    prev = idx[0]
    for i in idx[1:]:
        if i - prev > gap:
            groups.append((start, prev))
            start = i
        prev = i
    groups.append((start, prev))
    return [(int(a), int(b), (a + b) // 2) for a, b in groups]

def analyze(fname):
    p = os.path.join(OUT, fname)
    if not os.path.exists(p):
        print("MISSING", fname)
        return
    img = bpy.data.images.load(p)
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    arr = arr.reshape(h, w, 4)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    skin = (r > g * 1.08) & (g > b * 1.02) & (r > 0.40) & (r < 0.95)
    green = (g > r * 1.08) & (g > b * 1.08) & (g > 0.05) & (g < 0.6)
    anyc = skin | green
    prof = anyc.sum(axis=0)
    cl = clusters(prof)
    print(fname, "w=", w, "clusters(x0,x1,center):", cl)
    for (a, b, c) in cl:
        band = slice(a, b + 1)
        print("   center", c, "skin", int(skin[:, band].sum()), "green", int(green[:, band].sum()))

for f in ("doriath_units_front.png", "doriath_units_34.png"):
    analyze(f)
