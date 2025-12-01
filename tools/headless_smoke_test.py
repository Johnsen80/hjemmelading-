import os, sys, traceback
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
# Ensure repo root on sys.path
sys.path.insert(0, r'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading')
print('HEADLESS_SMOKE: start')
try:
    # Try to import QtWebEngine early (it must be imported before a Q(Core)Application
    # is created in some environments). If not available, ensure we set the
    # AA_ShareOpenGLContexts attribute on QApplication before instantiation.
    try:
        from PyQt6 import QtWebEngineWidgets
        print('HEADLESS_SMOKE: QtWebEngineWidgets imported')
    except Exception as e:
        print('HEADLESS_SMOKE: QtWebEngineWidgets import failed:', e)

    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication
    try:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        print('HEADLESS_SMOKE: Set AA_ShareOpenGLContexts')
    except Exception:
        pass

    app = QApplication([])
    print('HEADLESS_SMOKE: QApplication created')
    # Try to register any bundled fonts so Qt and matplotlib can find glyphs
    try:
        # Import local helper if present
        try:
            from HjemmeladingApp.utils.fonts import register_bundled_fonts
        except Exception:
            register_bundled_fonts = None
        if register_bundled_fonts:
            n = register_bundled_fonts()
            print('HEADLESS_SMOKE: registered bundled fonts count:', n)
    except Exception as e:
        print('HEADLESS_SMOKE: font registration failed:', e)
    # Settings dialog (use the packaged UI path)
    try:
        from HjemmeladingApp.ui.settings_dialog import SettingsDialog
        sd = SettingsDialog()
        print('HEADLESS_SMOKE: SettingsDialog instantiated')
        try:
            sd.close()
        except Exception:
            pass
    except Exception:
        print('HEADLESS_SMOKE: SettingsDialog failed:')
        traceback.print_exc()
    # Main window
    try:
        from src.ui.main_window import MainWindow
        mw = MainWindow()
        print('HEADLESS_SMOKE: MainWindow instantiated')
        try:
            mw.close()
        except Exception:
            pass
    except Exception:
        print('HEADLESS_SMOKE: MainWindow failed:')
        traceback.print_exc()
    # Process events briefly
    try:
        app.processEvents()
        print('HEADLESS_SMOKE: processEvents done')
    except Exception:
        traceback.print_exc()
    # Add a small matplotlib font diagnostic so we can see what matplotlib
    # sees at runtime (whether DejaVu Sans is available and roughly how many
    # font families matplotlib knows about).
    try:
        import matplotlib as mpl
        from matplotlib import font_manager as fm
        print('HEADLESS_SMOKE: matplotlib version', getattr(mpl, '__version__', '?'))
        try:
            ttflist = fm.fontManager.ttflist
            families = sorted({fe.name for fe in ttflist if getattr(fe, 'name', None)})
            print('HEADLESS_SMOKE: matplotlib font families count:', len(families))
            print('HEADLESS_SMOKE: sample families:', families[:20])
            print('HEADLESS_SMOKE: DejaVu Sans present:', any('DejaVu Sans' in f for f in families))
        except Exception as e:
            print('HEADLESS_SMOKE: unable to query fontManager.ttflist:', e)
    except Exception as e:
        print('HEADLESS_SMOKE: matplotlib not available or failed to import:', e)
        traceback.print_exc()
    try:
        app.quit()
    except Exception:
        pass
except Exception:
    traceback.print_exc()
print('HEADLESS_SMOKE: done')
