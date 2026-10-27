import os, sys, zipfile, re

ZIP = os.environ.get("ZEROAD_PUBLIC_ZIP")
if not ZIP:
    raise RuntimeError("Set ZEROAD_PUBLIC_ZIP to the installed public.zip path")

pattern = sys.argv[1]
path_filter = sys.argv[2] if len(sys.argv) > 2 else r"\.js$"
rx = re.compile(pattern)
pf = re.compile(path_filter)

with zipfile.ZipFile(ZIP) as z:
    for n in z.namelist():
        if not pf.search(n) or ".cached" in n:
            continue
        if not (n.startswith("simulation/") or n.startswith("globalscripts/") or n.startswith("gui/")):
            continue
        data = z.read(n).decode("utf-8", errors="replace")
        for i, line in enumerate(data.splitlines(), 1):
            if rx.search(line):
                print(f"{n}:{i}: {line.strip()[:200]}")
