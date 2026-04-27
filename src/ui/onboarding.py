from src.qt_compat import QFont, QSettings, QtWidgets
from src.utils.i18n import tr

QComboBox = QtWidgets.QComboBox
QDialog = QtWidgets.QDialog
QFormLayout = QtWidgets.QFormLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton
QStackedWidget = QtWidgets.QStackedWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QWidget = QtWidgets.QWidget

from src.ui.icon_registry import get_icon
from src.ui.reloading_theme import ReloadingTheme


class OnboardingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("onboarding_title"))
        self.setMinimumSize(520, 320)
        # allow stylesheet targeting and apply central stylesheet safely
        self.setObjectName("onboardingDialog")
        try:
            self.setStyleSheet(ReloadingTheme.get_stylesheet())
        except Exception:
            pass
        layout = QVBoxLayout()

        title = QLabel(tr("onboarding_heading"))
        title.setFont(QFont("Segoe UI", 16))
        title.setObjectName("onboardingTitle")
        # optional icon at the top if available
        try:
            ic = get_icon("welcome")
            if ic:
                title.setPixmap(ic.pixmap(24, 24))
        except Exception:
            pass
        layout.addWidget(title)

        body = QLabel(tr("onboarding_body"))
        body.setWordWrap(True)
        layout.addWidget(body)

        btn_layout = QHBoxLayout()
        btn_close = QPushButton(tr("onboarding_close"))
        btn_close.clicked.connect(self._dismiss_and_save)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _dismiss_and_save(self):
        try:
            settings = QSettings("VALKYRIE", "Hjemmelading")
            settings.setValue("onboarding_seen", True)
        except Exception:
            pass
        self.accept()


class FirstRunSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("first_run_title"))
        self.setMinimumSize(520, 360)
        self.setObjectName("firstRunSetupDialog")
        try:
            self.setStyleSheet(ReloadingTheme.get_stylesheet())
        except Exception:
            pass

        root = QVBoxLayout(self)

        title = QLabel(tr("first_run_heading"))
        title.setFont(QFont("Segoe UI", 16))
        title.setObjectName("onboardingTitle")
        root.addWidget(title)

        subtitle = QLabel(tr("first_run_subtitle"))
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        self.pages = QStackedWidget(self)
        root.addWidget(self.pages, 1)

        self._build_language_page()
        self._build_units_page()

        btn_row = QHBoxLayout()
        self.back_btn = QPushButton(tr("first_run_back"))
        self.back_btn.clicked.connect(self._go_back)
        btn_row.addWidget(self.back_btn)

        btn_row.addStretch()

        self.skip_btn = QPushButton(tr("first_run_skip"))
        self.skip_btn.clicked.connect(self._skip)
        btn_row.addWidget(self.skip_btn)

        self.next_btn = QPushButton(tr("first_run_next"))
        self.next_btn.clicked.connect(self._go_next)
        btn_row.addWidget(self.next_btn)

        self.finish_btn = QPushButton(tr("first_run_finish"))
        self.finish_btn.clicked.connect(self._finish)
        btn_row.addWidget(self.finish_btn)

        root.addLayout(btn_row)

        self._load_current_values()
        self._update_buttons()

    def _build_language_page(self) -> None:
        page = QWidget(self.pages)
        layout = QVBoxLayout(page)
        form = QFormLayout()

        self.language_combo = QComboBox(page)
        self.language_combo.addItem(tr("first_run_lang_en"), "en")
        self.language_combo.addItem(tr("first_run_lang_no"), "no")
        form.addRow(tr("first_run_language"), self.language_combo)

        layout.addLayout(form)
        layout.addStretch()
        self.pages.addWidget(page)

    def _build_units_page(self) -> None:
        page = QWidget(self.pages)
        layout = QVBoxLayout(page)
        form = QFormLayout()

        self.click_combo = QComboBox(page)
        self.click_combo.addItem("MOA", "MOA")
        self.click_combo.addItem("MRAD", "MRAD")
        form.addRow(tr("first_run_click_unit"), self.click_combo)

        self.distance_combo = QComboBox(page)
        self.distance_combo.addItem(tr("first_run_distance_meter"), "Meter")
        self.distance_combo.addItem(tr("first_run_distance_yards"), "Yards")
        form.addRow(tr("first_run_distance"), self.distance_combo)

        self.temp_combo = QComboBox(page)
        self.temp_combo.addItem(tr("first_run_temp_celsius"), "Celsius")
        self.temp_combo.addItem(tr("first_run_temp_fahrenheit"), "Fahrenheit")
        form.addRow(tr("first_run_temperature"), self.temp_combo)

        self.measure_combo = QComboBox(page)
        self.measure_combo.addItem(tr("first_run_measurement_mm"), "Millimeter (mm)")
        self.measure_combo.addItem(
            tr("first_run_measurement_inches"), "Tommer (inches)"
        )
        form.addRow(tr("first_run_measurements"), self.measure_combo)

        layout.addLayout(form)
        layout.addStretch()
        self.pages.addWidget(page)

    def _load_current_values(self) -> None:
        try:
            from src.utils.i18n import normalize_language_code

            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            language = normalize_language_code(settings.value("language", "en"))
            click_unit = settings.value("units/click_unit", "MOA")
            distance = settings.value("units/distance", "Meter")
            temp = settings.value("units/temperature", "Celsius")
            measurement = settings.value("units/measurement", "Millimeter (mm)")
        except Exception:
            language = "en"
            click_unit = "MOA"
            distance = "Meter"
            temp = "Celsius"
            measurement = "Millimeter (mm)"

        self._set_combo_by_data(self.language_combo, str(language))
        self._set_combo_by_data(self.click_combo, str(click_unit))
        self._set_combo_by_data(self.distance_combo, str(distance))
        self._set_combo_by_data(self.temp_combo, str(temp))
        self._set_combo_by_data(self.measure_combo, str(measurement))

    def _set_combo_by_data(self, combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _update_buttons(self) -> None:
        idx = self.pages.currentIndex()
        last = self.pages.count() - 1
        self.back_btn.setEnabled(idx > 0)
        self.next_btn.setVisible(idx < last)
        self.finish_btn.setVisible(idx >= last)

    def _go_back(self) -> None:
        idx = self.pages.currentIndex()
        if idx > 0:
            self.pages.setCurrentIndex(idx - 1)
        self._update_buttons()

    def _go_next(self) -> None:
        idx = self.pages.currentIndex()
        last = self.pages.count() - 1
        if idx < last:
            self.pages.setCurrentIndex(idx + 1)
        self._update_buttons()

    def _skip(self) -> None:
        self._save_settings()
        self.accept()

    def _finish(self) -> None:
        self._save_settings()
        self.accept()

    def _save_settings(self) -> None:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            language_value = str(self.language_combo.currentData() or "en")
            click_value = str(self.click_combo.currentData() or "MOA")
            distance_value = str(self.distance_combo.currentData() or "Meter")
            temp_value = str(self.temp_combo.currentData() or "Celsius")
            measurement_value = str(
                self.measure_combo.currentData() or "Millimeter (mm)"
            )
            settings.setValue("language", language_value)
            settings.setValue("units/click_unit", click_value)
            settings.setValue("units/distance", distance_value)
            settings.setValue("units/temperature", temp_value)
            settings.setValue("units/measurement", measurement_value)

            global_units = (
                "metric" if distance_value.lower().startswith("meter") else "imperial"
            )
            settings.setValue("units/global", global_units)
            settings.setValue("setup/first_run_completed", True)
        except Exception:
            pass

        try:
            from src.utils.i18n import normalize_language_code, set_language

            lang = normalize_language_code(self.language_combo.currentData() or "en")
            set_language(lang)
        except Exception:
            pass
