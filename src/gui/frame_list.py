"""
Frame List Widget - Displays selected frames with Apple-style design
"""
import cv2
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QImage, QPixmap, QDrag

from ..core.video_analyzer import SelectedFrame, VideoAnalyzer
from .apple_style import COLORS


class FrameThumbnail(QFrame):
    """Single frame thumbnail widget with Apple-style design."""

    clicked = pyqtSignal(int)
    remove_requested = pyqtSignal(int)

    def __init__(self, frame: SelectedFrame, index: int, parent=None):
        super().__init__(parent)
        self.frame = frame
        self.index = index
        self.selected = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(180, 140)
        self.setMaximumSize(220, 170)

        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Thumbnail image container
        image_container = QFrame()
        image_container.setStyleSheet(f"""
            QFrame {{
                background-color: #000;
                border-radius: 6px;
            }}
        """)
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(164, 92)
        image_layout.addWidget(self.image_label)
        layout.addWidget(image_container)

        self._update_thumbnail()

        # Info row
        info_layout = QHBoxLayout()
        info_layout.setSpacing(6)

        # Frame type indicator
        type_text = "Manuell" if self.frame.is_manual else "Auto"
        type_color = COLORS['accent_green'] if self.frame.is_manual else COLORS['accent_blue']
        type_label = QLabel(type_text)
        type_label.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 600;
            color: {type_color};
            background-color: {type_color}20;
            padding: 2px 6px;
            border-radius: 4px;
        """)
        info_layout.addWidget(type_label)

        # Timestamp
        timestamp_str = VideoAnalyzer.format_timestamp(self.frame.timestamp)
        time_label = QLabel(timestamp_str)
        time_label.setStyleSheet(f"font-size: 11px; color: {COLORS['text_secondary']};")
        info_layout.addWidget(time_label)

        info_layout.addStretch()

        # Remove button
        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 11px;
                font-size: 12px;
                font-weight: 600;
                color: {COLORS['text_tertiary']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_red']}20;
                color: {COLORS['accent_red']};
            }}
        """)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.index))
        info_layout.addWidget(remove_btn)

        layout.addLayout(info_layout)

    def _update_thumbnail(self):
        """Update the thumbnail image."""
        frame_rgb = cv2.cvtColor(self.frame.image, cv2.COLOR_BGR2RGB)

        h, w = frame_rgb.shape[:2]
        scale = min(164 / w, 92 / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        scaled = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)

        qimage = QImage(
            scaled.data,
            new_w, new_h,
            new_w * 3,
            QImage.Format.Format_RGB888
        )
        self.image_label.setPixmap(QPixmap.fromImage(qimage))

    def _update_style(self):
        """Update frame style."""
        if self.selected:
            self.setStyleSheet(f"""
                FrameThumbnail {{
                    background-color: {COLORS['bg_primary']};
                    border: 2px solid {COLORS['accent_blue']};
                    border-radius: 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                FrameThumbnail {{
                    background-color: {COLORS['bg_primary']};
                    border: 1px solid {COLORS['border_light']};
                    border-radius: 10px;
                }}
                FrameThumbnail:hover {{
                    border-color: {COLORS['border_medium']};
                }}
            """)

    def set_selected(self, selected: bool):
        """Set selection state."""
        self.selected = selected
        self._update_style()

    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)
        super().mousePressEvent(event)

    def update_index(self, new_index: int):
        """Update the frame index."""
        self.index = new_index


class FrameListWidget(QWidget):
    """Widget displaying list of selected frames with Apple-style design."""

    frame_removed = pyqtSignal(int)
    frame_selected = pyqtSignal(int)
    frames_reordered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frames = []
        self.thumbnails = []
        self.selected_index = -1

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        self.count_label = QLabel("Ausgewählte Frames")
        self.count_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        header_layout.addWidget(self.count_label)

        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {COLORS['bg_primary']};
            background-color: {COLORS['text_tertiary']};
            padding: 2px 8px;
            border-radius: 10px;
            min-width: 20px;
        """)
        self.count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.count_badge)

        header_layout.addStretch()

        self.clear_btn = QPushButton("Alle entfernen")
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: 12px;
                color: {COLORS['accent_red']};
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        self.clear_btn.clicked.connect(self.clear_all)
        header_layout.addWidget(self.clear_btn)

        main_layout.addLayout(header_layout)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumHeight(190)
        scroll_area.setMaximumHeight(210)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 10px;
            }}
        """)

        # Container
        self.container = QWidget()
        self.container.setStyleSheet(f"background-color: {COLORS['bg_secondary']};")
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.container_layout.setContentsMargins(12, 12, 12, 12)
        self.container_layout.setSpacing(12)

        # Empty placeholder
        self.empty_label = QLabel(
            "Keine Frames ausgewählt\n"
            "Klicke auf 'Analysieren' oder füge manuell Frames hinzu"
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"""
            color: {COLORS['text_tertiary']};
            font-size: 13px;
            padding: 40px;
        """)
        self.container_layout.addWidget(self.empty_label)

        scroll_area.setWidget(self.container)
        main_layout.addWidget(scroll_area)

    def add_frame(self, frame: SelectedFrame):
        """Add a frame to the list."""
        self.empty_label.hide()

        index = len(self.frames)
        thumbnail = FrameThumbnail(frame, index)
        thumbnail.clicked.connect(self._on_thumbnail_clicked)
        thumbnail.remove_requested.connect(self._on_remove_requested)

        self.frames.append(frame)
        self.thumbnails.append(thumbnail)
        self.container_layout.addWidget(thumbnail)

        self._update_count()

    def add_frames(self, frames: list):
        """Add multiple frames."""
        for frame in frames:
            self.add_frame(frame)

    def remove_frame(self, index: int):
        """Remove a frame by index."""
        if 0 <= index < len(self.frames):
            self.frames.pop(index)
            thumbnail = self.thumbnails.pop(index)
            self.container_layout.removeWidget(thumbnail)
            thumbnail.deleteLater()

            for i, thumb in enumerate(self.thumbnails):
                thumb.update_index(i)

            self._update_count()
            self.frame_removed.emit(index)

            if len(self.frames) == 0:
                self.empty_label.show()

    def clear_all(self):
        """Remove all frames."""
        while self.frames:
            self.remove_frame(0)

    def get_frames(self) -> list:
        """Get all selected frames."""
        return self.frames.copy()

    def get_frame_count(self) -> int:
        """Get number of selected frames."""
        return len(self.frames)

    def _on_thumbnail_clicked(self, index: int):
        """Handle thumbnail click."""
        if self.selected_index >= 0 and self.selected_index < len(self.thumbnails):
            self.thumbnails[self.selected_index].set_selected(False)

        self.selected_index = index
        if index < len(self.thumbnails):
            self.thumbnails[index].set_selected(True)

        self.frame_selected.emit(index)

    def _on_remove_requested(self, index: int):
        """Handle remove request."""
        self.remove_frame(index)

    def _update_count(self):
        """Update the frame count."""
        count = len(self.frames)
        self.count_badge.setText(str(count))

        if count > 0:
            self.count_badge.setStyleSheet(f"""
                font-size: 11px;
                font-weight: 600;
                color: {COLORS['bg_primary']};
                background-color: {COLORS['accent_blue']};
                padding: 2px 8px;
                border-radius: 10px;
                min-width: 20px;
            """)
        else:
            self.count_badge.setStyleSheet(f"""
                font-size: 11px;
                font-weight: 600;
                color: {COLORS['bg_primary']};
                background-color: {COLORS['text_tertiary']};
                padding: 2px 8px;
                border-radius: 10px;
                min-width: 20px;
            """)

    def is_frame_already_added(self, frame_number: int) -> bool:
        """Check if a frame number is already in the list."""
        for frame in self.frames:
            if frame.frame_number == frame_number:
                return True
        return False
