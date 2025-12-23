import sys

p = r"C:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/src/ui/main_window.py"
with open(p, "r", encoding="utf-8") as f:
    for i, ln in enumerate(f, start=1):
        if 1115 <= i <= 1135:
            sys.stdout.write(f"{i:5}: {ln.rstrip()}\n")
