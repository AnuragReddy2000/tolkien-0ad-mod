"""Scale translation components of matrix-keyframed Collada animations.

Used to shrink vanilla ambient carrion loops (e.g. the 27 m circling flock in
others/bird_circle_idle_01.dae) down to unit scale. Only matrix OUTPUT
sampler arrays are touched (rotation blocks stay bit-identical); time and
interpolation arrays are never modified.

Usage:
  py tools/art_build/scale_anim_translations.py <src.dae> <dst.dae> <factor>
"""

import sys
import xml.etree.ElementTree as ET


def main(src, dst, factor):
    factor = float(factor)
    ET.register_namespace("", "http://www.collada.org/2005/11/COLLADASchema")
    tree = ET.parse(src)
    root = tree.getroot()

    def strip(tag):
        return tag.split("}")[-1]

    # Sampler id -> OUTPUT source id.
    samp_out = {}
    for el in root.iter():
        if strip(el.tag) == "sampler":
            for inp in el:
                if strip(inp.tag) == "input" and inp.get("semantic") == "OUTPUT":
                    samp_out[el.get("id")] = inp.get("source").lstrip("#")

    # Source id -> float_array element.
    src_arr = {}
    for el in root.iter():
        if strip(el.tag) == "source":
            for fa in el:
                if strip(fa.tag) == "float_array":
                    src_arr[el.get("id")] = fa

    # Sanity: every OUTPUT source must be a whole-matrix array.
    for sid, src_id in samp_out.items():
        vals = list(map(float, src_arr[src_id].text.split()))
        if len(vals) % 16 != 0:
            raise SystemExit("non-matrix OUTPUT array: %s (%d floats)"
                             % (src_id, len(vals)))

    changed = 0
    for sid, src_id in sorted(samp_out.items()):
        fa = src_arr[src_id]
        vals = list(map(float, fa.text.split()))
        # Translation row of each 4x4 key (matches the vanilla exporter's
        # matrix layout, verified against bird_circle_idle_01.dae).
        for i in range(0, len(vals), 16):
            vals[i + 3] *= factor
            vals[i + 7] *= factor
            vals[i + 11] *= factor
        fa.text = " ".join(repr(v) for v in vals)
        changed += 1

    with open(dst, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True)
    print("scaled %d sampler outputs by %s -> %s" % (changed, factor, dst))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
