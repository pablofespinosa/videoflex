# Uso:  python release.py [patch|minor|major] "mensaje del commit"
import io, re, sys, subprocess

p = "VideoFlex_Q.py"
level = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("patch", "minor", "major") else "patch"
msg = sys.argv[2] if len(sys.argv) > 2 else "Mejoras varias"

src = io.open(p, encoding="utf-8").read()
m = re.search(r'(?m)^APP_VERSION\s*=\s*"(\d+)\.(\d+)\.(\d+)"', src)
if not m:
    print("?? No encuentro APP_VERSION"); sys.exit(1)
maj, mino, pat = map(int, m.groups())
if level == "major":
    maj += 1; mino = 0; pat = 0
elif level == "minor":
    mino += 1; pat = 0
else:
    pat += 1
newv = f"{maj}.{mino}.{pat}"
src = re.sub(r'(?m)^APP_VERSION\s*=\s*"\d+\.\d+\.\d+"', f'APP_VERSION = "{newv}"', src, count=1)
io.open(p, "w", encoding="utf-8").write(src)
print("Nueva version app:", newv)

for archivo, patron in [("README.md", r"Versión actual: \d+\.\d+\.\d+"),
                        ("LICENSE", r"\b\d+\.\d+\.\d+\b")]:
    try:
        txt = io.open(archivo, encoding="utf-8").read()
        txt2 = re.sub(patron, f"Versión actual: {newv}" if archivo == "README.md" else newv, txt)
        if txt2 != txt:
            io.open(archivo, "w", encoding="utf-8").write(txt2)
            print("OK", archivo, "sincronizado")
    except Exception as e:
        print(archivo, ":", e)

def run(*cmd):
    print(">", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.stdout.strip():
        print(r.stdout.strip()[:400])
    if r.returncode != 0:
        print("ERR:", r.stderr.strip()[:400])
    return r.returncode == 0

ok = run("git", "add", "VideoFlex_Q.py", "README.md", "LICENSE", "release.py")
ok = run("git", "commit", "-m", f"v{newv}: {msg}") and ok
ok = run("git", "tag", "-a", f"v{newv}", "-m", f"VideoFlex {newv}") and ok
ok = run("git", "push", "origin", "main") and ok
ok = run("git", "push", "origin", f"v{newv}") and ok
print("LISTO v" + newv if ok else "REVISAR errores arriba")
