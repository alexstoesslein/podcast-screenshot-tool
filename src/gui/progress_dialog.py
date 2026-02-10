"""
Progress Dialog - Shows progress for long-running operations
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal


class ProgressDialog(QDialog):
    """Dialog showing progress of operations."""

    cancelled = pyqtSignal()

    def __init__(self, title: str = "Verarbeitung...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._cancelled = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Status label
        self.status_label = QLabel("Starte...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Detail label
        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("color: #888; font-size: 11px;")
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.detail_label)

        # Cancel button
        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_btn)

    def set_status(self, text: str):
        """Set the main status text."""
        self.status_label.setText(text)

    def set_detail(self, text: str):
        """Set the detail text."""
        self.detail_label.setText(text)

    def set_progress(self, current: int, total: int):
        """Set progress values."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.detail_label.setText(f"{current} / {total}")

    def set_indeterminate(self, indeterminate: bool):
        """Set indeterminate mode."""
        if indeterminate:
            self.progress_bar.setMaximum(0)
        else:
            self.progress_bar.setMaximum(100)

    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._cancelled

    def _on_cancel(self):
        """Handle cancel button click."""
        self._cancelled = True
        self.cancelled.emit()
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Abbrechen...")

    def finish(self, success: bool = True, message: str = None):
        """Finish the dialog."""
        if success:
            self.set_status("Fertig!" if message is None else message)
            self.progress_bar.setValue(100)
        else:
            self.set_status("Fehler!" if message is None else message)

        self.cancel_btn.setText("Schliessen")
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.accept)

    def closeEvent(self, event):
        """Handle close event."""
        if not self._cancelled and self.progress_bar.value() < 100:
            self._on_cancel()
            event.ignore()
        else:
            event.accept()
