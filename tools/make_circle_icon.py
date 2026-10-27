import struct, zlib, os, sys, math

# Generates a plain white radial disc with a soft edge on transparency,
# mirroring vanilla's background_circle_<civ>.png minimap-flare backdrops
# (the engine tints it with the player colour).
W = H = 64
CX = CY = 31.5
R_OUT = 30.0
R_IN = 26.0

rows = []
for y in range(H):
    row = bytearray()
    for x in range(W):
        d = math.hypot(x - CX, y - CY)
        if d >= R_OUT:
            row += bytes((0, 0, 0, 0))
        elif d <= R_IN:
            row += bytes((235, 235, 235, 255))
        else:
            a = int(255 * (R_OUT - d) / (R_OUT - R_IN))
            row += bytes((235, 235, 235, a))
    rows.append(b"\x00" + bytes(row))

raw = b"".join(rows)

def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(raw, 9))
png += chunk(b"IEND", b"")

outdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tolkien", "art", "textures", "ui", "session", "icons", "bkg")
os.makedirs(outdir, exist_ok=True)
for civ in sys.argv[1:] or ("doriath", "lindon", "tolkien_test"):
    out = os.path.join(outdir, f"background_circle_{civ}.png")
    with open(out, "wb") as f:
        f.write(png)
    print("wrote", out, len(png), "bytes")
