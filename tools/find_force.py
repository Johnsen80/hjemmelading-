p = r"C:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/HjemmeladingApp/main.py"
with open(p, "r", encoding="utf-8") as f:
    for i, l in enumerate(f, start=1):
        if "_FORCE_PARENT_TO" in l:
            print(i, l.rstrip())
