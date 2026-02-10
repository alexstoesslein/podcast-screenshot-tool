"""
Main Window - Primary application window with responsive design
"""
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QComboBox,
    QCheckBox, QFileDialog, QMessageBox,
    QLineEdit, QApplication, QSlider,
    QFrame, QSizePolicy, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QFont

from .video_preview import VideoPreviewWidget
from .frame_list import FrameListWidget
from .progress_dialog import ProgressDialog
from .apple_style import get_stylesheet, COLORS
from ..core.video_analyzer import VideoAnalyzer, SelectedFrame
from ..core.screenshot_exporter import ScreenshotExporter, ExportSettings
from ..core.project_types import ProjectTypes
from ..utils.lut_processor import LUTProcessor
from ..utils.image_formats import ImageFormats


class AnalyzeWorker(QThread):
    """Worker thread for video analysis."""

    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, video_analyzer: VideoAnalyzer, num_frames: int, project_type: str):
        super().__init__()
        self.video_analyzer = video_analyzer
        self.num_frames = num_frames
        self.project_type = project_type
        self._cancelled = False

    def run(self):
        try:
            def progress_callback(current, total):
                if self._cancelled:
                    raise InterruptedError("Cancelled")
                self.progress.emit(current, total)

            settings = ProjectTypes.get_settings(self.project_type)
            self.video_analyzer.frame_scorer.set_weights(
                settings.face_weight,
                settings.sharpness_weight,
                settings.stability_weight
            )

            frames = self.video_analyzer.analyze_video(
                num_frames=self.num_frames,
                progress_callback=progress_callback
            )
            self.finished.emit(frames)
        except InterruptedError:
            self.finished.emit([])
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self._cancelled = True


class ExportWorker(QThread):
    """Worker thread for exporting screenshots."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, exporter: ScreenshotExporter, frames: list, settings: ExportSettings):
        super().__init__()
        self.exporter = exporter
        self.frames = frames
        self.settings = settings
        self._cancelled = False

    def run(self):
        try:
            def progress_callback(current, total, filename):
                if self._cancelled:
                    raise InterruptedError("Cancelled")
                self.progress.emit(current, total, filename)

            files = self.exporter.export_frames(
                self.frames,
                self.settings,
                progress_callback
            )
            self.finished.emit(files)
        except InterruptedError:
            self.finished.emit([])
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self._cancelled = True


class MainWindow(QMainWindow):
    """Main application window with responsive vertical layout."""

    SETTINGS_ORG = "ScreenshotTool"
    SETTINGS_APP = "ScreenshotTool"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screenshot Tool")
        self.setMinimumSize(800, 600)

        self.settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        self.lut_processor = LUTProcessor()
        self.exporter = ScreenshotExporter(self.lut_processor)
        self.output_folder = str(Path.home() / "Desktop")

        self._setup_ui()
        self._connect_signals()
        self._load_settings()

    def _create_section_title(self, text: str) -> QLabel:
        """Create a styled section title label."""
        label = QLabel(text)
        label.setProperty("class", "title")
        return label

    def _create_secondary_label(self, text: str) -> QLabel:
        """Create a secondary styled label."""
        label = QLabel(text)
        label.setProperty("class", "secondary")
        return label

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # ===== MAIN CONTENT: VIDEO LEFT + SIDEBAR RIGHT =====
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # ===== LEFT: VIDEO + FRAMES =====
        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)

        # Video header
        video_header = QHBoxLayout()
        self.import_btn = QPushButton("Video importieren")
        self.import_btn.setProperty("class", "primary")
        self.import_btn.setMinimumHeight(40)
        video_header.addWidget(self.import_btn)

        video_header.addSpacing(16)

        self.video_info_label = QLabel("")
        self.video_info_label.setProperty("class", "secondary")
        video_header.addWidget(self.video_info_label)

        video_header.addStretch()
        left_panel.addLayout(video_header)

        # Video preview (16:9 aspect ratio)
        self.video_preview = VideoPreviewWidget()
        self.video_preview.set_lut_processor(self.lut_processor)
        left_panel.addWidget(self.video_preview, stretch=1)

        # Frame list
        frame_card = QFrame()
        frame_card.setProperty("class", "card")
        frame_card_layout = QVBoxLayout(frame_card)
        frame_card_layout.setSpacing(8)
        frame_card_layout.setContentsMargins(12, 12, 12, 12)

        frame_card_layout.addWidget(self._create_section_title("Ausgewählte Frames"))

        self.frame_list = FrameListWidget()
        self.frame_list.setMinimumHeight(100)
        self.frame_list.setMaximumHeight(140)
        frame_card_layout.addWidget(self.frame_list)

        left_panel.addWidget(frame_card)

        content_layout.addLayout(left_panel, stretch=1)

        # ===== RIGHT: SETTINGS SIDEBAR (scrollable) =====
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFixedWidth(300)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        sidebar = QFrame()
        sidebar.setProperty("class", "card")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(14)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)

        # Project type
        sidebar_layout.addWidget(self._create_section_title("Projekt"))
        self.project_type_combo = QComboBox()
        self.project_type_combo.addItems(ProjectTypes.get_type_names())
        self.project_type_combo.setToolTip(ProjectTypes.get_description("Podcast"))
        sidebar_layout.addWidget(self.project_type_combo)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("background-color: #E0E0E0; max-height: 1px;")
        sidebar_layout.addWidget(sep1)

        # Analysis
        sidebar_layout.addWidget(self._create_section_title("Analyse"))

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("Screenshots:"))
        count_row.addStretch()
        self.num_screenshots_spin = QSpinBox()
        self.num_screenshots_spin.setMinimum(1)
        self.num_screenshots_spin.setMaximum(50)
        self.num_screenshots_spin.setValue(5)
        count_row.addWidget(self.num_screenshots_spin)
        sidebar_layout.addLayout(count_row)

        self.analyze_btn = QPushButton("Video analysieren")
        self.analyze_btn.setMinimumHeight(40)
        self.analyze_btn.setEnabled(False)
        sidebar_layout.addWidget(self.analyze_btn)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: #E0E0E0; max-height: 1px;")
        sidebar_layout.addWidget(sep2)

        # LUT
        sidebar_layout.addWidget(self._create_section_title("Farbkorrektur"))

        self.lut_btn = QPushButton("LUT laden...")
        self.lut_btn.setMinimumHeight(36)
        sidebar_layout.addWidget(self.lut_btn)

        self.lut_label = QLabel("Kein LUT geladen")
        self.lut_label.setProperty("class", "secondary")
        sidebar_layout.addWidget(self.lut_label)

        lut_checks = QHBoxLayout()
        self.apply_lut_check = QCheckBox("Anwenden")
        self.apply_lut_check.setEnabled(False)
        lut_checks.addWidget(self.apply_lut_check)
        self.preview_lut_check = QCheckBox("Vorschau")
        self.preview_lut_check.setEnabled(False)
        lut_checks.addWidget(self.preview_lut_check)
        lut_checks.addStretch()
        sidebar_layout.addLayout(lut_checks)

        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet("background-color: #E0E0E0; max-height: 1px;")
        sidebar_layout.addWidget(sep3)

        # Export
        sidebar_layout.addWidget(self._create_section_title("Export"))

        sidebar_layout.addWidget(QLabel("Dateiname:"))
        self.prefix_edit = QLineEdit("screenshot")
        self.prefix_edit.setPlaceholderText("z.B. podcast_ep01")
        sidebar_layout.addWidget(self.prefix_edit)

        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Format:"))
        format_row.addStretch()
        self.format_combo = QComboBox()
        self.format_combo.addItems(ImageFormats.get_format_list())
        self.format_combo.setCurrentText("PNG")
        format_row.addWidget(self.format_combo)
        sidebar_layout.addLayout(format_row)

        quality_row = QHBoxLayout()
        quality_row.addWidget(QLabel("Qualität:"))
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(95)
        quality_row.addWidget(self.quality_slider)
        self.quality_label = QLabel("95%")
        self.quality_label.setMinimumWidth(40)
        quality_row.addWidget(self.quality_label)
        sidebar_layout.addLayout(quality_row)

        self.quality_info_label = self._create_secondary_label("Nur für JPG/WebP")
        sidebar_layout.addWidget(self.quality_info_label)

        sidebar_layout.addWidget(QLabel("Speicherort:"))
        self.output_folder_edit = QLineEdit(self.output_folder)
        self.output_folder_edit.setReadOnly(True)
        sidebar_layout.addWidget(self.output_folder_edit)

        self.browse_folder_btn = QPushButton("Ordner wählen...")
        sidebar_layout.addWidget(self.browse_folder_btn)

        # Spacer before export button
        sidebar_layout.addSpacing(20)

        self.export_btn = QPushButton("Screenshots exportieren")
        self.export_btn.setProperty("class", "primary")
        self.export_btn.setMinimumHeight(44)
        self.export_btn.setEnabled(False)
        sidebar_layout.addWidget(self.export_btn)

        sidebar_scroll.setWidget(sidebar)
        content_layout.addWidget(sidebar_scroll)

        main_layout.addLayout(content_layout, stretch=1)

        # Status bar
        self.statusBar().showMessage("Bereit – Importiere ein Video um zu starten")

        # Initial format state
        self._on_format_changed("PNG")

    def _connect_signals(self):
        """Connect UI signals to handlers."""
        self.import_btn.clicked.connect(self._import_video)
        self.lut_btn.clicked.connect(self._load_lut)
        self.browse_folder_btn.clicked.connect(self._browse_output_folder)
        self.analyze_btn.clicked.connect(self._analyze_video)
        self.export_btn.clicked.connect(self._export_screenshots)

        self.video_preview.frame_selected.connect(self._add_manual_frame)
        self.apply_lut_check.toggled.connect(self._on_lut_setting_changed)
        self.preview_lut_check.toggled.connect(self._on_lut_preview_changed)

        self.frame_list.frame_removed.connect(self._on_frame_removed)
        self.quality_slider.valueChanged.connect(self._on_quality_changed)
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        self.project_type_combo.currentTextChanged.connect(self._on_project_type_changed)

    def _on_quality_changed(self, value: int):
        self.quality_label.setText(f"{value}%")

    def _on_format_changed(self, format_name: str):
        if format_name in ['JPG', 'WebP']:
            self.quality_slider.setEnabled(True)
            self.quality_info_label.setText("Nur für JPG/WebP")
        else:
            self.quality_slider.setEnabled(False)
            self.quality_info_label.setText("Verlustfrei")

    def _on_project_type_changed(self, type_name: str):
        description = ProjectTypes.get_description(type_name)
        self.project_type_combo.setToolTip(description)
        self.statusBar().showMessage(f"Projekttyp: {type_name} – {description}")

    def _import_video(self):
        formats = " ".join(f"*{ext}" for ext in VideoAnalyzer.SUPPORTED_FORMATS)
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Video importieren",
            str(Path.home()),
            f"Video Dateien ({formats})"
        )

        if filepath:
            self.statusBar().showMessage(f"Lade {Path(filepath).name}...")
            QApplication.processEvents()

            if self.video_preview.load_video(filepath):
                video_info = self.video_preview.get_video_analyzer().video_info
                self.video_info_label.setText(
                    f"{video_info.width}×{video_info.height} | "
                    f"{video_info.fps:.1f} fps | "
                    f"{VideoAnalyzer.format_timestamp(video_info.duration)}"
                )
                self.analyze_btn.setEnabled(True)
                self.frame_list.clear_all()

                video_name = Path(filepath).stem
                self.prefix_edit.setText(video_name)

                self.statusBar().showMessage(f"Video geladen: {Path(filepath).name}")
            else:
                QMessageBox.warning(self, "Fehler", "Video konnte nicht geladen werden.")
                self.statusBar().showMessage("Fehler beim Laden des Videos.")

    def _load_lut(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "LUT laden",
            str(Path.home()),
            "Cube LUT (*.cube)"
        )

        if filepath:
            if self.lut_processor.load_cube(filepath):
                lut_name = self.lut_processor.get_lut_name()
                self.lut_label.setText(f"✓ {lut_name}")
                self.lut_label.setStyleSheet(f"color: {COLORS['accent_green']};")
                self.apply_lut_check.setEnabled(True)
                self.preview_lut_check.setEnabled(True)
                self.settings.setValue("last_lut_path", filepath)
                self.statusBar().showMessage(f"LUT geladen: {lut_name}")
            else:
                QMessageBox.warning(self, "Fehler", "LUT konnte nicht geladen werden.")

    def _browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Ausgabeordner wählen",
            self.output_folder
        )

        if folder:
            self.output_folder = folder
            self.output_folder_edit.setText(folder)

    def _analyze_video(self):
        video_analyzer = self.video_preview.get_video_analyzer()
        if video_analyzer.video_info is None:
            return

        num_frames = self.num_screenshots_spin.value()
        project_type = self.project_type_combo.currentText()

        self.progress_dialog = ProgressDialog("Video analysieren...", self)

        self.analyze_worker = AnalyzeWorker(video_analyzer, num_frames, project_type)
        self.analyze_worker.progress.connect(self._on_analyze_progress)
        self.analyze_worker.finished.connect(self._on_analyze_finished)
        self.analyze_worker.error.connect(self._on_analyze_error)

        self.progress_dialog.cancelled.connect(self.analyze_worker.cancel)
        self.progress_dialog.set_status(f"Analysiere als '{project_type}'...")

        self.analyze_worker.start()
        self.progress_dialog.exec()

    def _on_analyze_progress(self, current: int, total: int):
        self.progress_dialog.set_progress(current, total)

    def _on_analyze_finished(self, frames: list):
        if frames:
            self.frame_list.clear_all()
            self.frame_list.add_frames(frames)
            self.export_btn.setEnabled(True)
            self.progress_dialog.finish(True, f"{len(frames)} Frames gefunden!")
            self.statusBar().showMessage(f"Analyse abgeschlossen – {len(frames)} Frames ausgewählt")
        else:
            self.progress_dialog.finish(False, "Keine Frames gefunden oder abgebrochen.")

    def _on_analyze_error(self, error: str):
        self.progress_dialog.finish(False, f"Fehler: {error}")
        QMessageBox.critical(self, "Fehler", f"Analyse fehlgeschlagen: {error}")

    def _add_manual_frame(self, frame_number: int):
        if self.frame_list.is_frame_already_added(frame_number):
            self.statusBar().showMessage("Frame bereits in der Auswahl.")
            return

        video_analyzer = self.video_preview.get_video_analyzer()
        frame = video_analyzer.create_manual_frame(frame_number)

        if frame:
            self.frame_list.add_frame(frame)
            self.export_btn.setEnabled(True)
            self.statusBar().showMessage(
                f"Frame {frame_number} hinzugefügt – {self.frame_list.get_frame_count()} Frames insgesamt"
            )

    def _on_frame_removed(self, index: int):
        if self.frame_list.get_frame_count() == 0:
            self.export_btn.setEnabled(False)

    def _on_lut_setting_changed(self, checked: bool):
        pass

    def _on_lut_preview_changed(self, checked: bool):
        self.video_preview.set_lut_preview(checked)

    def _export_screenshots(self):
        frames = self.frame_list.get_frames()
        if not frames:
            QMessageBox.information(self, "Export", "Keine Frames zum Exportieren ausgewählt.")
            return

        prefix = self.prefix_edit.text().strip()
        if not prefix:
            prefix = "screenshot"

        prefix = "".join(c for c in prefix if c.isalnum() or c in "-_ ")

        settings = ExportSettings(
            output_folder=self.output_folder,
            format_name=self.format_combo.currentText(),
            quality=self.quality_slider.value(),
            prefix=prefix,
            apply_lut=self.apply_lut_check.isChecked()
        )

        self.progress_dialog = ProgressDialog("Screenshots exportieren...", self)

        self.export_worker = ExportWorker(self.exporter, frames, settings)
        self.export_worker.progress.connect(self._on_export_progress)
        self.export_worker.finished.connect(self._on_export_finished)
        self.export_worker.error.connect(self._on_export_error)

        self.progress_dialog.cancelled.connect(self.export_worker.cancel)
        self.progress_dialog.set_status("Exportiere Screenshots...")

        self.export_worker.start()
        self.progress_dialog.exec()

    def _on_export_progress(self, current: int, total: int, filename: str):
        self.progress_dialog.set_progress(current, total)
        self.progress_dialog.set_detail(filename)

    def _on_export_finished(self, files: list):
        if files:
            self.progress_dialog.finish(True, f"{len(files)} Screenshots exportiert!")
            self.statusBar().showMessage(f"Export abgeschlossen – {len(files)} Dateien in {self.output_folder}")
        else:
            self.progress_dialog.finish(False, "Export abgebrochen.")

    def _on_export_error(self, error: str):
        self.progress_dialog.finish(False, f"Fehler: {error}")
        QMessageBox.critical(self, "Fehler", f"Export fehlgeschlagen: {error}")

    def closeEvent(self, event):
        self._save_settings()
        self.video_preview.close_video()
        event.accept()

    def _load_settings(self):
        last_lut = self.settings.value("last_lut_path", "")
        if last_lut and Path(last_lut).exists():
            if self.lut_processor.load_cube(last_lut):
                lut_name = self.lut_processor.get_lut_name()
                self.lut_label.setText(f"✓ {lut_name}")
                self.lut_label.setStyleSheet(f"color: {COLORS['accent_green']};")
                self.apply_lut_check.setEnabled(True)
                self.preview_lut_check.setEnabled(True)
                self.statusBar().showMessage(f"LUT automatisch geladen: {lut_name}")

        last_folder = self.settings.value("last_output_folder", "")
        if last_folder and Path(last_folder).exists():
            self.output_folder = last_folder
            self.output_folder_edit.setText(last_folder)

        last_project_type = self.settings.value("last_project_type", "Podcast")
        index = self.project_type_combo.findText(last_project_type)
        if index >= 0:
            self.project_type_combo.setCurrentIndex(index)

        last_format = self.settings.value("last_format", "PNG")
        index = self.format_combo.findText(last_format)
        if index >= 0:
            self.format_combo.setCurrentIndex(index)

        last_quality = self.settings.value("last_quality", 95, type=int)
        self.quality_slider.setValue(last_quality)

        last_count = self.settings.value("last_screenshot_count", 5, type=int)
        self.num_screenshots_spin.setValue(last_count)

    def _save_settings(self):
        if self.lut_processor.is_loaded():
            self.settings.setValue("last_lut_path", self.lut_processor.lut_path)

        self.settings.setValue("last_output_folder", self.output_folder)
        self.settings.setValue("last_project_type", self.project_type_combo.currentText())
        self.settings.setValue("last_format", self.format_combo.currentText())
        self.settings.setValue("last_quality", self.quality_slider.value())
        self.settings.setValue("last_screenshot_count", self.num_screenshots_spin.value())


def run_app():
    """Run the application."""
    import sys
    app = QApplication(sys.argv)

    # Apply Apple-style stylesheet
    app.setStyleSheet(get_stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
