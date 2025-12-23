p = r"C:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/HjemmeladingApp/main.py"
start = 480
end = 540
with open(p, "r", encoding="utf-8") as f:
    for i, l in enumerate(f, start=1):
        if start <= i <= end:
            print(f"{i:4}: {l.rstrip()}")
