"""
Video Preview Widget - Displays video with 16:9 aspect ratio
"""
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

from ..core.video_analyzer import VideoAnalyzer


class AspectRatioWidget(QWidget):
    """Widget that maintains a fixed aspect ratio."""

    def __init__(self, aspect_ratio=16/9, parent=None):
        super().__init__(parent)
        self.aspect_ratio = aspect_ratio
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

    def heightForWidth(self, width):
        return int(width / self.aspect_ratio)

    def hasHeightForWidth(self):
        return True

    def sizeHint(self):
        width = self.width()
        return self.size()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Maintain aspect ratio
        w = self.width()
        h = int(w / self.aspect_ratio)
        if h > self.height():
            h = self.height()
            w = int(h * self.aspect_ratio)


class VideoPreviewWidget(QWidget):
    """Widget for video preview with timeline scrubbing."""

    frame_selected = pyqtSignal(int)
    position_changed = pyqtSignal(int, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_analyzer = VideoAnalyzer()
        self.current_frame_number = 0
        self.lut_preview_enabled = False
        self.lut_processor = None
        self.aspect_ratio = 16 / 9

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video container
        self.video_container = QFrame()
        self.video_container.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 12px;
            }
        """)
        container_layout = QVBoxLayout(self.video_container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(12)

        # Video display with 16:9 aspect ratio
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(320, 180)
        self.video_label.setStyleSheet("""
            background-color: #000000;
            border-radius: 8px;
        """)
        self.video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        container_layout.addWidget(self.video_label, stretch=1)

        # Timeline row
        timeline_row = QHBoxLayout()
        timeline_row.setSpacing(12)

        self.time_label = QLabel("00:00.00")
        self.time_label.setMinimumWidth(70)
        self.time_label.setStyleSheet("""
            color: #ffffff;
            font-size: 13px;
            font-weight: 500;
        """)
        timeline_row.addWidget(self.time_label)

        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(100)
        self.timeline_slider.setValue(0)
        self.timeline_slider.setMinimumHeight(32)
        self.timeline_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.timeline_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background-color: #3a3a3a;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 18px;
                height: 18px;
                margin: -6px 0;
                background-color: #ffffff;
                border: none;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background-color: #007AFF;
            }
            QSlider::sub-page:horizontal {
                background-color: #007AFF;
                border-radius: 3px;
            }
        """)
        self.timeline_slider.valueChanged.connect(self._on_slider_changed)
        timeline_row.addWidget(self.timeline_slider, stretch=1)

        self.duration_label = QLabel("00:00.00")
        self.duration_label.setMinimumWidth(70)
        self.duration_label.setStyleSheet("""
            color: #ffffff;
            font-size: 13px;
            font-weight: 500;
        """)
        timeline_row.addWidget(self.duration_label)

        container_layout.addLayout(timeline_row)

        # Controls row
        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        btn_style = """
            QPushButton {
                background-color: #3a3a3a;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                min-width: 40px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #5a5a5a;
            }
        """

        self.prev_frame_btn = QPushButton("◀")
        self.prev_frame_btn.setStyleSheet(btn_style)
        self.prev_frame_btn.setToolTip("Vorheriges Frame (←)")
        self.prev_frame_btn.clicked.connect(self._prev_frame)
        controls_row.addWidget(self.prev_frame_btn)

        self.next_frame_btn = QPushButton("▶")
        self.next_frame_btn.setStyleSheet(btn_style)
        self.next_frame_btn.setToolTip("Nächstes Frame (→)")
        self.next_frame_btn.clicked.connect(self._next_frame)
        controls_row.addWidget(self.next_frame_btn)

        controls_row.addStretch()

        self.add_frame_btn = QPushButton("+ Frame hinzufügen")
        self.add_frame_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 16px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
            QPushButton:disabled {
                background-color: #3a3a3a;
                color: #5a5a5a;
            }
        """)
        self.add_frame_btn.setToolTip("Frame zur Auswahl hinzufügen (Leertaste)")
        self.add_frame_btn.clicked.connect(self._add_current_frame)
        controls_row.addWidget(self.add_frame_btn)

        controls_row.addStretch()

        self.frame_info_label = QLabel("Frame: 0 / 0")
        self.frame_info_label.setStyleSheet("""
            color: #888888;
            font-size: 13px;
        """)
        controls_row.addWidget(self.frame_info_label)

        container_layout.addLayout(controls_row)

        layout.addWidget(self.video_container)

        self._set_controls_enabled(False)

    def load_video(self, filepath: str) -> bool:
        """Load a video file."""
        video_info = self.video_analyzer.load_video(filepath)
        if video_info is None:
            return False

        # Update aspect ratio based on video
        self.aspect_ratio = video_info.width / video_info.height

        self.timeline_slider.setMaximum(video_info.frame_count - 1)
        self.timeline_slider.setValue(0)
        self.duration_label.setText(
            VideoAnalyzer.format_timestamp(video_info.duration)
        )

        self._seek_to_frame(0)
        self._set_controls_enabled(True)

        return True

    def set_lut_processor(self, lut_processor):
        """Set the LUT processor for preview."""
        self.lut_processor = lut_processor

    def set_lut_preview(self, enabled: bool):
        """Enable/disable LUT preview."""
        self.lut_preview_enabled = enabled
        self._update_display()

    def get_current_frame_number(self) -> int:
        """Get the current frame number."""
        return self.current_frame_number

    def get_video_analyzer(self) -> VideoAnalyzer:
        """Get the video analyzer instance."""
        return self.video_analyzer

    def _set_controls_enabled(self, enabled: bool):
        """Enable or disable playback controls."""
        self.timeline_slider.setEnabled(enabled)
        self.prev_frame_btn.setEnabled(enabled)
        self.next_frame_btn.setEnabled(enabled)
        self.add_frame_btn.setEnabled(enabled)

    def _on_slider_changed(self, value: int):
        """Handle timeline slider changes."""
        self._seek_to_frame(value)

    def _seek_to_frame(self, frame_number: int):
        """Seek to a specific frame."""
        self.current_frame_number = frame_number
        self._update_display()

        if self.video_analyzer.video_info:
            timestamp = frame_number / self.video_analyzer.video_info.fps
            self.time_label.setText(VideoAnalyzer.format_timestamp(timestamp))
            self.frame_info_label.setText(
                f"Frame: {frame_number} / {self.video_analyzer.video_info.frame_count - 1}"
            )
            self.position_changed.emit(frame_number, timestamp)

    def _update_display(self):
        """Update the video display with current frame."""
        frame = self.video_analyzer.get_frame_at_position(self.current_frame_number)
        if frame is None:
            return

        if self.lut_preview_enabled and self.lut_processor and self.lut_processor.is_loaded():
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb = self.lut_processor.apply_to_image(rgb)
        else:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Calculate display size maintaining aspect ratio
        label_w = self.video_label.width()
        label_h = self.video_label.height()

        if label_w <= 0 or label_h <= 0:
            return

        h, w = rgb.shape[:2]
        video_ratio = w / h
        label_ratio = label_w / label_h

        if video_ratio > label_ratio:
            # Video is wider - fit to width
            new_w = label_w
            new_h = int(label_w / video_ratio)
        else:
            # Video is taller - fit to height
            new_h = label_h
            new_w = int(label_h * video_ratio)

        # Ensure minimum size
        new_w = max(100, new_w)
        new_h = max(56, new_h)

        scaled = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)

        qimage = QImage(
            scaled.data,
            new_w, new_h,
            new_w * 3,
            QImage.Format.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qimage)
        self.video_label.setPixmap(pixmap)

    def _prev_frame(self):
        """Go to previous frame."""
        if self.current_frame_number > 0:
            self.timeline_slider.setValue(self.current_frame_number - 1)

    def _next_frame(self):
        """Go to next frame."""
        if self.video_analyzer.video_info:
            max_frame = self.video_analyzer.video_info.frame_count - 1
            if self.current_frame_number < max_frame:
                self.timeline_slider.setValue(self.current_frame_number + 1)

    def _add_current_frame(self):
        """Signal to add current frame to selection."""
        self.frame_selected.emit(self.current_frame_number)

    def resizeEvent(self, event):
        """Handle resize to update video display."""
        super().resizeEvent(event)
        if self.video_analyzer.video_info:
            self._update_display()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Space:
            self._add_current_frame()
        elif event.key() == Qt.Key.Key_Left:
            self._prev_frame()
        elif event.key() == Qt.Key.Key_Right:
            self._next_frame()
        else:
            super().keyPressEvent(event)

    def close_video(self):
        """Close the current video."""
        self.video_analyzer.close()
        self.video_label.clear()
        self.video_label.setStyleSheet("background-color: #000000; border-radius: 8px;")
        self._set_controls_enabled(False)
        self.time_label.setText("00:00.00")
        self.duration_label.setText("00:00.00")
        self.frame_info_label.setText("Frame: 0 / 0")
