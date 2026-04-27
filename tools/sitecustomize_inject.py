import zipfile

p = "dist/VALKYRIE_BALLISTICS/_internal/base_library.zip"
with zipfile.ZipFile(p, "a") as z:
    z.writestr(
        "sitecustomize.py", open("tools/sitecustomize_for_headless.py", "rb").read()
    )
print("wrote sitecustomize to", p)
