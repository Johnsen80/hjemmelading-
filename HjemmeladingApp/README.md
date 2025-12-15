# Valkyrie Ballistics

Local dev notes

- Run tests:
```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

- Run the app (requires PyQt6/Pillow as installed in your environment):
```powershell
# start app
python main.py
```

- Quick checks (linters):
```powershell
python -m ruff check . --fix
python -m black --check .
python -m flake8 .
```

If you want to push and open a PR, add remote and push branch `lint/auto-fix`.
