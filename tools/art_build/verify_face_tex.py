import bpy
import os
import numpy as np

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
p = os.path.join(MOD, "art", "textures", "skins", "props", "head", "elf_face_a.png")
img = bpy.data.images.load(p)
w, h = img.size
arr = np.empty(w * h * 4, dtype=np.float32)
img.pixels.foreach_get(arr)
arr = arr.reshape(h, w, 4)
r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

def cls(px, py):
    R, G, B = arr[py, px, 0], arr[py, px, 1], arr[py, px, 2]
    lum = (R + G + B) / 3
    if lum < 0.12:
        return "H"          # hair (dark)
    if B > R * 1.05 and B > 0.4:
        return "E"          # eye (blue)
    if R > 0.5 and G < R * 0.8 and B < R * 0.8:
        return "L"          # lip (rose)
    if R > G > B and R > 0.4:
        return "S"          # skin
    return "."

G = 40
print(f"elf_face_a.png {w}x{h}  H=hair E=eye L=lip S=skin .=other  (top row = v high = top of head)")
for row in range(G):
    line = ""
    for col in range(G):
        py = int(row / G * h)
        px = int(col / G * w)
        line += cls(px, py)
    print(f"{row:2d} {line}")

# Quantitative: chin/beard zone = high u (>=0.55), low v (<0.12) -> should be SKIN not HAIR
def frac_in(u0, u1, v0, v1, want):
    x0 = int(u0 * w); x1 = int(u1 * w); y0 = int(v0 * h); y1 = int(v1 * h)
    cnt = {"H": 0, "S": 0, "E": 0, "L": 0, ".": 0}
    for py in range(y0, max(y1, y0 + 1)):
        for px in range(x0, max(x1, x0 + 1)):
            cnt[cls(px, py)] += 1
    tot = sum(cnt.values())
    return {k: round(v / tot, 2) for k, v in cnt.items()}

print("CHIN/BEARD zone (u>=0.55, v<0.12):", frac_in(0.55, 1.0, 0.0, 0.12, None))
print("MOUTH/MUSTACHE (u>=0.55, 0.24<v<0.34):", frac_in(0.55, 1.0, 0.24, 0.34, None))
print("EYE band (u>=0.55, 0.62<v<0.74):", frac_in(0.55, 1.0, 0.62, 0.74, None))
print("SCALP (v>0.86):", frac_in(0.0, 1.0, 0.86, 1.0, None))
