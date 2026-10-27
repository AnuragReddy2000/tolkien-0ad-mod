import struct, zlib, os

W = H = 16
# 16x16 RGBA: dark forest-green rounded square with a pale "closed eye" bar.
bg = (24, 42, 22, 255)
fg = (168, 208, 140, 255)
edge = (12, 22, 12, 255)

def rounded(x, y):
    for cx, cy in ((0, 0), (15, 0), (0, 15), (15, 15)):
        if (x - cx) ** 2 + (y - cy) ** 2 > 2.5:
            return False
    return True

rows = []
for y in range(H):
    row = bytearray()
    for x in range(W):
        if not rounded(x, y):
            row += bytes((0, 0, 0, 0))
        elif 7 <= y <= 8 and 3 <= x <= 12:
            row += bytes(fg)
        elif x in (0, 15) or y in (0, 15):
            row += bytes(edge)
        else:
            row += bytes(bg)
    rows.append(b"\x00" + bytes(row))

raw = b"".join(rows)

def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(raw, 9))
png += chunk(b"IEND", b"")

out = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tolkien", "art", "textures", "ui", "session", "icons",
    "status_effects", "concealed.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "wb") as f:
    f.write(png)
print("wrote", out, len(png), "bytes")
