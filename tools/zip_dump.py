import os, sys, zipfile, re

ZIP = os.environ.get("ZEROAD_PUBLIC_ZIP")

def dump(name):
    if not ZIP:
        raise RuntimeError("Set ZEROAD_PUBLIC_ZIP to the installed public.zip path")
    with zipfile.ZipFile(ZIP) as z:
        try:
            print(z.read(name).decode("utf-8", errors="replace"))
        except KeyError:
            print("NOT FOUND:", name)
    print("=" * 60)

if __name__ == "__main__":
    for n in sys.argv[1:]:
        print("### " + n)
        dump(n)
