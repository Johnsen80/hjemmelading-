import zipfile

p = "dist/VALKYRIE_BALLISTICS/_internal/base_library.zip"
with zipfile.ZipFile(p) as z:
    entries = [n for n in z.namelist() if n.startswith("src/ui/")]
    for n in entries:
        print(n)
