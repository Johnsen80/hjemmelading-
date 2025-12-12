Optional Dependencies (install for full features)
===============================================

This project supports a number of optional, heavy dependencies used for plotting,
computer vision, and ML. The core application and headless/CI runs work without
these packages, but several GUI features (plots, image analysis, AI helpers)
require them.

Recommended optional packages and install commands (PowerShell, using the
project virtualenv `.venv`):

1) Matplotlib (plots / dashboards)

```powershell
& .venv\Scripts\python.exe -m pip install matplotlib
```

2) OpenCV (computer vision / target analyzer)

```powershell
& .venv\Scripts\python.exe -m pip install opencv-python
```

3) scikit-learn (lightweight ML models)

```powershell
& .venv\Scripts\python.exe -m pip install scikit-learn
```

4) TensorFlow (neural networks) — large install; optional

```powershell
& .venv\Scripts\python.exe -m pip install tensorflow
```

5) Prophet (time series forecasting)

```powershell
& .venv\Scripts\python.exe -m pip install prophet
```

6) SHAP (explainable ML)

```powershell
& .venv\Scripts\python.exe -m pip install shap
```

Notes
- Installing TensorFlow can be large and slow; prefer GPU wheels if applicable.
- After installing optional packages, re-run the import checker:

```powershell
& .venv\Scripts\python.exe -u tools/check_src_imports.py
```

If you want, I can also add an `extras` requirements file (e.g. `requirements-optional.txt`) or
prepare a single `pip install -r` command — tell me which option you prefer.
