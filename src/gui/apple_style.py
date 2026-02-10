"""
Apple Style - macOS-inspired stylesheet for the application
Responsive design with proper scaling for different screen sizes
"""

# Apple-inspired color palette
COLORS = {
    # Backgrounds
    'bg_primary': '#FFFFFF',
    'bg_secondary': '#F5F5F7',
    'bg_tertiary': '#E8E8ED',
    'bg_dark': '#1D1D1F',

    # Text
    'text_primary': '#1D1D1F',
    'text_secondary': '#6E6E73',
    'text_tertiary': '#AEAEB2',

    # Accents
    'accent_blue': '#007AFF',
    'accent_blue_hover': '#0056CC',
    'accent_blue_pressed': '#004499',
    'accent_green': '#34C759',
    'accent_red': '#FF3B30',
    'accent_orange': '#FF9500',

    # Borders
    'border_light': '#D2D2D7',
    'border_medium': '#C7C7CC',
}


def get_stylesheet():
    """Return the complete Apple-style stylesheet with responsive sizing."""
    return f'''
    /* ===== GLOBAL ===== */
    QMainWindow {{
        background-color: {COLORS['bg_secondary']};
    }}

    QWidget {{
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
        font-size: 14px;
        color: {COLORS['text_primary']};
    }}

    /* ===== LABELS ===== */
    QLabel {{
        color: {COLORS['text_primary']};
        font-size: 14px;
        padding: 2px;
    }}

    QLabel[class="secondary"] {{
        color: {COLORS['text_secondary']};
        font-size: 13px;
    }}

    QLabel[class="title"] {{
        font-size: 16px;
        font-weight: 600;
        padding: 4px 0;
    }}

    QLabel[class="small"] {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
    }}

    /* ===== BUTTONS ===== */
    QPushButton {{
        background-color: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 500;
        color: {COLORS['text_primary']};
        min-height: 32px;
    }}

    QPushButton:hover {{
        background-color: {COLORS['bg_tertiary']};
        border-color: {COLORS['border_medium']};
    }}

    QPushButton:pressed {{
        background-color: {COLORS['border_light']};
    }}

    QPushButton:disabled {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_tertiary']};
        border-color: {COLORS['bg_tertiary']};
    }}

    /* Primary Button (accent) */
    QPushButton[class="primary"] {{
        background-color: {COLORS['accent_blue']};
        border: none;
        color: white;
        font-weight: 600;
        font-size: 14px;
    }}

    QPushButton[class="primary"]:hover {{
        background-color: {COLORS['accent_blue_hover']};
    }}

    QPushButton[class="primary"]:pressed {{
        background-color: {COLORS['accent_blue_pressed']};
    }}

    QPushButton[class="primary"]:disabled {{
        background-color: {COLORS['border_light']};
        color: {COLORS['text_tertiary']};
    }}

    /* ===== INPUT FIELDS ===== */
    QLineEdit {{
        background-color: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 14px;
        min-height: 20px;
        selection-background-color: {COLORS['accent_blue']};
    }}

    QLineEdit:focus {{
        border-color: {COLORS['accent_blue']};
        border-width: 2px;
        padding: 9px 13px;
    }}

    QLineEdit:disabled {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_tertiary']};
    }}

    QLineEdit[readOnly="true"] {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_secondary']};
    }}

    /* ===== SPINBOX ===== */
    QSpinBox {{
        background-color: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        min-width: 80px;
        min-height: 24px;
    }}

    QSpinBox:focus {{
        border-color: {COLORS['accent_blue']};
        border-width: 2px;
    }}

    QSpinBox::up-button, QSpinBox::down-button {{
        width: 24px;
        border: none;
        background: transparent;
    }}

    QSpinBox::up-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-bottom: 6px solid {COLORS['text_secondary']};
        width: 0;
        height: 0;
    }}

    QSpinBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {COLORS['text_secondary']};
        width: 0;
        height: 0;
    }}

    /* ===== COMBOBOX ===== */
    QComboBox {{
        background-color: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 8px;
        padding: 10px 14px;
        padding-right: 36px;
        font-size: 14px;
        min-width: 120px;
        min-height: 24px;
    }}

    QComboBox:hover {{
        border-color: {COLORS['border_medium']};
    }}

    QComboBox:focus {{
        border-color: {COLORS['accent_blue']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 7px solid {COLORS['text_secondary']};
        width: 0;
        height: 0;
        margin-right: 10px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 10px;
        padding: 6px;
        selection-background-color: {COLORS['accent_blue']};
        selection-color: white;
        outline: none;
    }}

    QComboBox QAbstractItemView::item {{
        padding: 10px 16px;
        border-radius: 6px;
        min-height: 28px;
    }}

    QComboBox QAbstractItemView::item:hover {{
        background-color: {COLORS['bg_tertiary']};
    }}

    /* ===== CHECKBOX ===== */
    QCheckBox {{
        spacing: 10px;
        font-size: 14px;
    }}

    QCheckBox::indicator {{
        width: 22px;
        height: 22px;
        border-radius: 6px;
        border: 2px solid {COLORS['border_medium']};
        background-color: {COLORS['bg_primary']};
    }}

    QCheckBox::indicator:hover {{
        border-color: {COLORS['accent_blue']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent_blue']};
        border-color: {COLORS['accent_blue']};
        image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMiIgaGVpZ2h0PSIxMiIgdmlld0JveD0iMCAwIDEyIDEyIj48cGF0aCBmaWxsPSJ3aGl0ZSIgZD0iTTEwIDNMNC41IDguNSAyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgZmlsbD0ibm9uZSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
    }}

    QCheckBox::indicator:disabled {{
        background-color: {COLORS['bg_tertiary']};
        border-color: {COLORS['border_light']};
    }}

    /* ===== SLIDER ===== */
    QSlider::groove:horizontal {{
        height: 6px;
        background-color: {COLORS['bg_tertiary']};
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        width: 22px;
        height: 22px;
        margin: -8px 0;
        background-color: {COLORS['bg_primary']};
        border: 2px solid {COLORS['border_light']};
        border-radius: 11px;
    }}

    QSlider::handle:horizontal:hover {{
        border-color: {COLORS['accent_blue']};
    }}

    QSlider::sub-page:horizontal {{
        background-color: {COLORS['accent_blue']};
        border-radius: 3px;
    }}

    QSlider:disabled {{
        opacity: 0.5;
    }}

    /* ===== SCROLL AREA ===== */
    QScrollArea {{
        background-color: transparent;
        border: none;
    }}

    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}

    QScrollBar:horizontal {{
        height: 10px;
        background: transparent;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {COLORS['border_medium']};
        border-radius: 5px;
        min-width: 40px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {COLORS['text_tertiary']};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    QScrollBar:vertical {{
        width: 10px;
        background: transparent;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {COLORS['border_medium']};
        border-radius: 5px;
        min-height: 40px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['text_tertiary']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* ===== PROGRESS BAR ===== */
    QProgressBar {{
        background-color: {COLORS['bg_tertiary']};
        border: none;
        border-radius: 5px;
        height: 10px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {COLORS['accent_blue']};
        border-radius: 5px;
    }}

    /* ===== STATUS BAR ===== */
    QStatusBar {{
        background-color: {COLORS['bg_secondary']};
        border-top: 1px solid {COLORS['border_light']};
        padding: 8px 16px;
        font-size: 13px;
        color: {COLORS['text_secondary']};
    }}

    /* ===== FRAME (for cards) ===== */
    QFrame[class="card"] {{
        background-color: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 12px;
    }}

    /* ===== SPLITTER ===== */
    QSplitter::handle {{
        background-color: transparent;
    }}

    QSplitter::handle:horizontal {{
        width: 8px;
    }}

    QSplitter::handle:vertical {{
        height: 8px;
    }}

    /* ===== TOOLTIP ===== */
    QToolTip {{
        background-color: {COLORS['text_primary']};
        color: {COLORS['bg_primary']};
        border: none;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
    }}

    /* ===== DIALOG ===== */
    QDialog {{
        background-color: {COLORS['bg_secondary']};
    }}

    /* ===== MESSAGE BOX ===== */
    QMessageBox {{
        background-color: {COLORS['bg_secondary']};
    }}

    QMessageBox QLabel {{
        font-size: 14px;
        color: {COLORS['text_primary']};
    }}

    /* ===== TAB WIDGET ===== */
    QTabWidget::pane {{
        border: 1px solid {COLORS['border_light']};
        border-radius: 8px;
        background-color: {COLORS['bg_primary']};
        padding: 8px;
    }}

    QTabBar::tab {{
        background-color: {COLORS['bg_tertiary']};
        border: 1px solid {COLORS['border_light']};
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 10px 20px;
        margin-right: 4px;
        font-size: 14px;
    }}

    QTabBar::tab:selected {{
        background-color: {COLORS['bg_primary']};
        border-bottom: 1px solid {COLORS['bg_primary']};
    }}

    QTabBar::tab:hover {{
        background-color: {COLORS['bg_secondary']};
    }}
    '''
